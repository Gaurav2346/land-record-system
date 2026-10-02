#!/usr/bin/env python3
"""Deploy LandRegistry to Ganache and save the contract address."""

import argparse
import json

import config
from blockchain import BlockchainError, chain_status, deploy_contract


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy LandRegistry.sol to Ganache")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove saved address and deploy a new contract (required after recompiling).",
    )
    args = parser.parse_args()

    if args.force and config.CONTRACT_ADDRESS_FILE.exists():
        config.CONTRACT_ADDRESS_FILE.unlink()

    print("=" * 50)
    print("Land Registry — Contract Deployment")
    print("=" * 50)
    status = chain_status()
    print(json.dumps(status, indent=2, default=str))

    if not status.get("connected"):
        raise SystemExit(status.get("error", "Blockchain not connected"))

    if status.get("contract_deployed") and not args.force:
        print()
        print("Contract already deployed. Use --force after recompiling the contract.")
        raise SystemExit(0)

    contract, receipt = deploy_contract()
    print()
    print("Deployment successful.")
    print("Contract address:", contract.address)
    print("Transaction hash:", receipt.transactionHash.hex())
    print("Block number:", receipt.blockNumber)


if __name__ == "__main__":
    try:
        main()
    except BlockchainError as err:
        raise SystemExit(f"Error: {err}") from err
