import json
from matplotlib.figure import Figure

def save_png(figure: Figure, path: str):
    figure.savefig(path, dpi=300, bbox_inches="tight")

def save_svg(figure: Figure, path: str):
    figure.savefig(path, format="svg", bbox_inches="tight")

def save_scheme(scheme_data: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scheme_data, f, ensure_ascii=False, indent=4)

def load_scheme(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


