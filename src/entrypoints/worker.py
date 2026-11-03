"""Managed worker entrypoint: discovers workflows and runs the worker."""

import asyncio
import sys
from pathlib import Path

# Make the project root importable regardless of CWD.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


async def main() -> None:
    import mistralai_workflows

    try:
        from mistralai_workflows.discovery import discover_workflows
    except ImportError:  # fallback for alternate SDK layouts
        from mistralai_workflows import discover_workflows

    discovered = discover_workflows()
    await mistralai_workflows.run_worker(discovered)


if __name__ == "__main__":
    asyncio.run(main())
