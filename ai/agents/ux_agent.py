"""
ux_agent.py — UX Designer Agent
=================================
Implements the UX Design step (Step 02) of the AI Scrum pipeline.

Responsibilities:
    1. Load the prompt template from ai/prompts/ux_design.md
    2. Read .story_runs/STORY_ID/story_analysis.md (output of Step 01)
    3. Resolve all {{placeholders}} with story data + PO analysis
    4. Call the Anthropic API (claude-sonnet-4-20250514)
    5. Write the UX spec to .story_runs/STORY_ID/ux_design.md
    6. Return a structured dict for the pipeline result

Integration with run_story.py:
    from ai.agents.ux_agent import run as ux_run
    pipeline[1].agent_fn = ux_run   # Step 02 — UX Design

Signature expected by StoryRunner.run_step():
    agent_fn(story: UserStory, previous_results: list[dict]) -> dict

Standalone usage:
    python ai/agents/ux_agent.py AUTH-01
    python ai/agents/ux_agent.py AUTH-01 --dry-run
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
PROMPT_PATH  = PROJECT_ROOT / "ai" / "prompts" / "ux_design.md"
RUN_DIR      = PROJECT_ROOT / ".story_runs"
OUTPUT_FILE  = "ux_design.md"

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _load_template() -> str:
    """Load the raw prompt template from ai/prompts/ux_design.md."""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Prompt template introuvable : {PROMPT_PATH}\n"
            f"Assurez-vous que le fichier ai/prompts/ux_design.md existe."
        )
    return PROMPT_PATH.read_text(encoding="utf-8")


def _load_story_analysis(story_id: str) -> str:
    """
    Read the Story Analysis produced by Step 01 (po_agent).

    Returns the file content, or a placeholder message if the file
    does not exist yet (e.g. when running Step 02 in isolation).
    """
    analysis_path = RUN_DIR / story_id / "story_analysis.md"
    if analysis_path.exists():
        return analysis_path.read_text(encoding="utf-8")
    return (
        "_Story Analysis non disponible — "
        "exécuter Step 01 (Story Analysis) avant Step 02._"
    )


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
        {{story_analysis}}     → content of .story_runs/STORY_ID/story_analysis.md
    """
    template = _load_template()

    replacements = {
        "{{story_id}}":             story.id,
        "{{story_title}}":          story.title,
        "{{story_epic}}":           story.epic,
        "{{story_narrative}}":      story.narrative or "_Non spécifiée._",
        "{{acceptance_criteria}}":  _format_criteria(story),
        "{{out_of_scope}}":         _format_out_of_scope(story),
        "{{story_analysis}}":       load_context(story.id) or read_artefact(
                                        story.id, "story_analysis.md",
                                        "Step 01 (Story Analysis)"
                                    ),
    }

    prompt = template
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    # Sanity check — no unreplaced placeholders.
    # Ignore comment-only lines (Markdown blockquotes and HTML comments).
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
    Call the Anthropic API and return the text response.

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
# Output writer
# ---------------------------------------------------------------------------

def _write_output(story_id: str, content: str) -> Path:
    """Write the UX design spec to .story_runs/STORY_ID/ux_design.md."""
    output_dir = RUN_DIR / story_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_FILE
    output_path.write_text(content, encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------------

def run(story: "UserStory", previous_results: list[dict]) -> dict:
    """
    Execute the UX Design step.

    Called by StoryRunner.run_step() when wired as:
        pipeline[1].agent_fn = run

    Args:
        story:            The UserStory being processed.
        previous_results: Results from prior pipeline steps.
                          Step 01 result (Story Analysis) is expected at index 0.

    Returns:
        dict with keys:
            status       "done" | "blocked"
            output_file  Path to the written UX spec file
            design       Raw Markdown text returned by the LLM
            error        Error message (only present if status == "blocked")
    """
    print(f"\n  [UX Agent] Conception UX pour la story {story.id}...")

    # 1. Build the prompt (reads story_analysis.md from workspace)
    prompt = build_prompt(story)
    print(f"  [UX Agent] Prompt construit ({len(prompt)} caractères)")

    # Log whether Story Analysis was available
    analysis_path = RUN_DIR / story.id / "story_analysis.md"
    if analysis_path.exists():
        print(f"  [UX Agent] Story Analysis chargée depuis {analysis_path}")
    else:
        print(f"  [UX Agent] ⚠ Story Analysis absente — conception sans analyse PO")

    # 2. Call the API
    print(f"  [UX Agent] Appel Anthropic API (claude-sonnet-4-20250514)...")
    design_md = _call_anthropic(prompt)
    print(f"  [UX Agent] Réponse reçue ({len(design_md)} caractères)")

    # 3. Write output to workspace
    output_path = _write_output(story.id, design_md)
    print(f"  [UX Agent] UX Design écrit : {output_path}")

    # 4. Save summary for downstream agents
    summary = extract_summary(design_md)
    save_contract(story.id, "ux", summary, label="Step 02A — UX Design")
    print(f"  [UX Agent] Contract sauvé dans contracts/ux.md")

    return {
        "status":      "done",
        "output_file": str(output_path),
        "design":      design_md,
    }


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

def _standalone_main() -> None:
    """
    Run the UX agent directly for a given story ID.

    Usage:
        python ai/agents/ux_agent.py AUTH-01
        python ai/agents/ux_agent.py AUTH-01 --dry-run
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="ux_agent",
        description="UX Designer Agent — produit la spécification UX d'une User Story.",
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

    analysis_path = RUN_DIR / story.id / "story_analysis.md"
    print(f"Story Analysis : {'trouvée' if analysis_path.exists() else 'absente'}\n")

    prompt = build_prompt(story)

    if args.dry_run:
        print("=" * 70)
        print("PROMPT RÉSOLU (dry-run — API non appelée)")
        print("=" * 70)
        print(prompt)
        return

    result = run(story, [])

    print("\n" + "=" * 70)
    print(f"OUTPUT : {result['output_file']}")
    print("=" * 70)
    print(result["design"])


if __name__ == "__main__":
    _standalone_main()
