# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jangle.boot_django import boot_django

boot_django()

from datetime import datetime

from sphinx.application import Sphinx

from jangle import __about__

project = "jangle"
year = datetime.now().year
copyright = f"{year} {__about__.__author__}"
author = __about__.__author__
release = __about__.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
]
primary_domain = "py"

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_theme_options = {
    "description": "IETF BCP 47 / RFC 5646 language tags in Django",
    "github_user": "egginabucket",
    "github_repo": "jangle",
}

html_static_path = ["_static"]

html_css_files = [
    "style/custom.css",
]

autodoc_member_order = "bysource"


def setup(app: Sphinx) -> None:
    app.add_css_file("style/custom.css")
