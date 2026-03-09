#!/usr/bin/env python3
"""
run_story.py — AI Scrum Story Runner
=====================================
Simulates the full AI Scrum pipeline for a given User Story ID.

Usage:
    python scripts/run_story.py STORY_ID
    python scripts/run_story.py AUTH-01
    python scripts/run_story.py TASK-04 --dry-run
    python scripts/run_story.py FOYER-01 --step "UX Design"
    python scripts/run_story.py --list

Pipeline steps (defined in ai/workflows/sprint_cycle.md):
    1. Story Analysis
    2. UX Design
    3. Database Design
    4. Backend Implementation
    5. Frontend Implementation
    6. Automated Testing
    7. QA Validation

Step 01 (Story Analysis) is wired to ai/agents/po_agent.py and calls
the Anthropic API. All other steps remain in simulation mode until
their agents are wired via step.agent_fn.
"""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Agent imports
# ---------------------------------------------------------------------------
# po_run is imported with a fallback so the script remains usable
# (--list, --dry-run) even when the anthropic package is not installed.
try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ai.agents.po_agent import run as po_run  # type: ignore
    from ai.agents.ux_agent import run as ux_run  # type: ignore
    from ai.agents.db_agent      import run as db_run       # type: ignore
    from ai.agents.backend_agent import run as backend_run  # type: ignore
except ImportError as _e:  # pragma: no cover
    po_run      = None  # type: ignore
    ux_run      = None  # type: ignore
    db_run      = None  # type: ignore
    backend_run = None  # type: ignore
    import warnings
    warnings.warn(
        f"agents unavailable — Steps 01-04 will run in simulation mode ({_e})",
        stacklevel=1,
    )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BACKLOG_PATH  = PROJECT_ROOT / "docs" / "backlog" / "ai_sprint_backlog.md"
WORKFLOW_PATH = PROJECT_ROOT / "ai" / "workflows" / "sprint_cycle.md"
AGENTS_DIR    = PROJECT_ROOT / "ai" / "agents"

# Root directory for all story execution workspaces.
# Each story run creates a subdirectory: .story_runs/STORY_ID/
# Each pipeline step will later write its artifacts into this workspace
# (analysis.md, ux_design.md, db_schema.sql, backend_code.ts, etc.).
RUN_DIR = Path(".story_runs")


# ---------------------------------------------------------------------------
# Terminal colours
# ---------------------------------------------------------------------------

class C:
    _tty   = sys.stdout.isatty()
    RESET  = "\033[0m"  if _tty else ""
    BOLD   = "\033[1m"  if _tty else ""
    DIM    = "\033[2m"  if _tty else ""
    CYAN   = "\033[96m" if _tty else ""
    GREEN  = "\033[92m" if _tty else ""
    YELLOW = "\033[93m" if _tty else ""
    RED    = "\033[91m" if _tty else ""
    PURPLE = "\033[95m" if _tty else ""

    @classmethod
    def bold(cls, s):   return f"{cls.BOLD}{s}{cls.RESET}"
    @classmethod
    def dim(cls, s):    return f"{cls.DIM}{s}{cls.RESET}"
    @classmethod
    def ok(cls, s):     return f"{cls.GREEN}{s}{cls.RESET}"
    @classmethod
    def warn(cls, s):   return f"{cls.YELLOW}{s}{cls.RESET}"
    @classmethod
    def err(cls, s):    return f"{cls.RED}{s}{cls.RESET}"
    @classmethod
    def info(cls, s):   return f"{cls.CYAN}{s}{cls.RESET}"
    @classmethod
    def step(cls, s):   return f"{cls.PURPLE}{cls.BOLD}{s}{cls.RESET}"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class StepStatus(Enum):
    PENDING = "pending"
    ACTIVE  = "active"
    DONE    = "done"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class AcceptanceCriterion:
    text: str
    checked: bool = False


@dataclass
class UserStory:
    id: str
    title: str
    epic: str
    narrative: str
    acceptance_criteria: list[AcceptanceCriterion] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)

    @property
    def full_title(self) -> str:
        return f"{self.id} — {self.title}"

    @property
    def ac_count(self) -> int:
        return len(self.acceptance_criteria)


@dataclass
class PipelineStep:
    """
    One step in the AI Scrum pipeline.

    To wire a real LLM agent, set:
        step.agent_fn = my_agent_function

    The runner calls:
        result = step.agent_fn(story, previous_results)
    """
    number:          int
    name:            str
    responsible:     list[str]
    inputs:          list[str]
    outputs:         list[str]
    execution_rules: list[str]
    gate:            str
    status:          StepStatus = StepStatus.PENDING
    agent_fn:        Optional[callable] = None   # hook point for real agents
    result:          Optional[dict] = None

    @property
    def label(self) -> str:
        return f"Step {self.number:02d} — {self.name}"

    @property
    def responsible_str(self) -> str:
        return " · ".join(self.responsible)


