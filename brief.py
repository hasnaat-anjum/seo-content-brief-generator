#!/usr/bin/env python3
"""Entry point: python brief.py new "keyword" --file page.html --save

See seo_brief/cli.py for the full command list. Standard library only —
no packages to install.
"""

import sys

from seo_brief.cli import main

if __name__ == "__main__":
    sys.exit(main())
