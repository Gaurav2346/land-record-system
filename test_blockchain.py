"""Quick connectivity check (requires Ganache on :8545)."""

import json

from blockchain import BlockchainError, chain_status


def main() -> None:
    status = chain_status()
    print(json.dumps(status, indent=2, default=str))
    if not status.get("connected"):
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except BlockchainError as err:
        raise SystemExit(f"Error: {err}") from err
