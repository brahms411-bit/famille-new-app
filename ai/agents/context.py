"""
context.py — Shared context management for AI Scrum pipeline agents
=====================================================================
Solves the O(n²) context growth problem: without this module, each
agent re-injects the full output of every previous step into its prompt.
A realistic Step 05 prompt would exceed 25 000 chars before any
agent-specific content.

Architecture
------------
Each agent, after writing its artefacts, writes a **dense contract**
to .story_runs/STORY_ID/contracts/{step}.md  The contract is generated
by the LLM itself (via build_context_instruction / extract_summary),
so it costs ~0 extra tokens.

Ordering guarantee
------------------
ChatGPT-style alphabetical sort or hardcoded name lists are fragile:
a renamed step or a step replayed out-of-order silently corrupts the
context. We solve this with contracts/index.json, which records the
exact insertion order at write time. load_context() reads index.json
first and concatenates contracts in that order.

Files written per story run
---------------------------
.story_runs/STORY_ID/
    contracts/
        index.json          <- insertion-order registry  [{"step":"po","label":"..."},...]
        po.md               <- PO Agent contract
        ux.md               <- UX Agent contract
        db.md               <- DB Agent contract
        backend.md          <- Backend Agent contract
        frontend.md         <- Frontend Agent contract   (future)
        test.md             <- Test Agent contract       (future)
        qa.md               <- QA Agent contract         (future)

Public API
----------
    save_contract(story_id, step, contract_text, label="")
        Write one contract file and update index.json.
        Replaces the old save_summary().

    load_context(story_id) -> str
        Concatenate all contracts in insertion order.
        Returns "" if no contracts exist yet (Step 01 first run).

    build_context_instruction() -> str
        Prompt fragment appended to every agent prompt.
        Asks the LLM to produce a CONTEXT_SUMMARY block.

    extract_summary(llm_response) -> str
        Extract the <!-- CONTEXT_SUMMARY --> block from the LLM response.
        Falls back gracefully if the LLM omitted the block.

    read_artefact(story_id, filename, step_label, max_chars) -> str
        Bounded artefact reader (hard ceiling at max_chars).
        Use instead of raw Path.read_text() for technical contracts
        that cannot be summarised without data loss (SQL, TS types).

Migration note
--------------
    save_summary() has been renamed to save_contract().
    All agents must import save_contract instead of save_summary.
    The old context.md file is no longer written; contracts/ replaces it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT  = Path(__file__).resolve().parent.parent.parent
RUN_DIR       = PROJECT_ROOT / ".story_runs"
CONTRACTS_DIR = "contracts"
INDEX_FILE    = "index.json"

# Default per-artefact character budget (~1 000 tokens).
DEFAULT_MAX_CHARS = 4_000


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _contracts_dir(story_id: str) -> Path:
    return RUN_DIR / story_id / CONTRACTS_DIR


def _index_path(story_id: str) -> Path:
    return _contracts_dir(story_id) / INDEX_FILE


def _load_index(story_id: str) -> list[dict]:
    """
    Return the ordered list of registered contracts.

    Each entry: {"step": "po", "label": "Step 01 - Story Analysis"}
    Returns [] if no contracts have been written yet.
    """
    path = _index_path(story_id)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_index(story_id: str, index: list[dict]) -> None:
    path = _index_path(story_id)
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Contract write
# ---------------------------------------------------------------------------

def save_contract(
    story_id:      str,
    step:          str,
    contract_text: str,
    label:         str = "",
) -> Path:
    """
    Write a contract file for one pipeline step and update index.json.

    Replaces the former save_summary().  The contract is always generated
    by the LLM (via build_context_instruction / extract_summary) — no
    Python parsing of artefacts.

    If this step already has a contract (step replayed), the file is
    overwritten and the index entry is updated in-place, preserving the
    original insertion order.

    Args:
        story_id:      e.g. "AUTH-01"
        step:          Short key used as filename stem — e.g. "po", "ux", "db".
                       Must be alphanumeric + hyphens/underscores only.
        contract_text: Dense plain-text contract generated by the LLM.
        label:         Human-readable label for the index, e.g.
                       "Step 01 - Story Analysis".  Defaults to step.

    Returns:
        Path to the written contract file.
    """
    contracts_dir = _contracts_dir(story_id)
    contracts_dir.mkdir(parents=True, exist_ok=True)

    # Sanitise step key
    safe_step     = re.sub(r"[^\w\-]", "_", step)
    contract_path = contracts_dir / f"{safe_step}.md"

    header = (
        f"# Contract — {label or safe_step}\n"
        f"_Story: {story_id} · Generated by AI Scrum Runner_\n\n"
    )
    contract_path.write_text(
        header + contract_text.strip() + "\n",
        encoding="utf-8",
    )

    # Update index — insert if new, update in-place if replayed
    index = _load_index(story_id)
    entry = {"step": safe_step, "label": label or safe_step}
    existing = [i for i, e in enumerate(index) if e["step"] == safe_step]
    if existing:
        index[existing[0]] = entry   # update label if changed, keep position
    else:
        index.append(entry)          # first time: append preserves run order
    _save_index(story_id, index)

    return contract_path


# ---------------------------------------------------------------------------
# Context load
# ---------------------------------------------------------------------------

def load_context(story_id: str) -> str:
    """
    Return the accumulated context for this story run.

    Reads all contracts in the order recorded in index.json (= pipeline
    execution order, not filesystem / alphabetical order).

    Returns "" if no contracts have been written yet (safe for Step 01).
    """
    index = _load_index(story_id)
    if not index:
        return ""

    contracts_dir = _contracts_dir(story_id)
    parts: list[str] = []
    for entry in index:
        path = contracts_dir / f"{entry['step']}.md"
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))

    return "\n---\n".join(parts) if parts else ""


# ---------------------------------------------------------------------------
# Artefact reader with truncation
# ---------------------------------------------------------------------------

def read_artefact(
    story_id:   str,
    filename:   str,
    step_label: str,
    max_chars:  int = DEFAULT_MAX_CHARS,
) -> str:
    """
    Read a workspace artefact, truncating gracefully at max_chars.

    Use instead of raw Path.read_text() for technical artefacts injected
    directly (SQL schema, TS types) — data that cannot be summarised
    without precision loss.

    Args:
        story_id:   e.g. "AUTH-01"
        filename:   e.g. "db_schema.sql"
        step_label: Human label for the missing-file warning.
        max_chars:  Hard ceiling on returned content (default 4 000).

    Returns:
        File content (possibly truncated) or a placeholder string.
    """
    path = RUN_DIR / story_id / filename
    if not path.exists():
        return (
            f"_{filename} non disponible — "
            f"exécuter {step_label} avant cette étape._"
        )

    content = path.read_text(encoding="utf-8")
    if len(content) <= max_chars:
        return content

    truncated = content[:max_chars]
    last_nl   = truncated.rfind("\n")
    if last_nl > max_chars * 0.8:
        truncated = truncated[:last_nl]

    original_tokens = len(content) // 4
    kept_tokens     = len(truncated) // 4
    return (
        truncated
        + f"\n\n... [tronque - {original_tokens} tokens total, "
        f"{kept_tokens} tokens injectes. Lire {filename} pour le contenu complet.]\n"
    )


# ---------------------------------------------------------------------------
# Prompt fragment — instructs the LLM to produce its own contract
# ---------------------------------------------------------------------------

_CONTRACT_INSTRUCTION = """

