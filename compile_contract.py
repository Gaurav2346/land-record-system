#!/usr/bin/env python3
"""Compile LandRegistry.sol using the solc CLI."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOL_FILE = ROOT / "contracts" / "LandRegistry.sol"
BUILD_DIR = ROOT / "build"


def main() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        "solc",
        "--optimize",
        "--optimize-runs",
        "200",
        "--evm-version",
        "paris",
        "--combined-json",
        "abi,bin",
        str(SOL_FILE),
    ]
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("solc not found. Install Solidity: https://docs.soliditylang.org/")
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or exc.stdout)
        sys.exit(exc.returncode)

    payload = json.loads(result.stdout)
    contracts = payload.get("contracts", {})
    contract_data = None
    for key, value in contracts.items():
        if key.endswith(":LandRegistry"):
            contract_data = value
            break
    if not contract_data:
        print("LandRegistry artifact not found in solc output.")
        sys.exit(1)

    abi_path = BUILD_DIR / "LandRegistry.abi"
    bin_path = BUILD_DIR / "LandRegistry.bin"
    abi = contract_data["abi"]
    if not isinstance(abi, str):
        abi = json.dumps(abi)
    abi_path.write_text(abi)
    bin_path.write_text(contract_data["bin"])

    print("Compiled successfully:")
    print(" ", abi_path)
    print(" ", bin_path)


if __name__ == "__main__":
    main()
