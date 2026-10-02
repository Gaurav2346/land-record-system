"""Web3.py integration with LandRegistry on Ganache."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from eth_typing import ChecksumAddress
from web3 import Web3
from web3.contract import Contract
from web3.types import TxReceipt

import config

_w3: Optional[Web3] = None
_contract: Optional[Contract] = None


class BlockchainError(Exception):
    """Raised when blockchain operations fail."""


def get_web3() -> Web3:
    global _w3
    if _w3 is None:
        _w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
    if not _w3.is_connected():
        raise BlockchainError(
            "Cannot connect to Ganache. Start Ganache on "
            f"{config.RPC_URL} and try again."
        )
    return _w3


def _load_abi() -> list:
    if not config.BUILD_ABI.exists():
        raise BlockchainError(
            "Missing build/LandRegistry.abi. Run: python compile_contract.py"
        )
    return json.loads(config.BUILD_ABI.read_text())


def _load_bytecode() -> str:
    if not config.BUILD_BIN.exists():
        raise BlockchainError(
            "Missing build/LandRegistry.bin. Run: python compile_contract.py"
        )
    return config.BUILD_BIN.read_text().strip()


def save_contract_address(address: str) -> None:
    config.CONTRACT_ADDRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.CONTRACT_ADDRESS_FILE.write_text(
        Web3.to_checksum_address(address)
    )


def load_contract_address() -> Optional[str]:
    if not config.CONTRACT_ADDRESS_FILE.exists():
        return None
    raw = config.CONTRACT_ADDRESS_FILE.read_text().strip()
    return raw if raw else None


def get_default_account() -> ChecksumAddress:
    w3 = get_web3()
    accounts = w3.eth.accounts
    if not accounts:
        raise BlockchainError("No unlocked accounts found on Ganache.")
    idx = config.DEFAULT_ACCOUNT_INDEX
    if idx >= len(accounts):
        raise BlockchainError(
            f"Account index {idx} not available. Ganache has {len(accounts)} accounts."
        )
    return accounts[idx]


def account_for_wallet(wallet: str) -> ChecksumAddress:
    """Pick Ganache unlocked account matching owner wallet (demo helper)."""
    w3 = get_web3()
    target = Web3.to_checksum_address(wallet).lower()
    for acc in w3.eth.accounts:
        if acc.lower() == target:
            return acc
    raise BlockchainError(
        "Owner wallet is not an unlocked Ganache account. "
        "Use a Ganache address for transfers in this demo."
    )


def get_contract(*, require_deployed: bool = True) -> Contract:
    global _contract
    w3 = get_web3()
    abi = _load_abi()

    address = load_contract_address()
    if address:
        if _contract is None:
            _contract = w3.eth.contract(
                address=Web3.to_checksum_address(address),
                abi=abi,
            )
        return _contract

    if require_deployed:
        raise BlockchainError(
            "Smart contract not deployed. Run: python deploy_contract.py"
        )

    return w3.eth.contract(abi=abi, bytecode=_load_bytecode())


def chain_status() -> Dict[str, Any]:
    try:
        w3 = get_web3()
        account = get_default_account()
        balance = w3.from_wei(w3.eth.get_balance(account), "ether")
        deployed = load_contract_address() is not None
        count = None
        if deployed:
            count = get_contract().functions.propertyCount().call()
        return {
            "connected": True,
            "rpc_url": config.RPC_URL,
            "chain_id": w3.eth.chain_id,
            "default_account": account,
            "balance_eth": float(balance),
            "contract_address": load_contract_address(),
            "contract_deployed": deployed,
            "property_count": count,
            "accounts": [Web3.to_checksum_address(a) for a in w3.eth.accounts[:10]] if w3.eth.accounts else [],
        }
    except BlockchainError as exc:
        return {
            "connected": False,
            "rpc_url": config.RPC_URL,
            "error": str(exc),
            "contract_address": load_contract_address(),
            "contract_deployed": load_contract_address() is not None,
        }


def deploy_contract() -> Tuple[Contract, TxReceipt]:
    global _contract
    _contract = None
    w3 = get_web3()
    account = get_default_account()
    factory = get_contract(require_deployed=False)

    nonce = w3.eth.get_transaction_count(account)
    tx = factory.constructor().build_transaction(
        {
            "from": account,
            "nonce": nonce,
            "gas": 4_000_000,
            "gasPrice": w3.to_wei("2", "gwei"),
        }
    )
    tx_hash = w3.eth.send_transaction(tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status != 1 or not receipt.contractAddress:
        raise BlockchainError("Contract deployment failed.")

    address = Web3.to_checksum_address(receipt.contractAddress)
    save_contract_address(address)
    _contract = w3.eth.contract(address=address, abi=_load_abi())
    return _contract, receipt


def _send_contract_tx(function, from_account: ChecksumAddress) -> TxReceipt:
    w3 = get_web3()
    nonce = w3.eth.get_transaction_count(from_account)
    try:
        estimated = function.estimate_gas({"from": from_account})
    except Exception as exc:
        raise BlockchainError(f"Transaction simulation failed: {exc}") from exc

    tx = function.build_transaction(
        {
            "from": from_account,
            "nonce": nonce,
            "gas": estimated + 100_000,
            "gasPrice": w3.to_wei("2", "gwei"),
        }
    )
    tx_hash = w3.eth.send_transaction(tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise BlockchainError("Transaction reverted on chain.")
    return receipt


def document_hash_to_bytes32(hex_hash: Optional[str]) -> bytes:
    if not hex_hash:
        return b"\x00" * 32
    cleaned = hex_hash.strip().lower()
    if cleaned.startswith("0x"):
        cleaned = cleaned[2:]
    if len(cleaned) != 64:
        raise BlockchainError(
            "Document hash must be 64 hex characters (SHA-256)."
        )
    return bytes.fromhex(cleaned)


def register_property_on_chain(
    *,
    property_number: str,
    survey_number: str,
    owner_name: str,
    location: str,
    area: int,
    property_type: str,
    document_hash: Optional[str] = None,
    from_account: Optional[ChecksumAddress] = None,
) -> Tuple[int, TxReceipt, Dict[str, Any]]:
    contract = get_contract()
    sender = from_account or get_default_account()
    doc_bytes = document_hash_to_bytes32(document_hash)

    fn = contract.functions.registerProperty(
        property_number,
        survey_number,
        owner_name,
        location,
        int(area),
        property_type,
        doc_bytes,
    )
    receipt = _send_contract_tx(fn, sender)
    property_id = contract.functions.propertyCount().call()
    on_chain = fetch_property_from_chain(property_id)
    return property_id, receipt, on_chain


def transfer_ownership_on_chain(
    *,
    property_id: int,
    new_owner_wallet: str,
    new_owner_name: str,
    current_owner_wallet: Optional[str] = None,
    from_account: Optional[ChecksumAddress] = None,
) -> TxReceipt:
    contract = get_contract()
    if from_account is None:
        if current_owner_wallet:
            sender = account_for_wallet(current_owner_wallet)
        else:
            on_chain = fetch_property_from_chain(property_id)
            sender = account_for_wallet(on_chain["owner_wallet"])
    else:
        sender = from_account
    new_owner = Web3.to_checksum_address(new_owner_wallet)

    fn = contract.functions.transferOwnership(
        int(property_id),
        new_owner,
        new_owner_name,
    )
    return _send_contract_tx(fn, sender)


def fetch_property_from_chain(property_id: int) -> Dict[str, Any]:
    contract = get_contract()
    if not contract.functions.propertyExists(int(property_id)).call():
        raise BlockchainError(f"Property ID {property_id} does not exist on chain.")

    data = contract.functions.getProperty(int(property_id)).call()
    doc_bytes = data[8]
    doc_hex = (
        "0x" + doc_bytes.hex()
        if doc_bytes != b"\x00" * 32
        else None
    )

    return {
        "id": data[0],
        "property_number": data[1],
        "survey_number": data[2],
        "owner_name": data[3],
        "location": data[4],
        "area": data[5],
        "property_type": data[6],
        "owner_wallet": data[7],
        "document_hash": doc_hex,
        "verified_on_blockchain": True,
    }


def verify_property_on_chain(property_id: int) -> Dict[str, Any]:
    """Read live state from the blockchain (source of truth)."""
    return fetch_property_from_chain(property_id)


if __name__ == "__main__":
    print("Chain status:", json.dumps(chain_status(), indent=2, default=str))
