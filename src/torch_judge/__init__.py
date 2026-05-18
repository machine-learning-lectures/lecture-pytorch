"""Local PyTorch practice judge for the lecture-pytorch notebooks.

Usage:
    from torch_judge import check, status

    status()
    check("relu")
"""

from torch_judge._version import __version__
from torch_judge.engine import check, hint
from torch_judge.progress import reset_progress, status

__all__ = ["__version__", "check", "hint", "status", "reset_progress"]
