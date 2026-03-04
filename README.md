# Origraph Platform

Canonical project docs now live under [`docs/`](./docs).

- Overview: [`docs/README.md`](./docs/README.md)
- Demo runbook: [`docs/DEMO_RUNBOOK.md`](./docs/DEMO_RUNBOOK.md)
- Project mapping: [`PROJECT_MAP.md`](./PROJECT_MAP.md)

## Quick Start

```bash
./scripts/bootstrap_demo.sh
DEMO_MODE=fixture ./scripts/run_demo.sh
```

Open:

- `http://127.0.0.1:5050/` (landing)
- `http://127.0.0.1:5050/registry/demo/live` (guided demo)

## Licensing

This repository currently uses a split-license model during the transition to multi-repo:

- Root project files (`/`, `docs/`, `scripts/`): Apache-2.0 ([LICENSE](./LICENSE))
- `invisible-text-watermark/`: Apache-2.0 ([invisible-text-watermark/LICENSE](./invisible-text-watermark/LICENSE))
- `extension/`: Apache-2.0 ([extension/LICENSE](./extension/LICENSE))
- `origraph-registry-demo/`: AGPL-3.0 ([origraph-registry-demo/LICENSE](./origraph-registry-demo/LICENSE))
- `origraph-landing-vercel/`: Apache-2.0 ([origraph-landing-vercel/LICENSE](./origraph-landing-vercel/LICENSE))

## Branch Checkpoint

On March 3, 2026, remote `main` was checkpointed to `hacktheeast_ckpt` before pushing the current local project state to `main`.
