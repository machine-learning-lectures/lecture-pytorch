#!/usr/bin/env python3
"""Prepare PyTorch notebook material for the Quarto website.

The Jupyter notebooks stay usable as exercises, but Colab-specific cells and
badges are removed. For reading, each notebook is converted into a compact
Quarto page with the task, implementation skeleton, tests, and a collapsed
reference solution.
"""

from __future__ import annotations

import ast
import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "src" / "templates"
SOLUTIONS_DIR = ROOT / "src" / "solutions"
TASKS_DIR = ROOT / "src" / "torch_judge" / "tasks"
OUT_DIR = ROOT / "pytorch"
PAGES_DIR = OUT_DIR / "notebooks"
MATERIALS_DIR = ROOT / "materials"

COLAB_BADGE_RE = re.compile(
    r"\[!\[Open In? Colab\]\(https://colab\.research\.google\.com/assets/colab-badge\.svg\)\]"
    r"\([^)]+\)\s*",
    flags=re.IGNORECASE,
)
HTML_COLAB_LINK_RE = re.compile(
    r"\s*(?:&middot;|·)?\s*<a href=\"https://colab\.research\.google\.com/[^\"]+\""
    r"[^>]*>Colab</a>",
    flags=re.IGNORECASE,
)
MD_COLAB_LINK_RE = re.compile(
    r"\[([^\]]*Colab[^\]]*)\]\(https://colab\.research\.google\.com/[^)]+\)",
    flags=re.IGNORECASE,
)
CHECK_RE = re.compile(r"check\([\"']([^\"']+)[\"']\)")
TITLE_RE = re.compile(r"^#\s+(.+)$", flags=re.MULTILINE)


CATEGORIES: list[tuple[str, list[int]]] = [
    ("Fundamenty tensorów", [1, 2, 16, 17, 18, 19, 20, 21, 31, 40, 3, 4, 7, 8, 15, 22]),
    ("Attention i Transformery", [23, 5, 6, 9, 10, 11, 12, 14, 24, 25]),
    ("Architektura i adaptacja", [26, 27, 13, 28]),
    ("Trening i optymalizacja", [29, 30]),
    ("Inferencja i dekodowanie", [32, 33, 34]),
    ("Zaawansowane tematy", [35, 36, 37, 38, 39]),
]

LAB_CATEGORIES: list[tuple[str, list[dict[str, str]]]] = [
    (
        "Podstawy ML i PyTorch",
        [
            {
                "title": "1. Intro to PyTorch",
                "href": "../labs/lab-01-pytorch.qmd",
                "tools": "`torch.Tensor`, `autograd`",
                "summary": "Tensory, widoki, operacje wektorowe i gradienty.",
            },
            {
                "title": "2. Backpropagation",
                "href": "../labs/lab-02-backprop.qmd",
                "tools": "raw tensor matmul",
                "summary": "Ręczne gradienty dla mnożenia macierzy i weryfikacja autograd.",
            },
            {
                "title": "3. PCA",
                "href": "../labs/lab-03-pca.qmd",
                "tools": "`torch.linalg.svd`",
                "summary": "Centrowanie danych, SVD i wariancja wyjaśniona.",
            },
            {
                "title": "4. Metrics",
                "href": "../labs/lab-04-metrics.qmd",
                "tools": "precision, recall, `F_beta`",
                "summary": "Precision, recall i F-beta przy niezbalansowanych klasach.",
            },
            {
                "title": "5. Isolation Forest",
                "href": "../labs/lab-05-isolation-forest.qmd",
                "tools": "`IsolationForest`",
                "summary": "Izolowanie anomalii krótkimi ścieżkami w losowych drzewach.",
            },
            {
                "title": "6. Entropy and KL",
                "href": "../labs/lab-06-entropy-kl.qmd",
                "tools": "entropy, KL",
                "summary": "Niepewność rozkładu i koszt użycia przybliżenia.",
            },
        ],
    ),
    (
        "Modele generatywne",
        [
            {
                "title": "7. Autoencoder",
                "href": "../labs/lab-07-autoencoder.qmd",
                "tools": "`nn.Module`, MSE",
                "summary": "Bottleneck, rekonstrukcja i wykrywanie anomalii.",
            },
            {
                "title": "8. VAE",
                "href": "../labs/lab-08-vae.qmd",
                "tools": "VAE, ELBO",
                "summary": "Reparameterization trick, ELBO i generowanie próbek.",
            },
            {
                "title": "9. GAN",
                "href": "../labs/lab-09-gan.qmd",
                "tools": "GAN, BCE",
                "summary": "Dwóch optymalizatorów: generator kontra dyskryminator.",
            },
            {
                "title": "10. WGAN-GP",
                "href": "../labs/lab-10-wgan-gp.qmd",
                "tools": "gradient penalty",
                "summary": "Wasserstein distance i gradient penalty.",
            },
            {
                "title": "11. VQ-VAE",
                "href": "../labs/lab-11-vq-vae.qmd",
                "tools": "VQ, codebook",
                "summary": "Dyskretny codebook, nearest neighbor i straight-through estimator.",
            },
        ],
    ),
]


