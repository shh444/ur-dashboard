import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# -- Project --
project = "UR Dashboard"
copyright = "2026, HesuWork"
author = "HesuWork"
release = "1.0.0"

# -- Extensions --
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]

# -- Options --
autodoc_member_order = "bysource"
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- HTML --
html_theme = "sphinx_rtd_theme"
html_static_path = []

# -- Intersphinx --
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
