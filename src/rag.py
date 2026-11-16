"""Recuperación léxica local; sin generación ni servicios externos."""
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1] / "data" / "knowledge"
STOP = set("a al de del el la las los un una que cual es son en por para me mi se y o como cuanto cuesta".split())


def tokens(text):
    text = "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")
    return set(re.findall(r"[a-z0-9]+", text)) - STOP


def retrieve(query):
    words = tokens(query)
    scored = []
    for path in sorted(ROOT.glob("*.md")):
        if path.name == "README.md":
            continue
        content = path.read_text(encoding="utf-8")
        # Cada documento declara sus temas; no se selecciona por vocabulario incidental.
        title = content.splitlines()[0]
        score = len(words & tokens(title))
        if score:
            scored.append((score, path.name, content))
    if not scored:
        return "No encuentro esa información en la documentación. ¿Puedes concretar la consulta?"
    scored.sort(key=lambda row: (-row[0], row[1]))
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return "La consulta abarca varios temas. ¿Puedes preguntar por uno solo?"
    _, name, content = scored[0]
    return content.split("\n", 1)[1].strip() + f" [Fuente: {name}]"
