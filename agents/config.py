import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

WORKDIR = Path(os.getenv("WORKDIR", ".")).resolve()
SKILLDIR = Path(os.getenv("SKILLDIR", ".")).resolve()
MODEL = os.getenv("MODEL", "glm-4.7")
TASKSDIR = WORKDIR / ".tasks"
