# TorchCode notebooks

Ten katalog zawiera środowisko JupyterLab do ćwiczenia implementacji operatorów PyTorch oraz automatyczny judge `torch_judge`.

Wersja do czytania na telefonie jest generowana do stron Quarto w katalogu `pytorch/notebooks/` i podpinana pod wspólny indeks `materials/index.qmd`. Notebooki zostają materiałem ćwiczeniowym, a HTML jest materiałem do spokojnego przejścia krok po kroku.

## Uruchomienie lokalne

```bash
make run
```

Po starcie otwórz `http://localhost:8888`. Notebooki są kopiowane do `notebooks/`, a puste szablony resetują się przy każdym uruchomieniu kontenera.

## Jak pracować z notebookiem

1. Otwórz szablon, na przykład `01_relu.ipynb`.
2. Przeczytaj opis zadania i sygnaturę funkcji.
3. Uzupełnij komórkę `YOUR IMPLEMENTATION HERE`.
4. Uruchom komórkę debugującą.
5. Uruchom komórkę `check("...")`.
6. Gdy utkniesz, użyj `hint("...")` albo otwórz notebook z sufiksem `_solution.ipynb`.

## Generowanie stron HTML

Z poziomu katalogu głównego repozytorium:

```powershell
python scripts\prepare_pytorch_pages.py
quarto render
```

Skrypt usuwa z notebooków elementy chmurowe, aktualizuje strony `pytorch/notebooks/*.qmd` i odświeża wspólny indeks `materials/index.qmd`.
