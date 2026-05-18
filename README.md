# Interactive ML & Generative Models Labs

Quarto site for university labs covering PyTorch fundamentals, PCA, anomaly metrics, Isolation Forest, entropy/KL divergence, autoencoders, VAEs, GANs, WGAN-GP, and VQ-VAE.

Repository: https://github.com/machine-learning-lectures/agh-mat

Published site: https://machine-learning-lectures.github.io/agh-mat/

## Local preview

```powershell
quarto preview
```

The pages show executable Python/PyTorch scripts without evaluating them during the website build. Students can copy a script from a lab page and run it in a Python 3.11/3.12 environment.

## Lab environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## GitHub Pages

The workflow in `.github/workflows/pages.yml` renders the Quarto project and deploys the generated `_site` artifact through GitHub Pages Actions. In the repository settings, set **Pages -> Build and deployment -> Source** to **GitHub Actions**.
