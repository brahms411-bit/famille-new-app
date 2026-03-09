"""
backend_agent.py — Backend Developer Agent
============================================
Implements the Backend Implementation step (Step 04) of the AI Scrum pipeline.

Responsibilities:
    1. Load the prompt template from ai/prompts/backend_design.md
    2. Read prior step outputs from the story workspace:
         story_analysis.md  (Step 01 — PO Agent)
         ux_design.md       (Step 02 — UX Agent)
         db_schema.sql      (Step 03 — DB Agent)
         database_types.ts  (Step 03 — DB Agent)
    3. Resolve all {{placeholders}} with story data + workspace files
    4. Call the Anthropic API (claude-sonnet-4-20250514)
    5. Parse the LLM response into 3 TypeScript files
    6. Write to the story workspace:
         .story_runs/STORY_ID/backend_routes.ts
         .story_runs/STORY_ID/backend_service.ts
         .story_runs/STORY_ID/validation_schemas.ts
    7. Return a structured dict for the pipeline result

Integration with run_story.py:
    from ai.agents.backend_agent import run as backend_run
    pipeline[3].agent_fn = backend_run   # Step 04 — Backend Implementation

Signature expected by StoryRunner.run_step():
    agent_fn(story: UserStory, previous_results: list[dict]) -> dict

Standalone usage:
    python ai/agents/backend_agent.py AUTH-01
    python ai/agents/backend_agent.py AUTH-01 --dry-run
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.run_story import UserStory

# Ensure PROJECT_ROOT is importable when running the agent as a standalone script
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai.agents.context import (  # type: ignore
    load_context,
    read_artefact,
    save_contract,
    build_context_instruction,
    extract_summary,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPT_PATH  = PROJECT_ROOT / "ai" / "prompts" / "backend_design.md"
RUN_DIR      = PROJECT_ROOT / ".story_runs"

# Output file names written to .story_runs/STORY_ID/
OUTPUT_ROUTES     = "backend_routes.ts"
OUTPUT_SERVICE    = "backend_service.ts"
OUTPUT_VALIDATION = "validation_schemas.ts"

# ---------------------------------------------------------------------------
# Workspace readers
# ---------------------------------------------------------------------------

def _read_workspace_file(story_id: str, filename: str, step_label: str) -> str:
    """
    Read a file from the story workspace.

    Returns the file content, or a descriptive placeholder if missing
    (e.g. when running Step 04 in isolation or dry-run).
    """
    path = RUN_DIR / story_id / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return (
        f"_{filename} non disponible — "
        f"exécuter {step_label} avant Step 04._"
    )


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _load_template() -> str:
    """Load the raw prompt template from ai/prompts/backend_design.md."""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Prompt template introuvable : {PROMPT_PATH}\n"
            f"Assurez-vous que le fichier ai/prompts/backend_design.md existe."
        )
    return PROMPT_PATH.read_text(encoding="utf-8")


def _format_criteria(story: "UserStory") -> str:
    """Render acceptance criteria as a numbered Markdown list."""
    if not story.acceptance_criteria:
        return "_Aucun critère d'acceptation défini._"
    lines = []
    for i, ac in enumerate(story.acceptance_criteria, 1):
        status = "[x]" if ac.checked else "[ ]"
        lines.append(f"{i}. {status} {ac.text}")
    return "\n".join(lines)


def _format_out_of_scope(story: "UserStory") -> str:
    """Render out-of-scope items as a Markdown list."""
    if not story.out_of_scope:
        return "_Non spécifié._"
    return "\n".join(f"- {item}" for item in story.out_of_scope)


def build_prompt(story: "UserStory") -> str:
    """
    Resolve all {{placeholders}} in the template with story data.

    Placeholders supported:
        {{story_id}}           → story.id
        {{story_title}}        → story.title
        {{story_epic}}         → story.epic
        {{story_narrative}}    → story.narrative
        {{acceptance_criteria}} → formatted CA list
        {{out_of_scope}}       → formatted OOS list
        {{story_analysis}}     → story_analysis.md  (Step 01)
        {{ux_design}}          → ux_design.md        (Step 02)
        {{db_schema}}          → db_schema.sql        (Step 03)
        {{database_types}}     → database_types.ts    (Step 03)
    """
    template = _load_template()

    replacements = {
        "{{story_id}}":             story.id,
        "{{story_title}}":          story.title,
        "{{story_epic}}":           story.epic,
        "{{story_narrative}}":      story.narrative or "_Non spécifiée._",
        "{{acceptance_criteria}}":  _format_criteria(story),
        "{{out_of_scope}}":         _format_out_of_scope(story),
        # Steps 01-02 context via context.md (dense summary, not full files)
        "{{story_analysis}}":       load_context(story.id) or _read_workspace_file(
                                        story.id, "story_analysis.md",
                                        "Step 01 (Story Analysis)"
                                    ),
        "{{ux_design}}":            "",  # covered by context.md above
        # DB artefacts are injected directly — they are technical contracts
        # that cannot be summarised without loss (table names, column types).
        # read_artefact() truncates at 4 000 chars to stay bounded.
        "{{db_schema}}":            read_artefact(
                                        story.id, "db_schema.sql",
                                        "Step 03 (Database Design)"
                                    ),
        "{{database_types}}":       read_artefact(
                                        story.id, "database_types.ts",
                                        "Step 03 (Database Design)"
                                    ),
    }

    prompt = template
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    # Sanity check — no unreplaced placeholders.
    # Ignore HTML comment lines which may contain {{ }} examples.
    def _is_comment(line: str) -> bool:
        s = line.strip()
        return s.startswith(">") or s.startswith("<!--") or s.startswith("-->")

    prompt_no_comments = "\n".join(
        line for line in prompt.splitlines()
        if not _is_comment(line)
    )
    remaining = re.findall(r"\{\{[^}]+\}\}", prompt_no_comments)
    if remaining:
        raise ValueError(
            f"Placeholders non résolus dans le template : {remaining}\n"
            f"Ajoutez-les dans build_prompt() ou corrigez le template."
        )

    # Extract the body of the ## Prompt section (everything after the heading).
    prompt_match = re.search(
        r"^## Prompt\s*\n(.+)",
        prompt,
        re.MULTILINE | re.DOTALL,
    )
    if prompt_match:
        return prompt_match.group(1).strip() + build_context_instruction()

    # Fallback: strip metadata block and return the rest.
    extracted = re.sub(r"(?s)^.*?## Prompt\s*\n", "", prompt).strip()
    return extracted + build_context_instruction()


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def _call_anthropic(prompt: str) -> str:
    """
    Call the Anthropic API and return the raw text response.

    Uses the anthropic Python SDK if available, falls back to raw HTTP.
    The API key is read from the ANTHROPIC_API_KEY environment variable.
    """
    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8096,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    except ImportError:
        import os
        import urllib.request

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY non défini.\n"
                "Exportez la variable : export ANTHROPIC_API_KEY=sk-ant-..."
            )

        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 8096,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]


# ---------------------------------------------------------------------------
# Response parser — splits one LLM response into 3 TypeScript files
# ---------------------------------------------------------------------------

def _parse_response(raw: str) -> dict[str, str]:
    """
    Parse the LLM response into three separate file contents.

    Expected format (set by backend_design.md prompt):

        <!-- SECTION: backend_routes.ts -->
        ```typescript
        ...
        ```

        <!-- SECTION: backend_service.ts -->
        ```typescript
        ...
        ```

        <!-- SECTION: validation_schemas.ts -->
        ```typescript
        ...
        ```

    Strategies (in order):
        1. Structured <!-- SECTION: filename --> markers   (preferred)
        2. Heuristic: 3 consecutive ```typescript blocks   (fallback)
        3. Full raw response written to all 3 files        (last resort)
    """
    sections: dict[str, str] = {}

    # Strategy 1 — section markers
    section_pattern = re.compile(
        r"<!--\s*SECTION:\s*(\S+)\s*-->\s*```(?:typescript|ts)\n(.*?)```",
        re.DOTALL,
    )
    for match in section_pattern.finditer(raw):
        filename = match.group(1).strip()
        content  = match.group(2).strip()
        sections[filename] = content

    if len(sections) >= 3:
        return sections

    # Strategy 2 — heuristic: 3 typescript blocks in declaration order
    ts_blocks = re.findall(r"```(?:typescript|ts)\n(.*?)```", raw, re.DOTALL)
    targets = [OUTPUT_ROUTES, OUTPUT_SERVICE, OUTPUT_VALIDATION]
    for filename, block in zip(targets, ts_blocks):
        sections.setdefault(filename, block.strip())

    if len(sections) >= 3:
        return sections

    # Strategy 3 — complete fallback
    fallback = (
        "// WARNING: backend_agent could not parse the LLM response into sections.\n"
        "// Full response follows — split manually.\n\n"
        + raw
    )
    for filename in targets:
        sections.setdefault(filename, fallback)

    return sections


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def _write_outputs(story_id: str, sections: dict[str, str]) -> dict[str, Path]:
    """Write the three backend artefacts into the story workspace."""
    output_dir = RUN_DIR / story_id
    output_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for filename in (OUTPUT_ROUTES, OUTPUT_SERVICE, OUTPUT_VALIDATION):
        content = sections.get(filename, f"// {filename} not generated\n")
        path    = output_dir / filename
        path.write_text(content, encoding="utf-8")
        written[filename] = path

    return written


# ---------------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------------

def run(story: "UserStory", previous_results: list[dict]) -> dict:
    """
    Execute the Backend Implementation step.

    Called by StoryRunner.run_step() when wired as:
        pipeline[3].agent_fn = run

    Args:
        story:            The UserStory being processed.
        previous_results: Results from prior pipeline steps.
                          Index 0 → Story Analysis (po_agent)
                          Index 1 → UX Design      (ux_agent)
                          Index 2 → DB Design       (db_agent)

    Returns:
        dict with keys:
            status           "done" | "blocked"
            routes_file      Path to backend_routes.ts
            service_file     Path to backend_service.ts
            validation_file  Path to validation_schemas.ts
            error            Error message (only if status == "blocked")
    """
    print(f"\n  [Backend Agent] Implémentation backend pour la story {story.id}...")

    # 1. Build the prompt
    prompt = build_prompt(story)
    print(f"  [Backend Agent] Prompt construit ({len(prompt)} caractères)")

    # Log availability of prior step outputs
    for filename, label in [
        ("story_analysis.md", "Story Analysis"),
        ("ux_design.md",      "UX Design"),
        ("db_schema.sql",     "DB Schema"),
        ("database_types.ts", "DB Types"),
    ]:
        path   = RUN_DIR / story.id / filename
        status = "trouvé" if path.exists() else "absent ⚠"
        print(f"  [Backend Agent] {label} : {status}")

    # 2. Call the API
    print(f"  [Backend Agent] Appel Anthropic API (claude-sonnet-4-20250514)...")
    raw_response = _call_anthropic(prompt)
    print(f"  [Backend Agent] Réponse reçue ({len(raw_response)} caractères)")

    # 3. Parse into 3 files
    sections = _parse_response(raw_response)
    print(f"  [Backend Agent] Sections parsées : {list(sections.keys())}")

    # 4. Write outputs
    written = _write_outputs(story.id, sections)
    for filename, wpath in written.items():
        print(f"  [Backend Agent] Écrit : {wpath}")

    # Save summary for downstream agents
    summary = extract_summary(raw_response)
    save_contract(story.id, "backend", summary, label="Step 04 — Backend Implementation")
    print(f"  [Backend Agent] Contract sauvé dans contracts/backend.md")

    return {
        "status":          "done",
        "routes_file":     str(written[OUTPUT_ROUTES]),
        "service_file":    str(written[OUTPUT_SERVICE]),
        "validation_file": str(written[OUTPUT_VALIDATION]),
    }


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

def _standalone_main() -> None:
    """
    Run the Backend agent directly for a given story ID.

    Usage:
        python ai/agents/backend_agent.py AUTH-01
        python ai/agents/backend_agent.py AUTH-01 --dry-run
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="backend_agent",
        description="Backend Developer Agent — génère les routes, le service layer et les schemas Zod.",
    )
    parser.add_argument("story_id", help="ID de la story (ex: AUTH-01)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher le prompt résolu sans appeler l'API",
    )
    args = parser.parse_args()

    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from run_story import BacklogParser  # type: ignore

    backlog_path = PROJECT_ROOT / "docs" / "backlog" / "ai_sprint_backlog.md"
    story = BacklogParser(backlog_path).get_story(args.story_id)

    print(f"\nStory chargée : {story.full_title}")
    print(f"CA : {story.ac_count} critères")

    for filename, label in [
        ("story_analysis.md", "Story Analysis"),
        ("ux_design.md",      "UX Design"),
        ("db_schema.sql",     "DB Schema"),
        ("database_types.ts", "DB Types"),
    ]:
        path = RUN_DIR / story.id / filename
        print(f"  {label} : {'trouvée' if path.exists() else 'absente'}")
    print()

    prompt = build_prompt(story)

    if args.dry_run:
        print("=" * 70)
        print("PROMPT RÉSOLU (dry-run — API non appelée)")
        print("=" * 70)
        print(prompt)
        return

    result = run(story, [])

    print("\n" + "=" * 70)
    print(f"ROUTES     : {result['routes_file']}")
    print(f"SERVICE    : {result['service_file']}")
    print(f"VALIDATION : {result['validation_file']}")
    print("=" * 70)


if __name__ == "__main__":
    _standalone_main()