@dataclass
class PipelineResult:
    story_id:    str
    started_at:  datetime
    finished_at: Optional[datetime] = None
    steps:       list[dict] = field(default_factory=list)
    workspace:   str = ""  # path to .story_runs/STORY_ID/ set by run_pipeline()

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    @property
    def success(self) -> bool:
        done_steps = [s for s in self.steps if s["status"] != StepStatus.SKIPPED.value]
        return bool(done_steps) and all(
            s["status"] == StepStatus.DONE.value for s in done_steps
        )


# ---------------------------------------------------------------------------
# Backlog parser
# ---------------------------------------------------------------------------

class BacklogParser:
    """
    Parses ai_sprint_backlog.md and extracts UserStory objects.

    Supported story header formats (1 to 4 heading levels):
        ## AUTH-01 — Title          standard backlog
        ## AUTH-01 - Title           ASCII dash
        ## AUTH-01: Title            colon separator
        ### AUTH-01 — Title         sub-heading
        #### AUTH-01 — Title        sub-sub-heading
        #### ✅ AUTH-01 — Title     sprint checklist with status emoji
    """

    EPIC_PAT      = re.compile(r"^# (EPIC \d+[^#\n]*)", re.MULTILINE)

    # Single robust pattern covering all supported story header formats.
    # group(1) = story ID (e.g. AUTH-01)
    # group(2) = story title
    STORY_PAT = re.compile(
        r"^#{1,4}"            # 1–4 heading markers
        r"\s*"               # optional leading space
        r"(?:✅\s*)?"    # optional ✅ status emoji (sprint backlogs)
        r"([A-Z]+-\d+)"      # group 1: STORY-ID
        r"\s*[—\-:]\s*" # separator: em-dash, hyphen, or colon
        r"(.+)$",             # group 2: title (rest of line)
        re.MULTILINE,
    )

    NARRATIVE_PAT = re.compile(r"^> (.+)$", re.MULTILINE)
    AC_PAT        = re.compile(r"^- \[([ xX])\] (.+)$", re.MULTILINE)
    OOS_PAT       = re.compile(r"\*\*Out of scope\*\*\s*:\s*(.+)$", re.MULTILINE)

    def __init__(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(
                f"Backlog introuvable : {path}\n"
                f"Verifiez que le fichier existe a l'emplacement attendu."
            )
        self.path = path
        self._raw = path.read_text(encoding="utf-8")
        self._stories: dict[str, UserStory] = {}
        self._parsed = False

    def _parse(self) -> None:
        if self._parsed:
            return

        epics: list[tuple[int, str]] = [
            (m.start(), m.group(1).strip())
            for m in self.EPIC_PAT.finditer(self._raw)
        ]

        story_matches = list(self.STORY_PAT.finditer(self._raw))

        if not story_matches:
            raise ValueError(
                f"Aucune story détectée dans le backlog : {self.path}\n"
                f"Formats supportés :\n"
                f"  ## AUTH-01 — Title\n"
                f"  ## AUTH-01 - Title\n"
                f"  ## AUTH-01: Title\n"
                f"  ### AUTH-01 — Title\n"
                f"  #### AUTH-01 — Title\n"
                f"  #### ✅ AUTH-01 — Title\n"
                f"Vérifiez que les IDs respectent le format PREFIXE-CHIFFRE (ex: AUTH-01)."
            )

        for i, m in enumerate(story_matches):
            story_id    = m.group(1).strip()
            story_title = m.group(2).strip()
            start       = m.start()
            end         = story_matches[i + 1].start() if i + 1 < len(story_matches) else len(self._raw)
            block       = self._raw[start:end]

            # Parent epic
            epic_name = "Unknown"
            for ep_pos, ep_name in reversed(epics):
                if ep_pos < start:
                    epic_name = ep_name
                    break

            # Narrative — first blockquote, strip markdown
            narrative = ""
            narr_matches = self.NARRATIVE_PAT.findall(block)
            if narr_matches:
                raw = narr_matches[0]
                narrative = re.sub(r"\*\*|\*|`", "", raw).strip()

            # Acceptance criteria
            criteria = [
                AcceptanceCriterion(
                    text=ac.group(2).strip(),
                    checked=ac.group(1).lower() == "x",
                )
                for ac in self.AC_PAT.finditer(block)
            ]

            # Out of scope
            oos: list[str] = []
            oos_m = self.OOS_PAT.search(block)
            if oos_m:
                oos = [item.strip() for item in oos_m.group(1).split(",")]

            self._stories[story_id] = UserStory(
                id=story_id,
                title=story_title,
                epic=epic_name,
                narrative=narrative,
                acceptance_criteria=criteria,
                out_of_scope=oos,
            )

        self._parsed = True

    def get_story(self, story_id: str) -> UserStory:
        self._parse()
        sid = story_id.upper().strip()
        if sid not in self._stories:
            available = sorted(self._stories.keys())
            cols = "  ".join(f"{s:<12}" for s in available)
            raise ValueError(
                f"Story '{sid}' introuvable dans le backlog.\n"
                f"Stories disponibles ({len(available)}) :\n  {cols}"
            )
        return self._stories[sid]

    def list_stories(self) -> list[str]:
        self._parse()
        return sorted(self._stories.keys())

    def get_parser(self) -> "BacklogParser":
        """Convenience alias — for explicit access to the parsed backlog."""
        self._parse()
        return self


# ---------------------------------------------------------------------------
# Pipeline definition
# ---------------------------------------------------------------------------

def build_pipeline(story: UserStory) -> list[PipelineStep]:
    """
    Builds the ordered list of PipelineStep objects for the given story.

    Each step declares its Input Gate, Output Gate, responsible agents
    and execution rules — derived from ai/workflows/sprint_cycle.md.

    To add a new step or modify an existing one, edit this function.
    To wire a real LLM agent, set step.agent_fn after calling this function.
    """
    sid = story.id

    return [
        PipelineStep(
            number=1,
            name="Story Analysis",
            responsible=["Orchestrateur", "Product Owner (clarification si besoin)"],
            agent_fn=po_run,  # wired to ai/agents/po_agent.py → .story_runs/STORY_ID/story_analysis.md
            inputs=[
                f"User Story {sid} — texte complet + CA",
                "docs/backlog/ai_sprint_backlog.md",
                "Definition of Done du projet",
                "Matrice des dependances inter-stories",
            ],
            outputs=[
                "Rapport d'analyse structurelle (checklist INVEST — 7 criteres)",
                "Points d'attention par agent (UX, BE, DB, TEST)",
                "Dependances confirmees Done ou signalee(s)",
                "Questions de clarification pour le PO (si applicable)",
                f"Feu vert : '{sid} analysee — prete pour UX + DB'",
            ],
            execution_rules=[
                "Verifier les 7 criteres INVEST avant toute chose",
                "Stories FOYER/TASK/SHOP : CA d'isolation multi-tenant obligatoire",
                "Stories avec mutation : CA d'erreur reseau obligatoire",
                "Story > 8 points → decomposition requise avant de continuer",
                "CA ambigu → 1 question precise au PO (jamais d'interpretation)",
            ],
            gate=(
                "Tous les criteres INVEST satisfaits · "
                "CA testables · dependances resolues"
            ),
        ),

        PipelineStep(
            number=2,
            name="UX Design",  # parallel slot A — runs with DB Design
            responsible=["UX Designer"],
            agent_fn=ux_run,  # wired to ai/agents/ux_agent.py → .story_runs/STORY_ID/ux_design.md
            inputs=[
                f"Story {sid} clarifiee + CA (Etape 1)",
                "Points d'attention UX du Rapport d'Analyse",
                "ux_design.md — inventaire des composants §3.5",
                "ux_design.md — systeme de design §3.2–§3.4",
                "ux_design.md — structure de navigation §4.1",
            ],
            outputs=[
                "Fiche(s) ecran au format standard (ux_design.md §3.1)",
                "5 etats par ecran : loading · vide · nominal · erreur · succes",
                "Zones de tap >= 44x44px sur tous les elements interactifs",
                "aria-labels definis sur les elements non-natifs",
                "Adaptation desktop >= 768px specifiee",
                "Nouveaux composants documentes dans l'inventaire",
            ],
            execution_rules=[
                "Mobile-first absolu — layout 375px toujours concu en premier",
                "Desktop est un delta vs mobile — jamais une refonte",
                "Les 5 etats sont obligatoires — pas d'ecran blanc, pas de liste vide sans contexte",
                "Nouveaux composants documentes dans l'inventaire avant de continuer",
                "Si comportement non couvert → 1 question PO avant de produire la spec",
            ],
            gate=(
                "Fiche(s) ecran completes · 5 etats · "
                "checklist Annexe A passante"
            ),
        ),

        PipelineStep(
            number=3,
            name="Database Design",  # parallel slot B — runs with UX Design
            responsible=["Database Developer"],
            agent_fn=db_run,  # wired to ai/agents/db_agent.py → db_schema.sql, rls_policies.sql, database_types.ts
            inputs=[
                f"Story {sid} + CA (Etape 1)",
                "Points d'attention DB du Rapport d'Analyse",
                "supabase_database.md — schema actuel §2",
                "supabase_database.md — patterns RLS §4",
                "src/types/database.ts actuel",
            ],
            outputs=[
                "supabase/migrations/[timestamp]_[nom].sql — migration idempotente",
                "RLS active + 4 policies (SELECT / INSERT WITH CHECK / UPDATE / DELETE)",
                "Indexes de performance crees pour les patterns de requetes connus",
                "Tests RLS passants — isolation cross-foyer verifiee",
                "src/types/database.ts regenere et commite",
                "Signal SYNC A emis vers BE et FE",
            ],
            execution_rules=[
                "household_id NOT NULL sur toute nouvelle table de donnees metier — sans exception",
                "Ordre : CREATE TABLE → ENABLE RLS → Policies → Indexes → Triggers",
                "Migration idempotente : IF NOT EXISTS · DROP POLICY IF EXISTS · OR REPLACE",
                "SYNC A interdit avant que la migration ET les tests RLS passent localement",
                "Breaking change → preavid 1 cycle + migration backward-compatible",
            ],
            gate=(
                "Migration locale passante · RLS + 4 policies · "
                "tests isolation OK · SYNC A emis"
            ),
        ),

        PipelineStep(
            number=4,
            name="Backend Implementation",
            responsible=["Backend Developer"],
            agent_fn=backend_run,  # wired to ai/agents/backend_agent.py → backend_routes.ts, backend_service.ts, validation_schemas.ts
            inputs=[
                "SYNC A recu — types TypeScript disponibles (Etape 3)",
                f"Story {sid} + CA (Etape 1)",
                "nextjs_development.md — patterns API Routes §5",
                "supabase_database.md — pattern membership §3.2",
            ],
            outputs=[
                "src/lib/validations/[domaine].ts — schemas Zod",
                "src/app/api/v1/[ressource]/route.ts — GET, POST",
                "src/app/api/v1/[ressource]/[id]/route.ts — PATCH, DELETE",
                "Chaine de securite : validation → auth → membership → DB → reponse",
                "next build passant · TypeScript strict · ESLint clean",
                "SERVICE_ROLE_KEY absente du bundle client",
                "Signal SYNC B emis vers FE (contrat API)",
            ],
            execution_rules=[
                "Chaine de securite non negociable : validation → auth → membership → DB → reponse",
                "z.string().uuid() sur tous les IDs · .min(1).max(N).trim() sur les chaines",
                "POST → 201 | DELETE → 204 | Zod failure → 422 | Non-membre → 403",
                "household_id lu depuis la DB pour PATCH/DELETE — jamais depuis le body",
                "Verification : grep -r SUPABASE_SERVICE_ROLE .next/static/ → 0 resultat",
            ],
            gate=(
                "next build propre · chaine securite complete · SYNC B emis"
            ),
        ),

        PipelineStep(
            number=5,
            name="Frontend Implementation",
            responsible=["Frontend Developer"],
            inputs=[
                "Fiche(s) ecran UX (Etape 2)",
                "SYNC A — types TypeScript (Etape 3)",
                "SYNC B — contrat API Backend (Etape 4)",
                "nextjs_development.md — composants §3 + hooks §4",
                "ux_design.md — inventaire composants §3.5",
            ],
            outputs=[
                "src/components/[domaine]/[Composant].tsx — 5 etats implementes",
                "src/hooks/use[Domaine].ts — optimistic update + rollback",
                "src/app/(app)/[route]/page.tsx — page assemblee",
                "next build passant · TypeScript strict (pas de any)",
                "Verifie sur 375px · pb-safe · tap zones >= 44x44px · aria-labels",
            ],
            execution_rules=[
                "La fiche ecran UX est la source de verite — deviations → relance Etape 2",
                "Les 5 etats sont obligatoires pour chaque composant de la spec",
                "Optimistic update : local state → API call → rollback exact si erreur",
                "focus-visible:ring-2 sur tous les elements focusables",
                "Composants peuvent demarrer apres Etape 2 · Hooks attendent SYNC B",
            ],
            gate=(
                "next build propre · 5 etats · optimistic update · 375px verifie"
            ),
        ),

        PipelineStep(
            number=6,
            name="Automated Testing",
            responsible=[
                "Testing Developer",
                "Infrastructure Developer (parallele)",
            ],
            inputs=[
                "Composants et hooks FE complets (Etape 5)",
                "API Routes BE completes (Etape 4)",
                "Migration DB + policies RLS (Etape 3)",
                f"Story {sid} + CA (Etape 1) — pour fixtures de test",
                "testing_quality.md — patterns de tests §3–§4",
            ],
            outputs=[
                "src/__tests__/components/*.test.tsx — tests unitaires verts",
                "src/__tests__/hooks/use*.test.ts — tests hooks verts",
                "src/__tests__/api/*/route.test.ts — tests integration verts",
                "supabase/tests/rls/*_isolation.sql — tests RLS verts",
                "Couverture >= 70% — rapport npm run test:coverage",
                "CI pipeline vert (type-check + lint + tests + build)",
                "Preview URL accessible · /api/health → 200",
                "Signal SYNC C emis vers QA",
            ],
            execution_rules=[
                "Chaque CA couvert par au moins 1 test automatise",
                "Tests integration : 4 niveaux — validation (422) · auth (401) · isolation (403) · nominal",
                "Tests RLS obligatoires pour toute story FOYER / TASK / SHOP",
                "Echec RLS = bug P1 → signal SM immediat · pipeline suspendu",
                "SYNC C interdit tant que tests ET preview ne sont pas OK tous les deux",
                "INFRA applique les migrations preview AVANT de notifier QA",
            ],
            gate=(
                "Suite verte · couverture >= 70% · CI verte · "
                "preview accessible · SYNC C emis"
            ),
        ),

        PipelineStep(
            number=7,
            name="QA Validation",
            responsible=["QA Engineer"],
            inputs=[
                "SYNC C — URL preview + resultats tests (Etape 6)",
                f"Story {sid} + CA exacts (Etape 1)",
                "Fiche(s) ecran UX (Etape 2)",
                "testing_quality.md — checklists de validation §5.3",
            ],
            outputs=[
                "Rapport de validation au format standard (QA.md §4.1)",
                "Tableau CA : Pass ou Fail pour chaque critere (texte exact)",
                "Verifications manuelles : 375px · offline · clavier · aria-live",
                "Isolation multi-tenant verifiee (si story household)",
                "Verification de regression — suite complete executee",
                "Fiches de bug avec etapes de reproduction (si applicable)",
                "Verdict formel : 'Pret pour Sprint Review' ou 'Rejete — [raison]'",
            ],
            execution_rules=[
                "'Pret pour Sprint Review' uniquement si TOUS les CA passent + 0 bug P1/P2",
                "Texte exact du CA dans le rapport — jamais paraphrase",
                "QA ne corrige pas le code — QA documente et signale l'agent responsable",
                "Bug P1 → signal SM immediat — ne pas attendre la fin du rapport",
                "Sur 'Rejete' → Orchestrateur route le bug et relance l'etape concernee",
            ],
            gate=(
                "Rapport complet · tous CA documentes · "
                "verdict formel prononce"
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Renderer — all display logic in one place
# ---------------------------------------------------------------------------

class Renderer:
    """All terminal output lives here — StoryRunner stays clean."""

    WIDTH = 70

    @staticmethod
    def banner() -> None:
        w = Renderer.WIDTH
        print()
        print(C.info("=" * w))
        print(C.bold(C.info("  AI Scrum Story Runner — pipeline simulateur")))
        print(C.info("=" * w))

    @staticmethod
    def story_card(story: UserStory) -> None:
        print()
        print(C.bold("  STORY"))
        print(C.dim("  " + "-" * 40))
        print(f"  {C.bold(story.full_title)}")
        print(C.dim(f"  Epic : {story.epic}"))
        if story.narrative:
            wrapped = textwrap.fill(
                story.narrative,
                width=Renderer.WIDTH - 4,
                initial_indent="  ",
                subsequent_indent="  ",
            )
            print(wrapped)
        ac_label = str(story.ac_count) + " critere(s) d'acceptation"
        print(f"  {C.dim(ac_label)}")
        if story.acceptance_criteria:
            print()
            print(C.bold("  Criteres d'acceptation :"))
            for ac in story.acceptance_criteria:
                mark = C.ok("v") if ac.checked else C.dim("o")
                text = textwrap.fill(
                    ac.text,
                    width=Renderer.WIDTH - 8,
                    initial_indent=f"    {mark} ",
                    subsequent_indent="      ",
                )
                print(text)
        if story.out_of_scope:
            oos = ", ".join(story.out_of_scope[:3])
            if len(story.out_of_scope) > 3:
                oos += "..."
            print(C.dim(f"\n  Hors perimetre : {oos}"))
        print()

    @staticmethod
    def pipeline_overview(steps: list[PipelineStep]) -> None:
        print(C.bold("  PIPELINE"))
        print(C.dim("  " + "-" * 40))
        for step in steps:
            connector = "L" if step.number == len(steps) else "+"
            print(f"  {C.dim(connector + '--')} {C.info(step.label)}")
            agents = " + ".join(step.responsible)
            indent = "     " if step.number == len(steps) else "  |  "
            print(C.dim(f"  {indent} {agents}"))
        print()

    @staticmethod
    def step_header(step: PipelineStep, total: int) -> None:
        print()
        print(C.dim("-" * Renderer.WIDTH))
        progress = f"[{step.number}/{total}]"
        print(C.step(f"  {step.label}") + C.dim(f"  {progress}"))
        print(C.dim("-" * Renderer.WIDTH))

    @staticmethod
    def section(title: str, items: list[str], bullet: str = "->", color_fn=None) -> None:
        print()
        print(C.bold(f"  {title}"))
        for item in items:
            col = color_fn(bullet) if color_fn else C.dim(bullet)
            wrapped = textwrap.fill(
                item,
                width=Renderer.WIDTH - 8,
                initial_indent=f"    {col} ",
                subsequent_indent="       ",
            )
            print(wrapped)

    @staticmethod
    def gate(text: str) -> None:
        print()
        print(C.bold("  Gate de sortie"))
        print(f"    {C.ok(text)}")

    @staticmethod
    def step_done(simulated: bool = True) -> None:
        print()
        if simulated:
            print(C.ok("  [OK] Simulation reussie") + C.dim("  — aucun agent LLM appele"))
        else:
            print(C.ok("  [DONE]"))

    @staticmethod
    def step_blocked(reason: str) -> None:
        print()
        print(C.err(f"  [BLOQUE] {reason}"))

    @staticmethod
    def summary(result: PipelineResult) -> None:
        print()
        print(C.info("=" * Renderer.WIDTH))
        print(C.bold("  RESUME DU PIPELINE"))
        print(C.info("=" * Renderer.WIDTH))
        print()
        print(f"  Story   : {C.bold(result.story_id)}")
        print(f"  Demarre : {result.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if result.finished_at:
            print(f"  Termine : {result.finished_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if result.duration_seconds is not None:
                print(f"  Duree   : {result.duration_seconds:.2f}s")
        print()
        for s in result.steps:
            status = s["status"]
            icons = {
                StepStatus.DONE.value:    C.ok("[OK]    "),
                StepStatus.SKIPPED.value: C.warn("[SKIP]  "),
                StepStatus.BLOCKED.value: C.err("[BLOQUE]"),
                StepStatus.PENDING.value: C.dim("[WAIT]  "),
            }
            icon = icons.get(status, C.dim("[?]     "))
            print(f"  {icon} {s['name']}")
        print()
        if result.success:
            print(C.ok(C.bold("  Pipeline termine — pret pour Sprint Review")))
        else:
            print(C.warn(C.bold("  Pipeline partiel — verifier les etapes bloquees")))
        print()

    @staticmethod
    def parallel_header(steps: list) -> None:
        """Announce a parallel execution window."""
        print()
        print(C.dim("-" * Renderer.WIDTH))
        names = "  //  ".join(C.step(s.label) for s in steps)
        print(f"  {names}")
        print(C.dim("  (parallel execution)"))
        print(C.dim("-" * Renderer.WIDTH))

    @staticmethod
    def parallel_done(results: list[dict], elapsed: float) -> None:
        """Summary line after a parallel window completes."""
        statuses = "  |  ".join(
            C.ok(f"[OK] {r['name']}") if r["status"] == StepStatus.DONE.value
            else C.err(f"[BLOQUE] {r['name']}")
            for r in results
        )
        print()
        print(f"  {statuses}")
        print(C.dim(f"  Fenetre parallele terminee en {elapsed:.2f}s"))

    @staticmethod
    def error(msg: str) -> None:
        print()
        print(C.err(f"  Erreur : {msg}"))
        print()

    @staticmethod
    def info_msg(msg: str) -> None:
        print(C.dim(f"  > {msg}"))


# ---------------------------------------------------------------------------
# Story Runner
# ---------------------------------------------------------------------------

class StoryRunner:
    """
    Orchestrates the AI Scrum pipeline for a single User Story.

    Designed to be extended:
      - Override run_step() to add real agent calls
      - Set step.agent_fn on individual steps to wire LLM agents
      - Subclass and override run_pipeline() for custom gate logic

    The class follows the interface defined in scrum_orchestrator.md:
      - Input Gate checked before each step (currently: verify inputs listed)
      - Output Gate checked after each step (currently: step marked Done)
      - Blocked step halts the pipeline at that point
    """

    def __init__(
        self,
        story_id:    str,
        dry_run:     bool = False,
        target_step: Optional[str] = None,
        verbose:     bool = False,
    ) -> None:
        self.story_id    = story_id.upper().strip()
        self.dry_run     = dry_run
        self.target_step = target_step
        self.verbose     = verbose

        self._story:    Optional[UserStory] = None
        self._pipeline: list[PipelineStep]  = []
        self._result:   Optional[PipelineResult] = None

    # -- Public interface -----------------------------------------------------

    def run(self) -> PipelineResult:
        """Entry point — load story, build pipeline, execute all steps."""
        Renderer.banner()

        self._story    = self.load_story()
        self._pipeline = self.load_pipeline()

        Renderer.story_card(self._story)
        Renderer.pipeline_overview(self._pipeline)

        if self.dry_run:
            print(C.warn("  Mode dry-run — aucune etape executee.\n"))
            return PipelineResult(story_id=self.story_id, started_at=datetime.now())

        self._result = PipelineResult(
            story_id=self.story_id,
            started_at=datetime.now(),
        )

        steps_to_run = self._resolve_target_steps()
        self.run_pipeline(steps_to_run)

        self._result.finished_at = datetime.now()
        Renderer.summary(self._result)
        return self._result

    # -- Loaders --------------------------------------------------------------

    def load_backlog(self) -> BacklogParser:
        """Load and return the backlog parser."""
        parser = BacklogParser(BACKLOG_PATH)
        if self.verbose:
            Renderer.info_msg(f"Backlog charge : {BACKLOG_PATH}")
        return parser

    def load_story(self) -> UserStory:
        """Load and return the UserStory for self.story_id."""
        parser = self.load_backlog()
        story  = parser.get_story(self.story_id)
        if self.verbose:
            Renderer.info_msg(f"Story trouvee : {story.full_title}")
        return story

    def load_pipeline(self) -> list[PipelineStep]:
        """
        Build and return the ordered pipeline for the current story.

        Extension point: override this method to load step definitions
        dynamically from ai/workflows/sprint_cycle.md or a database.
        """
        if self._story is None:
            raise RuntimeError("load_story() must be called before load_pipeline()")
        steps = build_pipeline(self._story)
        if self.verbose:
            Renderer.info_msg(f"Pipeline charge : {len(steps)} etapes")
        return steps

    # -- Step execution -------------------------------------------------------

    def run_step(
        self,
        step:             PipelineStep,
        previous_results: list[dict],
    ) -> dict:
        """
        Execute a single pipeline step.

        Simulation mode (agent_fn is None):
            Display the step card, mark Done, return a success result.

        Real agent mode (agent_fn is set):
            Display the step card, call agent_fn(story, previous_results),
            store the output in step.result, mark Done or Blocked.

        Extension point: override this method to add retries, logging,
        structured output validation, or timeout handling.
        """
        total = len(self._pipeline)

        Renderer.step_header(step, total)
        Renderer.section("Responsable(s)", step.responsible, ">>", lambda x: C.info(x))
        Renderer.section("Inputs requis (Input Gate)", step.inputs, "->", lambda x: C.warn(x))
        Renderer.section("Outputs attendus (Output Gate)", step.outputs, "<-", lambda x: C.ok(x))

        if self.verbose:
            Renderer.section("Regles d'execution", step.execution_rules, " *", lambda x: C.dim(x))

        Renderer.gate(step.gate)

        result: dict = {"name": step.name, "status": StepStatus.DONE.value}

        if step.agent_fn is not None:
            # Real agent call — structured for future use
            try:
                agent_output   = step.agent_fn(self._story, previous_results)
                step.result    = agent_output
                step.status    = StepStatus.DONE
                result["output"] = agent_output
            except Exception as exc:
                step.status      = StepStatus.BLOCKED
                result["status"] = StepStatus.BLOCKED.value
                result["error"]  = str(exc)
                Renderer.step_blocked(str(exc))
                return result
        else:
            step.status = StepStatus.DONE

        Renderer.step_done(simulated=(step.agent_fn is None))
        return result

    def run_pipeline(self, steps: list[PipelineStep]) -> None:
        """
        Run the pipeline with a parallel execution window for UX + DB Design.

        Execution order:
            Step 01 — Story Analysis       (sequential)
            Step 02A — UX Design  \
                                    (parallel — ThreadPoolExecutor max_workers=2)
            Step 02B — Database Design /
            Step 03+ — Backend, Frontend, Testing, QA  (sequential)

        Execution Rule 3 (scrum_orchestrator.md §5):
            A blocked step halts the pipeline immediately.
            In the parallel window, a block in either branch halts both.
        """
        import time

        # Create the story workspace directory.
        # Each pipeline step will later write its artifacts into this workspace
        # (analysis.md, ux_design.md, db_schema.sql, backend_code.ts, etc.).
        story_dir = RUN_DIR / self.story_id
        story_dir.mkdir(parents=True, exist_ok=True)
        if self.verbose:
            Renderer.info_msg(f"Workspace cree : {story_dir}")
        if self._result is not None:
            self._result.workspace = str(story_dir)

        previous_results: list[dict] = []

        # ── Identify the parallel window: steps with number 2 and 3
        #    (UX Design and Database Design). Everything else is sequential.
        # ── Index by step.number for robust identification.
        parallel_numbers = {2, 3}   # UX Design=2, Database Design=3
        parallel_steps   = [s for s in steps if s.number in parallel_numbers]
        sequential_steps = [s for s in steps if s.number not in parallel_numbers]

        def _record(result: dict, step: PipelineStep) -> None:
            """Append result to previous_results and PipelineResult.steps."""
            previous_results.append(result)
            if self._result is not None:
                self._result.steps.append(result)

        def _halt_remaining(blocked_name: str) -> None:
            """Mark all still-PENDING steps as waiting and log the suspension."""
            Renderer.info_msg(
                f"Pipeline suspendu a \'{blocked_name}\' — "
                "resoudre le blocage avant de continuer."
            )
            for s in self._pipeline:
                if s.status == StepStatus.PENDING:
                    if self._result:
                        self._result.steps.append({
                            "name":   s.name,
                            "status": StepStatus.PENDING.value,
                        })

        # ── Phase 1: sequential steps before the parallel window (Step 01) ──
        for step in sequential_steps:
            if step.number >= min(parallel_numbers):
                break   # reached steps that come after the parallel window
            if self.verbose:
                Renderer.info_msg(f"Input Gate verifie pour : {step.name}")
            result = self.run_step(step, previous_results)
            _record(result, step)
            if result["status"] == StepStatus.BLOCKED.value:
                _halt_remaining(step.name)
                return

        # ── Phase 2: parallel window — UX Design // Database Design ─────────
        if parallel_steps:
            Renderer.parallel_header(parallel_steps)
            if self.verbose:
                for ps in parallel_steps:
                    Renderer.info_msg(f"Input Gate verifie pour : {ps.name} (parallele)")

            # Snapshot of previous_results before the window — both threads
            # receive the same read-only view (list copy) so there is no race.
            snapshot = list(previous_results)
            parallel_results: dict[int, dict] = {}
            t0 = time.monotonic()

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = {
                    executor.submit(self.run_step, ps, snapshot): ps
                    for ps in parallel_steps
                }
                for future in as_completed(futures):
                    ps     = futures[future]
                    try:
                        res = future.result()
                    except Exception as exc:
                        # Unexpected exception from the thread — treat as BLOCKED
                        res = {
                            "name":   ps.name,
                            "status": StepStatus.BLOCKED.value,
                            "error":  str(exc),
                        }
                        ps.status = StepStatus.BLOCKED
                        Renderer.step_blocked(str(exc))
                    parallel_results[ps.number] = res

            elapsed = time.monotonic() - t0

            # Collect results in canonical order (UX first, then DB)
            ordered = [parallel_results[ps.number] for ps in parallel_steps]
            Renderer.parallel_done(ordered, elapsed)

            # Register results and check for blocks
            for res in ordered:
                _record(res, next(s for s in parallel_steps if s.name == res["name"]))
                if res["status"] == StepStatus.BLOCKED.value:
                    _halt_remaining(res["name"])
                    return

        # ── Phase 3: sequential steps after the parallel window (Step 03+) ──
        for step in sequential_steps:
            if step.number < min(parallel_numbers):
                continue   # already executed in Phase 1
            if self.verbose:
                Renderer.info_msg(f"Input Gate verifie pour : {step.name}")
            result = self.run_step(step, previous_results)
            _record(result, step)
            if result["status"] == StepStatus.BLOCKED.value:
                _halt_remaining(step.name)
                return

    # -- Helpers --------------------------------------------------------------

    def _resolve_target_steps(self) -> list[PipelineStep]:
        """Return only the targeted step(s), marking others as SKIPPED."""
        if self.target_step is None:
            return self._pipeline

        target  = self.target_step.lower().strip()
        matched = [s for s in self._pipeline if target in s.name.lower()]

        if not matched:
            names = [s.name for s in self._pipeline]
            raise ValueError(
                f"Etape '{self.target_step}' introuvable.\n"
                f"Etapes disponibles : {', '.join(names)}"
            )

        for step in self._pipeline:
            if step not in matched:
                step.status = StepStatus.SKIPPED
                if self._result:
                    self._result.steps.append({
                        "name":   step.name,
                        "status": StepStatus.SKIPPED.value,
                    })

        return matched


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_story",
        description="AI Scrum Story Runner — simule le pipeline de developpement.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Exemples :
              python scripts/run_story.py AUTH-01
              python scripts/run_story.py TASK-04 --verbose
              python scripts/run_story.py FOYER-01 --step "UX Design"
              python scripts/run_story.py SHOP-02 --dry-run
              python scripts/run_story.py --list
        """),
    )
    parser.add_argument(
        "story_id",
        nargs="?",
        help="ID de la User Story a executer (ex: AUTH-01, TASK-04)",
    )
    parser.add_argument(
        "--step",
        metavar="NOM",
        help="Executer une seule etape (ex: 'UX Design', 'Backend Implementation')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher la story et le pipeline sans executer les etapes",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lister toutes les stories disponibles dans le backlog",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Afficher les regles d'execution et les messages de diagnostic",
    )
    return parser


def cmd_list() -> None:
    """List all available stories grouped by epic prefix."""
    parser = BacklogParser(BACKLOG_PATH)
    stories = parser.list_stories()
    print()
    print(C.bold(f"  Backlog — {len(stories)} stories disponibles"))
    print(C.dim("  " + "-" * 40))

    current_prefix = None
    for sid in stories:
        prefix = sid.split("-")[0]
        if prefix != current_prefix:
            print(f"\n  {C.bold(C.info(prefix))}")
            current_prefix = prefix
        story = parser.get_story(sid)
        ac_n  = f"{story.ac_count} CA"
        print(f"    {C.info(sid):<16}  {story.title:<40}  {C.dim(ac_n)}")
    print()


def main() -> None:
    arg_parser = build_arg_parser()
    args       = arg_parser.parse_args()

    # Verify required files
    missing = [
        str(p) for p in (BACKLOG_PATH, WORKFLOW_PATH) if not p.exists()
    ]
    if missing:
        print(C.err("\n  Fichiers requis introuvables :"))
        for f in missing:
            print(C.err(f"    {f}"))
        print(C.dim(
            "\n  Structure attendue depuis la racine du projet :\n"
            "    docs/backlog/ai_sprint_backlog.md\n"
            "    ai/workflows/sprint_cycle.md\n"
        ))
        sys.exit(1)

    if args.list:
        cmd_list()
        return

    if not args.story_id:
        arg_parser.print_help()
        print()
        sys.exit(0)

    try:
        runner = StoryRunner(
            story_id    = args.story_id,
            dry_run     = args.dry_run,
            target_step = args.step,
            verbose     = args.verbose,
        )
        result = runner.run()
        sys.exit(0 if result.success else 1)

    except FileNotFoundError as exc:
        Renderer.error(str(exc))
        sys.exit(2)

    except ValueError as exc:
        Renderer.error(str(exc))
        sys.exit(2)

    except KeyboardInterrupt:
        print(C.warn("\n\n  Interrompu par l'utilisateur.\n"))
        sys.exit(130)


if __name__ == "__main__":
    main()
