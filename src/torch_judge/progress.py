"""Track solved/attempted/todo progress in a local JSON file."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from torch_judge.tasks import list_tasks

PROGRESS_PATH = os.environ.get("PROGRESS_PATH", "data/progress.json")

_COLORS = {
    "solved": "\033[92m[ok]",
    "attempted": "\033[93m[try]",
    "todo": "\033[90m[todo]",
}
_DIFF_COLORS = {
    "Easy": "\033[92m",
    "Medium": "\033[93m",
    "Hard": "\033[91m",
}
_RESET = "\033[0m"


def _load() -> dict[str, Any]:
    path = Path(PROGRESS_PATH)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save(data: dict[str, Any]) -> None:
    path = Path(PROGRESS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def mark_solved(task_id: str, exec_time: float | None = None) -> None:
    data = _load()
    entry = data.get(task_id, {})
    entry["status"] = "solved"
    entry["solved_at"] = datetime.now().isoformat()
    if exec_time is not None:
        best = entry.get("best_time")
        entry["best_time"] = min(best, exec_time) if best else exec_time
    entry["attempts"] = entry.get("attempts", 0) + 1
    data[task_id] = entry
    _save(data)


def mark_attempted(task_id: str) -> None:
    data = _load()
    entry = data.get(task_id, {})
    if entry.get("status") != "solved":
        entry["status"] = "attempted"
    entry["attempts"] = entry.get("attempts", 0) + 1
    data[task_id] = entry
    _save(data)


def status() -> None:
    """Print a dashboard of all problems and their status."""
    data = _load()
    tasks = list_tasks()

    solved_count = sum(
        1 for task_id, _ in tasks if data.get(task_id, {}).get("status") == "solved"
    )
    total = len(tasks)

    print(f"\n{'-' * 56}")
    print(f"  PyTorch Gym Progress: {solved_count}/{total} solved")
    print(f"{'-' * 56}")

    for task_id, task in tasks:
        entry = data.get(task_id, {})
        state = entry.get("status", "todo")
        icon = _COLORS.get(state, _COLORS["todo"])
        difficulty = task["difficulty"]
        diff_color = _DIFF_COLORS.get(difficulty, "")
        best = entry.get("best_time")
        time_text = f"  {best * 1000:.1f}ms" if best else ""
        attempts = entry.get("attempts", 0)
        attempts_text = f"  ({attempts} attempts)" if attempts else ""

        print(
            f"  {icon} {task_id:<20s}{_RESET} "
            f"{diff_color}[{difficulty}]{_RESET}{time_text}{attempts_text}"
        )
        print(f"     {task['title']}")

    print(f"{'-' * 56}\n")


def reset_progress() -> None:
    """Clear all progress."""
    path = Path(PROGRESS_PATH)
    if path.exists():
        path.unlink()
    print("Progress reset.")
