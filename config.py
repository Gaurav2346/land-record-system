"""Application configuration (Ganache / contract address)."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

RPC_URL = os.getenv("GANACHE_RPC_URL", "http://127.0.0.1:8545")
CONTRACT_ADDRESS_FILE = BASE_DIR / "config" / "contract_address.txt"
BUILD_ABI = BASE_DIR / "build" / "LandRegistry.abi"
BUILD_BIN = BASE_DIR / "build" / "LandRegistry.bin"

# Ganache default unlocked account index for demo transactions
DEFAULT_ACCOUNT_INDEX = int(os.getenv("GANACHE_ACCOUNT_INDEX", "0"))
