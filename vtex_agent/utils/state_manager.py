"""State management for persistent workflow execution."""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

STATE_DIR = Path(__file__).parent.parent.parent / "state"


def ensure_state_dir():
    """Ensure state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def save_state(step_name: str, data: Dict[str, Any]) -> str:
    """
    Save state to a JSON file.
    
    Args:
        step_name: Name of the step (e.g., 'discovery', 'mapping', 'extraction')
        data: State data to persist
        
    Returns:
        Path to saved state file
    """
    ensure_state_dir()
    state_file = STATE_DIR / f"{step_name}.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return str(state_file)


def load_state(step_name: str) -> Optional[Dict[str, Any]]:
    """
    Load state from a JSON file.
    
    Args:
        step_name: Name of the step to load
        
    Returns:
        State data or None if file doesn't exist
    """
    state_file = STATE_DIR / f"{step_name}.json"
    if not state_file.exists():
        return None
    with open(state_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_state_path(step_name: str) -> str:
    """Get the path to a state file without loading it."""
    return str(STATE_DIR / f"{step_name}.json")


def save_custom_prompt(instructions: str) -> str:
    """
    Save custom extraction prompt instructions to state.
    
    Args:
        instructions: Custom instructions to append to extraction prompts
        
    Returns:
        Path to saved state file
    """
    ensure_state_dir()
    state_file = STATE_DIR / "custom_prompt.json"
    data = {
        "instructions": instructions,
        "updated_at": str(Path(__file__).stat().st_mtime) if Path(__file__).exists() else None
    }
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return str(state_file)


def load_custom_prompt() -> Optional[str]:
    """
    Load custom extraction prompt instructions from state.
    
    Returns:
        Custom instructions string or None if not found
    """
    state_file = STATE_DIR / "custom_prompt.json"
    if not state_file.exists():
        return None
    with open(state_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("instructions")

