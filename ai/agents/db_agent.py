"""
db_agent.py — Database Developer Agent
========================================
Implements the Database Design step (Step 03) of the AI Scrum pipeline.

Responsibilities:
    1. Load the prompt template from ai/prompts/db_design.md
    2. Read .story_runs/STORY_ID/story_analysis.md (output of Step 01)
    3. Read .story_runs/STORY_ID/ux_design.md      (output of Step 02)
    4. Resolve all {{placeholders}} with story data + prior step outputs
    5. Call the Anthropic API (claude-sonnet-4-20250514)
    6. Parse the LLM response into 3 separate files
    7. Write to the story workspace:
         .story_runs/STORY_ID/db_schema.sql
         .story_runs/STORY_ID/rls_policies.sql
         .story_runs/STORY_ID/database_types.ts
    8. Return a structured dict for the pipeline result

Integration with run_story.py:
    from ai.agents.db_agent import run as db_run
    pipeline[2].agent_fn = db_run   # Step 03 — Database Design

Signature expected by StoryRunner.run_step():
    agent_fn(story: UserStory, previous_results: list[dict]) -> dict

Standalone usage:
    python ai/agents/db_agent.py AUTH-01
    python ai/agents/db_agent.py AUTH-01 --dry-run
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
PROMPT_PATH  = PROJECT_ROOT / "ai" / "prompts" / "db_design.md"
RUN_DIR      = PROJECT_ROOT / ".story_runs"

# Output file names written to .story_runs/STORY_ID/
OUTPUT_SCHEMA  = "db_schema.sql"
OUTPUT_RLS     = "rls_policies.sql"
OUTPUT_TYPES   = "database_types.ts"

# ---------------------------------------------------------------------------
# Workspace readers — graceful fallback when prior steps haven't run yet
# ---------------------------------------------------------------------------

def _read_workspace_file(story_id: str, filename: str, step_label: str) -> str:
    """
    Read a file from the story workspace.

    Returns the file content, or a descriptive placeholder if the file
    does not exist (e.g. when running Step 03 in isolation / dry-run).
    """
    path = RUN_DIR / story_id / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return (
        f"_{filename} non disponible — "
        f"exécuter {step_label} avant Step 03._"
    )


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _load_template() -> str:
    """Load the raw prompt template from ai/prompts/db_design.md."""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Prompt template introuvable : {PROMPT_PATH}\n"
            f"Assurez-vous que le fichier ai/prompts/db_design.md existe."
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
        {{story_analysis}}     → content of story_analysis.md (Step 01)
        {{ux_design}}          → content of ux_design.md      (Step 02)
    """
    template = _load_template()

    replacements = {
        "{{story_id}}":             story.id,
        "{{story_title}}":          story.title,
        "{{story_epic}}":           story.epic,
        "{{story_narrative}}":      story.narrative or "_Non spécifiée._",
        "{{acceptance_criteria}}":  _format_criteria(story),
        "{{out_of_scope}}":         _format_out_of_scope(story),
        # Use the accumulated context summary (context.md) instead of
        # re-injecting full artefact files — keeps prompt size bounded.
        "{{story_analysis}}":       load_context(story.id) or _read_workspace_file(
                                        story.id, "story_analysis.md",
                                        "Step 01 (Story Analysis)"
                                    ),
        "{{ux_design}}":            "",  # covered by context.md above
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
        # Fallback: raw HTTP with urllib (no extra dependencies)
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
# Response parser — splits one LLM response into 3 files
# ---------------------------------------------------------------------------

def _parse_response(raw: str) -> dict[str, str]:
    """
    Parse the LLM response into three separate file contents.

    Expected format in the response (set by db_design.md prompt):

        <!-- SECTION: db_schema.sql -->
        ```sql
        ...
        ```

        <!-- SECTION: rls_policies.sql -->
        ```sql
        ...
        ```

        <!-- SECTION: database_types.ts -->
        ```typescript
        ...
        ```

    Strategy:
        1. Try the structured <!-- SECTION: filename --> marker approach.
        2. Fall back to heuristic code-block extraction if markers are absent.
        3. If extraction fails, write the full raw response to all three files
           so the developer has something to work with.
    """
    sections: dict[str, str] = {}

    # Strategy 1 — section markers
    # Match: <!-- SECTION: filename --> followed by a fenced code block
    section_pattern = re.compile(
        r"<!--\s*SECTION:\s*(\S+)\s*-->\s*```[a-z]*\n(.*?)```",
        re.DOTALL,
    )
    for match in section_pattern.finditer(raw):
        filename = match.group(1).strip()
        content  = match.group(2).strip()
        sections[filename] = content

    if len(sections) >= 3:
        return sections

    # Strategy 2 — heuristic: extract fenced code blocks by language tag
    # The prompt always requests sql (×2) then typescript (×1) in that order.
    sql_blocks = re.findall(r"```sql\n(.*?)```", raw, re.DOTALL)
    ts_blocks  = re.findall(r"```typescript\n(.*?)```", raw, re.DOTALL)

    if sql_blocks:
        sections.setdefault(OUTPUT_SCHEMA, sql_blocks[0].strip())
    if len(sql_blocks) >= 2:
        sections.setdefault(OUTPUT_RLS, sql_blocks[1].strip())
    if ts_blocks:
        sections.setdefault(OUTPUT_TYPES, ts_blocks[0].strip())

    if len(sections) >= 3:
        return sections

    # Strategy 3 — complete fallback: write full response to all files
    # with a header comment so the developer knows what happened.
    fallback = (
        "-- WARNING: db_agent could not parse the LLM response into sections.\n"
        "-- Full response follows — split manually.\n\n"
        + raw
    )
    sections.setdefault(OUTPUT_SCHEMA, fallback)
    sections.setdefault(OUTPUT_RLS,    fallback)
    sections.setdefault(OUTPUT_TYPES,  fallback)
    return sections


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def _write_outputs(story_id: str, sections: dict[str, str]) -> dict[str, Path]:
    """
    Write the three database artefacts into the story workspace.

    Returns a mapping {filename: Path} for the three written files.
    """
    output_dir = RUN_DIR / story_id
    output_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for filename in (OUTPUT_SCHEMA, OUTPUT_RLS, OUTPUT_TYPES):
        content = sections.get(filename, f"-- {filename} not generated\n")
        path    = output_dir / filename
        path.write_text(content, encoding="utf-8")
        written[filename] = path

    return written


# ---------------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------------

def run(story: "UserStory", previous_results: list[dict]) -> dict:
    """
    Execute the Database Design step.

    Called by StoryRunner.run_step() when wired as:
        pipeline[2].agent_fn = run

    Args:
        story:            The UserStory being processed.
        previous_results: Results from prior pipeline steps.
                          Index 0 → Story Analysis (po_agent)
                          Index 1 → UX Design     (ux_agent)

    Returns:
        dict with keys:
            status       "done" | "blocked"
            schema_file  Path to db_schema.sql
            rls_file     Path to rls_policies.sql
            types_file   Path to database_types.ts
            error        Error message (only present if status == "blocked")
    """
    print(f"\n  [DB Agent] Conception base de données pour la story {story.id}...")

    # 1. Build the prompt (reads story_analysis.md and ux_design.md from workspace)
    prompt = build_prompt(story)
    print(f"  [DB Agent] Prompt construit ({len(prompt)} caractères)")

    # Log availability of prior step outputs
    for filename, label in [
        ("story_analysis.md", "Story Analysis"),
        ("ux_design.md",      "UX Design"),
    ]:
        path = RUN_DIR / story.id / filename
        status = "trouvé" if path.exists() else "absent ⚠"
        print(f"  [DB Agent] {label} : {status}")

    # 2. Call the API
    print(f"  [DB Agent] Appel Anthropic API (claude-sonnet-4-20250514)...")
    raw_response = _call_anthropic(prompt)
    print(f"  [DB Agent] Réponse reçue ({len(raw_response)} caractères)")

    # 3. Parse the response into 3 files
    sections = _parse_response(raw_response)
    print(f"  [DB Agent] Sections parsées : {list(sections.keys())}")

    # 4. Write outputs to workspace
    written = _write_outputs(story.id, sections)
    for filename, wpath in written.items():
        print(f"  [DB Agent] Écrit : {wpath}")

    # Save summary for downstream agents
    summary = extract_summary(raw_response)
    save_contract(story.id, "db", summary, label="Step 02B — Database Design")
    print(f"  [DB Agent] Contract sauvé dans contracts/db.md")

    return {
        "status":      "done",
        "schema_file": str(written[OUTPUT_SCHEMA]),
        "rls_file":    str(written[OUTPUT_RLS]),
        "types_file":  str(written[OUTPUT_TYPES]),
    }


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

def _standalone_main() -> None:
    """
    Run the DB agent directly for a given story ID.

    Usage:
        python ai/agents/db_agent.py AUTH-01
        python ai/agents/db_agent.py AUTH-01 --dry-run
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="db_agent",
        description="Database Developer Agent — génère le schéma SQL, les policies RLS et les types TypeScript.",
    )
    parser.add_argument("story_id", help="ID de la story (ex: AUTH-01)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher le prompt résolu sans appeler l'API",
    )
    args = parser.parse_args()

    # Load story from backlog
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from run_story import BacklogParser  # type: ignore

    backlog_path = PROJECT_ROOT / "docs" / "backlog" / "ai_sprint_backlog.md"
    story = BacklogParser(backlog_path).get_story(args.story_id)

    print(f"\nStory chargée : {story.full_title}")
    print(f"CA : {story.ac_count} critères")

    for filename, label in [
        ("story_analysis.md", "Story Analysis"),
        ("ux_design.md",      "UX Design"),
    ]:
        path = RUN_DIR / story.id / filename
        print(f"{label} : {'trouvée' if path.exists() else 'absente'}")
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
    print(f"SCHEMA  : {result['schema_file']}")
    print(f"RLS     : {result['rls_file']}")
    print(f"TYPES   : {result['types_file']}")
    print("=" * 70)


if __name__ == "__main__":
    _standalone_main()
