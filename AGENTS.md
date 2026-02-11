# AGENTS.md

## Project Overview

Torappu is an asset unpacker for Arknights focused on resource extraction and analysis. It provides a CLI for downloading asset bundles, diffing versions, and running task-based processors that emit structured output under `storage/`.

## Architecture

- **CLI Interface** (`torappu/__main__.py`): Click-based CLI entry point that runs the async pipeline via `anyio`.
- **Core Orchestrator** (`torappu/core/__init__.py`): Loads task modules, groups by priority, and runs them concurrently per priority.
- **Client** (`torappu/core/client.py`): Handles remote asset fetching, caching, manifest diffing, and path resolution.
- **Task System** (`torappu/core/tasks/`): Individual task modules implement extraction for specific asset types.

## Key Directories

- `torappu/core/tasks/` - Task implementations (each module exposes a `Task` class)
- `torappu/core/utils/` - Shared helpers for Unity asset parsing and IO
- `OpenArknightsFBS/` - FlatBuffer schema definitions
- `assets/` - Static assets used by tasks
- `bin/` - Bundled tools like `flatc` (platform-specific)
- `storage/` - Local cache and extracted outputs (`assetbundle/`, `asset/`, `assets_storage/`, etc.)
- `scripts/` - Utility scripts for data processing

## Development Commands

### Setup

```bash
uv sync
```

### CLI Usage

```bash
# Basic extraction
python -m torappu [CLIENT_VERSION] [RES_VERSION]

# With version comparison
python -m torappu [CLIENT_VERSION] [RES_VERSION] -c [PREV_CLIENT_VERSION] -r [PREV_RES_VERSION]

# Include/exclude specific tasks (by Task.name)
python -m torappu [CLIENT_VERSION] [RES_VERSION] -i task1,task2
python -m torappu [CLIENT_VERSION] [RES_VERSION] -e task1,task2
```

### Docker Usage

```bash
# Build and run
docker build -t torappu .
docker run torappu [CLIENT_VERSION] [RES_VERSION]
```

### Quality Assurance

```bash
uv run ruff check .
uv run ruff format .
pyright
```

## Configuration

Settings are loaded via Pydantic and `.env` (see `torappu/config.py`). Common environment variables:

- `ENVIRONMENT`: `production` or `debug`
- `LOG_LEVEL`: numeric or string log level (default `INFO`)
- `TOKEN`: auth token for backend uploads
- `TIMEOUT`: network timeout seconds (default `10`)
- `BACKEND_ENDPOINT`: backend API base URL
- `FLATC_PATH`: override bundled `flatc` path
- `SENTRY_DSN`: Sentry DSN for error reporting

## Task System Architecture

- Base class: `torappu/core/tasks/base.py` (`BaseTask`)
- Tasks are auto-discovered from `torappu.core.tasks.*` modules
- Each module should export a `Task` class with `priority` and `name`
- Tasks run in ascending priority order; tasks with the same priority run concurrently
- `Task.name` is used for `-i/--include` and `-e/--exclude` CLI filters

### Adding New Tasks

```python
from typing import ClassVar

from torappu.core.tasks.base import BaseTask
from torappu.models import Diff


class Task(BaseTask):
    priority: ClassVar[int] = 5
    name = "MyNewTask"

    def check(self, diff_list: list[Diff]) -> bool:
        return any(d.path.startswith("my/prefix") for d in diff_list)

    async def start(self):
        ...
```

## Asset Pipeline

1. **Remote Fetching**: Client downloads asset bundles from the CDN
2. **Local Caching**: Bundles cached under `storage/assetbundle/`
3. **UnityPy Processing**: Unity assets parsed for extraction
4. **Task Processing**: Tasks run based on version diffs and filters
5. **Output Generation**: Results written to structured paths under `storage/`

## Key Dependencies

- **UnityPy**: Unity asset extraction
- **httpx**: HTTP client for remote asset fetching
- **Pydantic Settings**: Configuration management
- **Loguru**: Structured logging
- **lz4inv**: LZ4 decompression for asset bundles
- **pycryptodome**: Cryptographic operations
- **tenacity**: Retry logic for network operations
- **click** / **anyio**: CLI and async runtime
