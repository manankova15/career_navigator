# Contributing

## Workflow

- Create feature branches from `main`.
- Keep API and event changes documented in `docs/`.
- Do not commit secrets or generated data.
- Add tests for domain logic when implementing features.

## Local setup

```bash
# Install Python dev tools
pip install -e .

# Start infrastructure (requires Podman 4.1+)
make infra-up

# Or start everything at once
make dev-up
```

## Container tooling

The project uses **Podman** (rootless, daemonless). Make sure:

1. `podman` is installed and the machine is running (macOS):
   ```bash
   podman machine start
   ```
2. `podman-compose` is available:
   ```bash
   pip install podman-compose
   # or use the built-in: podman compose (Podman 4.1+)
   ```

## Branching

| Branch prefix | Purpose |
|---|---|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `chore/` | Tooling, config, CI |
| `docs/` | Documentation only |

## Secrets

Never commit `.env` or any file containing credentials.
Use `.env.example` as the template — it must never contain real values.
