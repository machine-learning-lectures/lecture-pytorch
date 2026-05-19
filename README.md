# Interactive ML & Generative Models Labs

Quarto site for university labs covering PyTorch fundamentals, PCA, anomaly metrics, Isolation Forest, entropy/KL divergence, autoencoders, VAEs, GANs, WGAN-GP, and VQ-VAE.

The `materials/` section is a shared mobile-readable index for classic labs and PyTorch notebook exercises. Notebook pages include step-by-step notes, judge checks, and collapsed reference solutions.

Repository: https://github.com/machine-learning-lectures/lecture-pytorch

Published site: https://machine-learning-lectures.github.io/lecture-pytorch/

## Local preview

```powershell
quarto preview
```

The pages show executable Python/PyTorch scripts without evaluating them during the website build. Students can copy a script from a lab page and run it in a Python 3.11/3.12 environment.

To refresh the generated PyTorch notebook pages:

```powershell
python scripts\prepare_pytorch_pages.py
quarto render
```

## Lab environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## GitHub Pages

The workflow in `.github/workflows/pages.yml` renders the Quarto project and deploys the generated `_site` artifact through GitHub Pages Actions. In the repository settings, set **Pages -> Build and deployment -> Source** to **GitHub Actions**.
