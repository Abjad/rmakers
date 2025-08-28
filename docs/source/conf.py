import os
import sys

import rmakers

sys.path.insert(0, os.path.abspath("../../source"))

autodoc_member_order = "groupwise"

copyright = "2008-2025, Trevor Bača."

extensions = [
    "abjad.ext.sphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.graphviz",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_toggleprompt",
    "uqbar.sphinx.api",
    "uqbar.sphinx.book",
    "uqbar.sphinx.inheritance",
    "uqbar.sphinx.style",
]

graphviz_dot_args = ["-s32"]
graphviz_output_format = "svg"

html_last_updated_fmt = "%b %d, %Y"
html_show_sphinx = False
html_static_path = ["_static"]
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "canonical_url": "https://abjad.github.io/rmakers",
    "navigation_depth": 1,
    "sticky_navigation": False,
    "style_external_links": True,
    "style_nav_header_background": "#55EE77",
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("http://www.sphinx-doc.org/en/master/", None),
}

project = "rmakers"
pygments_style = "sphinx"

smartquotes = True

templates_path = ["_templates"]
todo_include_todos = True

uqbar_api_member_documenter_classes = [
    "uqbar.apis.FunctionDocumenter",
    "uqbar.apis.SummarizingClassDocumenter",
]
uqbar_api_module_documenter_class = "uqbar.apis.SummarizingModuleDocumenter"
uqbar_api_root_documenter_class = "uqbar.apis.SummarizingRootDocumenter"
uqbar_api_source_paths = ["rmakers"]
uqbar_api_title = "rmakers API"
uqbar_book_console_setup = [
    "import abjad",
    "import rmakers",
    "from fractions import Fraction",
]
uqbar_book_console_teardown = []
uqbar_book_extensions = [
    "uqbar.book.extensions.GraphExtension",
    "abjad.ext.sphinx.LilyPondExtension",
]
uqbar_book_strict = False
uqbar_book_use_black = True
uqbar_book_use_cache = True

version = rmakers.__version__
