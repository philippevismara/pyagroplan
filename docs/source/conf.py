# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pyagroplan"
copyright = "2024, Titouan Lorieul"
author = "Titouan Lorieul"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.napoleon",
    "sphinx_rtd_theme",
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


# -- Options for autodoc -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

import sys
from pathlib import Path
sys.path.insert(0, str(Path("..", "..").resolve()))

autodoc_typehints = "description"


# -- Options for coverage -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/coverage.html

coverage_modules = ["src"]


# -- Options for napoleon -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_preprocess_types = True
napoleon_include_init_with_doc = True
napoleon_use_ivar = True
