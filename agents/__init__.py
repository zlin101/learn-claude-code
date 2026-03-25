import sys
from pathlib import Path

# Add agents directory to sys.path for consistent imports
_agents_dir = Path(__file__).parent.resolve()
if str(_agents_dir) not in sys.path:
    sys.path.insert(0, str(_agents_dir))

__all__ = ["agent"]
