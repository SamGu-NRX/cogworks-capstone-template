"""Put learning-labs/ on sys.path so `import labs...` works from a
repo-root pytest run. The labs are not a package to install; this is the
whole trick. See INTERFACE.md for the commands this supports.
"""

import sys
from pathlib import Path

LABS_ROOT = Path(__file__).resolve().parents[1]
if str(LABS_ROOT) not in sys.path:
    sys.path.insert(0, str(LABS_ROOT))
