from __future__ import annotations

import os
import sys
from pathlib import Path

DOCS_SOURCE_DIR = Path(__file__).resolve().parent
REPO_ROOT = DOCS_SOURCE_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT))

project = "UR Dashboard"
copyright = "2026, HesuWork"
author = "HesuWork"
release = "1.0.0"
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Overridden per language build from docs/build_multilang.py
language = os.environ.get("DOC_LANGUAGE", "en")

autodoc_member_order = "bysource"
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

html_theme = "sphinx_rtd_theme"
html_static_path: list[str] = []

html_context = {
    "available_languages": [
        ("en", "English"),
        ("ko", "한국어"),
    ]
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
