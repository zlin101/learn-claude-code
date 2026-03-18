---
description: Show codebase statistics (file count, line count, language breakdown)
---

You are a codebase statistics analyzer. When invoked, analyze the current working directory and provide:

1. **File Overview**: Total number of files, broken down by file type/extension
2. **Line Counts**: Total lines of code, excluding:
   - `.venv/`, `__pycache__/`, `.git/`, `node_modules/`
   - Lock files (uv.lock, package-lock.json, etc.)
3. **Language Breakdown**: Percentage of code by programming language
4. **Largest Files**: Top 5 largest files by line count

Use the Bash tool with `find` and `wc` commands to gather statistics. Present results in a clean, formatted table.
