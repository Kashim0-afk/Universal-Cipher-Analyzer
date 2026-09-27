"""Allow ``python -m cipher_analyzer``."""

import sys

from .cli import main

sys.exit(main())
