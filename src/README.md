# PyTorch Gym

This directory contains the notebook practice track used by the
`lecture-pytorch` course.

It includes:

- `templates/` - blank notebooks for solving PyTorch exercises
- `solutions/` - reference solutions for self-checking
- `torch_judge/` - local checker used by the notebooks

The notebooks are designed to complement the Quarto course published from the
repository root. Start with the course pages, then open the matching notebook
when you want hands-on practice.

## Local Use

Install the judge package in editable mode from the repository root:

```powershell
pip install -e ./src
```

Then open the notebooks:

```powershell
jupyter lab src/templates/00_welcome.ipynb
```

## Google Colab

The template notebooks install the checker from this repository:

```bash
pip install -q "git+https://github.com/machine-learning-lectures/lecture-pytorch.git#subdirectory=src"
```

Inside a notebook, use:

```python
from torch_judge import check, hint, status

check("relu")
hint("relu")
status()
```