@dataclass
class NotebookPage:
    number: int
    slug: str
    filename: str
    solution_filename: str
    task_id: str
    title: str
    difficulty: str
    function_name: str
    hint: str
    body_markdown: str
    imports_code: list[str]
    skeleton_code: str
    debug_code: list[str]
    check_code: str
    solution_code: list[str]
    test_names: list[str]

    @property
    def page_filename(self) -> str:
        return f"{self.number:02d}-{self.slug}.qmd"

    @property
    def href(self) -> str:
        return f"pytorch/notebooks/{self.page_filename}"


def read_notebook(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_notebook(path: Path, nb: dict[str, Any]) -> None:
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def source(cell: dict[str, Any]) -> str:
    cell_source = cell.get("source", [])
    if isinstance(cell_source, list):
        return "".join(cell_source)
    return str(cell_source)


def set_source(cell: dict[str, Any], text: str) -> None:
    cell["source"] = text.splitlines(keepends=True)


def is_colab_install_cell(cell: dict[str, Any]) -> bool:
    text = source(cell)
    return (
        cell.get("cell_type") == "code"
        and "google.colab" in text
        and "torch-judge" in text
    )


def clean_colab_markdown(text: str) -> str:
    text = COLAB_BADGE_RE.sub("", text)
    text = HTML_COLAB_LINK_RE.sub("", text)
    text = MD_COLAB_LINK_RE.sub(lambda match: match.group(1), text)

    kept_lines: list[str] = []
    for line in text.splitlines():
        if "colab" in line.lower():
            continue
        if "colab.research.google.com" in line.lower():
            continue
        if "open in colab" in line.lower():
            continue
        if "google colab" in line.lower():
            continue
        if "colab toolbar" in line.lower():
            continue
        kept_lines.append(line.rstrip())

    cleaned = "\n".join(kept_lines)
    cleaned = re.sub(r"[ \t]+·[ \t]*(?=\|)", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned + ("\n" if cleaned else "")


def clean_notebook(path: Path) -> bool:
    nb = read_notebook(path)
    original = json.dumps(nb, ensure_ascii=False, sort_keys=True)
    cells: list[dict[str, Any]] = []

    for cell in nb.get("cells", []):
        if is_colab_install_cell(cell):
            continue
        if cell.get("cell_type") == "markdown":
            set_source(cell, clean_colab_markdown(source(cell)))
        cells.append(cell)

    nb["cells"] = cells
    updated = json.dumps(nb, ensure_ascii=False, sort_keys=True) != original
    if updated:
        write_notebook(path, nb)
    return updated


def clean_all_notebooks() -> int:
    updated = 0
    for folder in (TEMPLATES_DIR, SOLUTIONS_DIR):
        for path in sorted(folder.glob("*.ipynb")):
            if clean_notebook(path):
                updated += 1
    return updated


def load_tasks() -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    for path in sorted(TASKS_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if any(isinstance(target, ast.Name) and target.id == "TASK" for target in node.targets):
                tasks[path.stem] = ast.literal_eval(node.value)
                break
    return tasks


def extract_task_id(nb: dict[str, Any], fallback: str) -> str:
    for cell in nb.get("cells", []):
        match = CHECK_RE.search(source(cell))
        if match:
            return match.group(1)
    return fallback


def clean_title(raw: str, fallback: str) -> str:
    match = TITLE_RE.search(raw)
    title = match.group(1).strip() if match else fallback
    title = re.sub(r"^[^\w`]+", "", title).strip()
    title = re.sub(r"^(Easy|Medium|Hard):\s+", "", title, flags=re.IGNORECASE)
    return title or fallback


def markdown_without_title(text: str) -> str:
    text = TITLE_RE.sub("", text, count=1)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def classify_code_cells(nb: dict[str, Any]) -> tuple[list[str], str, list[str], str]:
    imports: list[str] = []
    skeleton = ""
    debug: list[str] = []
    check = ""

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        text = source(cell).strip()
        if not text:
            continue
        if CHECK_RE.search(text):
            check = text
        elif "YOUR IMPLEMENTATION HERE" in text or "Replace this" in text or "\n    pass" in text:
            skeleton = text
        elif text.startswith("import ") or text.startswith("from "):
            imports.append(text)
        else:
            debug.append(text)

    return imports, skeleton, debug, check


def solution_cells(nb: dict[str, Any]) -> list[str]:
    cells: list[str] = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        text = source(cell).strip()
        if not text or CHECK_RE.search(text):
            continue
        cells.append(text)
    return cells


def notebook_number(path: Path) -> int:
    return int(path.name.split("_", 1)[0])


def make_page(path: Path, tasks: dict[str, dict[str, Any]]) -> NotebookPage:
    nb = read_notebook(path)
    first_md = next((source(cell) for cell in nb.get("cells", []) if cell.get("cell_type") == "markdown"), "")
    task_id = extract_task_id(nb, path.stem.removeprefix(f"{notebook_number(path):02d}_"))
    task = tasks.get(task_id, {})
    number = notebook_number(path)
    slug = path.stem.split("_", 1)[1].replace("_", "-")
    imports, skeleton, debug, check = classify_code_cells(nb)
    solution_path = SOLUTIONS_DIR / f"{path.stem}_solution.ipynb"
    solution = solution_cells(read_notebook(solution_path)) if solution_path.exists() else []

    return NotebookPage(
        number=number,
        slug=slug,
        filename=path.name,
        solution_filename=solution_path.name,
        task_id=task_id,
        title=task.get("title") or clean_title(first_md, path.stem),
        difficulty=task.get("difficulty", "Practice"),
        function_name=task.get("function_name", ""),
        hint=task.get("hint", ""),
        body_markdown=markdown_without_title(first_md),
        imports_code=imports,
        skeleton_code=skeleton,
        debug_code=debug,
        check_code=check,
        solution_code=solution,
        test_names=[test.get("name", "Test") for test in task.get("tests", [])],
    )


def fence(code: str) -> str:
    return f"```python\n{code.rstrip()}\n```"


def plain_text(value: str) -> str:
    return html.escape(value, quote=False)


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def difficulty_class(difficulty: str) -> str:
    return {
        "Easy": "easy",
        "Medium": "medium",
        "Hard": "hard",
    }.get(difficulty, "practice")


def page_markdown(page: NotebookPage, previous: NotebookPage | None, next_page: NotebookPage | None) -> str:
    parts: list[str] = [
        "---",
        f"title: {yaml_string(f'{page.number:02d}. {page.title}')}",
        f"description: {yaml_string(f'HTMLowa wersja notebooka {page.filename}.')}",
        "---",
        "",
        "::: {.lesson-meta}",
        f"**Poziom:** `{page.difficulty}`<br>",
        f"**Funkcja/klasa:** `{page.function_name or page.task_id}`<br>",
        f"**Notebook:** [`{page.filename}`](../../src/templates/{page.filename})",
        ":::",
        "",
        "::: {.lab-question}",
        "**Cel lekcji:** zrozum, jaki tensor wchodzi do funkcji, jaki tensor powinien wyjść, a potem zobacz minimalną implementację.",
        ":::",
        "",
        "## Treść zadania",
        "",
        page.body_markdown,
        "",
        "## Krok po kroku",
        "",
        "1. Przeczytaj sygnaturę i zapisz w głowie kształty tensorów.",
        "2. Odszukaj operację matematyczną: redukcję, mnożenie macierzy, maskowanie, indeksowanie albo moduł `nn.Module`.",
        "3. Zaimplementuj tylko brakujący fragment w szkielecie. Nie zaczynaj od optymalizacji.",
        "4. Uruchom mini-debug z notebooka i sprawdź kształty oraz wartości graniczne.",
        "5. Dopiero na końcu porównaj z rozwiązaniem referencyjnym.",
        "",
    ]

    if page.hint:
        parts.extend([
            "::: {.callout-tip}",
            "## Wskazówka",
            plain_text(page.hint),
            ":::",
            "",
        ])

    if page.imports_code:
        parts.extend(["## Importy", ""])
        for code in page.imports_code:
            parts.extend([fence(code), ""])

    if page.skeleton_code:
        parts.extend(["## Szkielet z notebooka", "", fence(page.skeleton_code), ""])

    if page.debug_code:
        parts.extend(["## Mini-debug", ""])
        for code in page.debug_code:
            parts.extend([fence(code), ""])

    if page.test_names or page.check_code:
        parts.extend(["## Co sprawdza judge", ""])
        if page.test_names:
            parts.extend([f"- {name}" for name in page.test_names])
            parts.append("")
        if page.check_code:
            parts.extend([fence(page.check_code), ""])

    if page.solution_code:
        parts.extend([
            "<details class=\"solution-details\">",
            "<summary>Pokaż rozwiązanie referencyjne</summary>",
            "",
        ])
        for code in page.solution_code:
            parts.extend([fence(code), ""])
        parts.extend(["</details>", ""])

    nav_items: list[str] = []
    if previous:
        nav_items.append(f"[← Poprzednie](./{previous.page_filename})")
    nav_items.append("[Indeks](../../materials/index.qmd)")
    if next_page:
        nav_items.append(f"[Następne →](./{next_page.page_filename})")
    parts.extend(["::: {.lesson-nav}", " | ".join(nav_items), ":::", ""])

    return "\n".join(parts)


def category_for(page: NotebookPage) -> str:
    for category, numbers in CATEGORIES:
        if page.number in numbers:
            return category
    return "Pozostale"


def index_markdown(pages: list[NotebookPage]) -> str:
    by_number = {page.number: page for page in pages}
    parts: list[str] = [
        "---",
        'title: "PyTorch w notebookach"',
        'description: "HTMLowe wersje notebooków Jupyter przygotowane do czytania na telefonie."',
        "---",
        "",
        "Ta sekcja jest zbudowana z notebooków Jupyter, ale czyta się ją jak zwykłe strony HTML z poprzednich zajęć: bez Colaba, bez uruchamiania kodu podczas budowania strony i z rozwiązaniami schowanymi do samokontroli.",
        "",
        "::: {.callout-note}",
        "## Tryb czytania",
        "Każda strona ma krótki cel, treść zadania, kroki pracy, kod do debugowania, listę testów i rozwiązanie referencyjne. Na telefonie najpierw czytaj opis i kroki, a kod traktuj jak mapę tego, co później wpiszesz w Jupyterze.",
        ":::",
        "",
    ]

    for category, numbers in CATEGORIES:
        category_pages = [by_number[number] for number in numbers if number in by_number]
        if not category_pages:
            continue
        parts.extend([f"## {category}", "", "::: {.notebook-list}", ""])
        for page in category_pages:
            css_class = difficulty_class(page.difficulty)
            parts.extend([
                f"::: {{.notebook-item .{css_class}}}",
                f"### [{page.number:02d}. {page.title}](notebooks/{page.page_filename})",
                "",
                f"`{page.difficulty}` · `{page.function_name or page.task_id}`",
                "",
                f"<p>{plain_text(page.hint) if page.hint else 'Zobacz treść zadania, szkielet i rozwiązanie referencyjne.'}</p>",
                ":::",
                "",
            ])
        parts.extend([":::", ""])

    return "\n".join(parts)


def materials_index_markdown(pages: list[NotebookPage]) -> str:
    by_number = {page.number: page for page in pages}
    parts: list[str] = [
        "---",
        'title: "Indeks materiałów"',
        'description: "Wspólny indeks klasycznych laboratoriów i notebooków PyTorch."',
        "toc: false",
        "---",
        "",
        "To jest jedna mapa kursu: najpierw krótkie laboratoria z poprzednich zajęć, potem notebooki PyTorch przerobione na strony HTML do czytania na telefonie. Notebooki są pokazane jako zwykłe strony HTML: bez Colaba, bez wykonywania kodu podczas budowania strony i z rozwiązaniami schowanymi do samokontroli.",
        "",
        "::: {.callout-note}",
        "## Tryb czytania",
        "Karty prowadzą bezpośrednio do materiałów. Klasyczne laboratoria mają krótką intuicję, kod i zadania, a notebooki PyTorch pokazują treść zadania, kroki, testy judge i ukryte rozwiązania referencyjne.",
        ":::",
        "",
    ]

    for category, labs in LAB_CATEGORIES:
        parts.extend([f"## {category}", "", "::: {.notebook-list}", ""])
        for lab in labs:
            parts.extend([
                "::: {.notebook-item .lab}",
                f"### [{lab['title']}]({lab['href']})",
                "",
                lab["tools"],
                "",
                f"<p>{plain_text(lab['summary'])}</p>",
                ":::",
                "",
            ])
        parts.extend([":::", ""])

    for category, numbers in CATEGORIES:
        category_pages = [by_number[number] for number in numbers if number in by_number]
        if not category_pages:
            continue
        parts.extend([f"## {category}", "", "::: {.notebook-list}", ""])
        for page in category_pages:
            css_class = difficulty_class(page.difficulty)
            parts.extend([
                f"::: {{.notebook-item .{css_class}}}",
                f"### [{page.number:02d}. {page.title}](../pytorch/notebooks/{page.page_filename})",
                "",
                f"`{page.difficulty}` · `{page.function_name or page.task_id}`",
                "",
                f"<p>{plain_text(page.hint) if page.hint else 'Zobacz treść zadania, szkielet i rozwiązanie referencyjne.'}</p>",
                ":::",
                "",
            ])
        parts.extend([":::", ""])

    return "\n".join(parts)


def render_pages() -> list[NotebookPage]:
    tasks = load_tasks()
    pages = [
        make_page(path, tasks)
        for path in sorted(TEMPLATES_DIR.glob("[0-9][0-9]_*.ipynb"))
        if path.name != "00_welcome.ipynb"
    ]
    pages.sort(key=lambda page: page.number)

    if PAGES_DIR.exists():
        shutil.rmtree(PAGES_DIR)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    for index, page in enumerate(pages):
        previous = pages[index - 1] if index > 0 else None
        next_page = pages[index + 1] if index < len(pages) - 1 else None
        (PAGES_DIR / page.page_filename).write_text(
            page_markdown(page, previous, next_page),
            encoding="utf-8",
        )

    MATERIALS_DIR.mkdir(exist_ok=True)
    (MATERIALS_DIR / "index.qmd").write_text(materials_index_markdown(pages), encoding="utf-8")
    return pages


def main() -> None:
    updated = clean_all_notebooks()
    pages = render_pages()
    print(f"Cleaned notebooks: {updated}")
    print(f"Generated pages: {len(pages)}")


if __name__ == "__main__":
    main()
