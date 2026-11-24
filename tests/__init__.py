"""Run the test suite:  python -m unittest discover -s tests -v"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seo_brief.parse import parse_file  # noqa: E402


def load_example_pages():
    """Parse the three example competitor pages in examples/competitors/."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(here, "examples", "competitors")
    names = [
        "budget-espresso-guide.html",
        "cheap-espresso-list.html",
        "budget-espresso-buying-guide.html",
    ]
    return [parse_file(os.path.join(folder, name)) for name in names]


def example_files():
    """Paths of the three example competitor pages."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    folder = os.path.join(here, "examples", "competitors")
    return [os.path.join(folder, name) for name in (
        "budget-espresso-guide.html",
        "cheap-espresso-list.html",
        "budget-espresso-buying-guide.html",
    )]
