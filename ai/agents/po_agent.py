"""
po_agent.py — Product Owner Agent
===================================
Implements the Story Analysis step (Step 01) of the AI Scrum pipeline.

Responsibilities:
    1. Load the prompt template from ai/prompts/story_analysis.md
    2. Resolve all {{placeholders}} with real UserStory data
    3. Call the Anthropic API (claude-sonnet-4-20250514)
    4. Write the analysis to .story_runs/STORY_ID/story_analysis.md
    5. Return a structured dict for the pipeline result

Integration with run_story.py:
    from ai.agents.po_agent import run as po_run
    pipeline[0].agent_fn = po_run   # Step 01 — Story Analysis

Signature expected by StoryRunner.run_step():
    agent_fn(story: UserStory, previous_results: list[dict]) -> dict

Standalone usage:
    python ai/agents/po_agent.py AUTH-01
"""

from __future__ import annotations

import json
import re
import sys
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.run_story import UserStory

# Ensure PROJECT_ROOT is importable when running the agent as a standalone script
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ai.agents.context import (  # type: ignore
    save_contract,
    build_context_instruction,
    extract_summary,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT  = Path(__file__).resolve().parent.parent.parent
PROMPT_PATH   = PROJECT_ROOT / "ai" / "prompts" / "story_analysis.md"
RUN_DIR       = PROJECT_ROOT / ".story_runs"
OUTPUT_FILE   = "story_analysis.md"

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _load_template() -> str:
    """Load the raw prompt template from ai/prompts/story_analysis.md."""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Prompt template introuvable : {PROMPT_PATH}\n"
            f"Assurez-vous que le fichier ai/prompts/story_analysis.md existe."
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
    """
    template = _load_template()

    replacements = {
        "{{story_id}}":             story.id,
        "{{story_title}}":          story.title,
        "{{story_epic}}":           story.epic,
        "{{story_narrative}}":      story.narrative or "_Non spécifiée._",
        "{{acceptance_criteria}}":  _format_criteria(story),
        "{{out_of_scope}}":         _format_out_of_scope(story),
    }

    prompt = template
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    # Sanity check — no unreplaced placeholders.
    # Ignore comment-only lines (Markdown blockquotes and HTML comments)
    # since they may legitimately contain {{ }} examples.
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
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    except ImportError:
        # Fallback: raw HTTP with urllib (no extra dependencies)
        import json
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
            "max_tokens": 4096,
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
    """Write the analysis to .story_runs/STORY_ID/story_analysis.md."""
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
    Execute the Story Analysis step.

    Called by StoryRunner.run_step() when wired as:
        pipeline[0].agent_fn = run

    Args:
        story:            The UserStory being processed.
        previous_results: Results from prior pipeline steps (empty for Step 01).

    Returns:
        dict with keys:
            status        "done" | "blocked"
            output_file   Path to the written analysis file
            invest_ready  True if INVEST verdict is READY
            analysis      Raw Markdown text returned by the LLM
            error         Error message (only present if status == "blocked")
    """
    print(f"\n  [PO Agent] Analyse de la story {story.id}...")

    # 1. Build the prompt
    prompt = build_prompt(story)
    print(f"  [PO Agent] Prompt construit ({len(prompt)} caractères)")

    # 2. Call the API
    print(f"  [PO Agent] Appel Anthropic API (claude-sonnet-4-20250514)...")
    analysis_md = _call_anthropic(prompt)
    print(f"  [PO Agent] Réponse reçue ({len(analysis_md)} caractères)")

    # 3. Write output to workspace
    output_path = _write_output(story.id, analysis_md)
    print(f"  [PO Agent] Analyse écrite : {output_path}")

    # 4. Extract summary and save to context.md for downstream agents
    summary = extract_summary(analysis_md)
    save_contract(story.id, "po", summary, label="Step 01 — Story Analysis")
    print(f"  [PO Agent] Contract sauvé dans contracts/po.md")

    # 5. Parse INVEST verdict from the response
    invest_ready = _parse_invest_verdict(analysis_md)

    return {
        "status":       "done",
        "output_file":  str(output_path),
        "invest_ready": invest_ready,
        "analysis":     analysis_md,
    }


def _parse_invest_verdict(analysis_md: str) -> bool:
    """Return True if the INVEST verdict is READY."""
    match = re.search(r"\*\*Verdict INVEST\*\*\s*:\s*(READY|NEEDS CLARIFICATION|NOT READY)", analysis_md)
    if match:
        return match.group(1) == "READY"
    return False


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

def _standalone_main() -> None:
    """
    Run the PO agent directly for a given story ID.

    Usage:
        python ai/agents/po_agent.py AUTH-01
        python ai/agents/po_agent.py TASK-04 --dry-run
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="po_agent",
        description="Product Owner Agent — analyse une User Story et produit les instructions développeurs.",
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
    from run_story import BacklogParser, UserStory  # type: ignore

    backlog_path = PROJECT_ROOT / "docs" / "backlog" / "ai_sprint_backlog.md"
    story = BacklogParser(backlog_path).get_story(args.story_id)

    print(f"\nStory chargée : {story.full_title}")
    print(f"CA : {story.ac_count} critères\n")

    prompt = build_prompt(story)

    if args.dry_run:
        print("=" * 70)
        print("PROMPT RÉSOLU (dry-run — API non appelée)")
        print("=" * 70)
        print(prompt)
        return

    result = run(story, [])

    print("\n" + "=" * 70)
    print(f"INVEST READY : {result['invest_ready']}")
    print(f"OUTPUT       : {result['output_file']}")
    print("=" * 70)
    print(result["analysis"])


if __name__ == "__main__":
    _standalone_main()
