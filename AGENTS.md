# pd-compose

Compose-like tool for proot-distro on Termux.

## Git Workflow

- Always create a new branch from `main` before making changes.
- Never modify, commit, or push directly to `main`.
- Submit changes via a Pull Request.
- After pushing, check CI workflow results using GitHub Actions with http curl or MCP tools.
- If any check fails, retrieve the logs with and fix the issue before merging.
- Use conventional one-liner commit messages (e.g. `feat:`, `fix:`, `ci:`, `chore:`).

## CI

The CI workflow runs on pull requests. It tests Python 3.13 and 3.14 using `actions/checkout@v6`, `actions/setup-python@v6`, and the standard ubuntu runner. Rich formatting is disabled via `TYPER_USE_RICH=0`.

## Docker Development Environment

### Requirements

- Docker
- Docker Compose

### Build and start

```bash
docker compose build app
docker compose up -d app
```

### Run tests

```bash
docker compose exec app pip install -e ".[dev]"
docker compose exec app python -m pytest -v
```

### Run pd-compose commands

```bash
docker compose exec app pd-compose --help
docker compose exec app pd-compose up --dry-run
```

### Usage with `docker run`

```bash
docker run --rm pd-compose:latest ps
docker run --rm pd-compose:latest up --help
```

### Stop the container

```bash
docker compose down
```