---
**Instruction finale - obligatoire**

Avant de terminer ta reponse, ajoute ton contract pour les agents suivants :

<!-- CONTEXT_SUMMARY -->
[Contract dense en 3-6 lignes MAX. Inclure :
 - Les decisions cles prises
 - Les noms exacts des types / tables / routes / composants produits
 - Les contraintes importantes pour les agents suivants
 - Ce qui a ete mis hors perimetre
Ne pas repeter les CA - uniquement les decisions et artefacts.]
<!-- END_CONTEXT_SUMMARY -->
"""


def build_context_instruction() -> str:
    """
    Return the prompt fragment appended to every agent system prompt.

    Asks the LLM to produce a CONTEXT_SUMMARY block at the end of its
    response. This block is extracted by extract_summary() and written
    as a per-step contract via save_contract().
    """
    return _CONTRACT_INSTRUCTION


def extract_summary(llm_response: str) -> str:
    """
    Extract the <!-- CONTEXT_SUMMARY --> block from an LLM response.

    Falls back gracefully if the LLM omitted the block, so save_contract()
    always has something meaningful to write.

    Args:
        llm_response: Raw text returned by the Anthropic API.

    Returns:
        Extracted contract text (stripped), or a fallback string.
    """
    match = re.search(
        r"<!--\s*CONTEXT_SUMMARY\s*-->(.*?)<!--\s*END_CONTEXT_SUMMARY\s*-->",
        llm_response,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    # Fallback: last non-empty, non-code paragraph
    paragraphs     = [p.strip() for p in llm_response.split("\n\n") if p.strip()]
    text_paragraphs = [p for p in paragraphs if not p.startswith("```")]
    if text_paragraphs:
        return text_paragraphs[-1][:400]

    return "(contract non disponible - LLM n'a pas produit de bloc CONTEXT_SUMMARY)"
