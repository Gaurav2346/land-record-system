# Blockchain-Based Land & Property Record Management System

A college mini-project that registers land and property details on a **local Ethereum blockchain**, verifies records from the chain, transfers ownership between wallet addresses, and keeps application data (including transfer history) in **SQLite**. The web dashboard is built with **Flask**, **Bootstrap**, and plain **JavaScript**.

---

## Problem statement

Traditional land records can be altered, hard to audit, or depend on a single authority. This project demonstrates how **immutable on-chain storage** plus a simple web app can:

- Register property details with a **transparent transaction hash**
- **Verify** ownership and metadata directly from the blockchain
- **Transfer** ownership with an auditable history
- Optionally link **document fingerprints** (SHA-256) to a property

This is a **local demo** (Ganache), not a production land registry.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│  Browser (HTML + CSS + Bootstrap + JavaScript)              │
│  Dashboard: Register · Verify · Transfer · Hash · List    │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP (REST API)
┌───────────────────────────▼─────────────────────────────────┐
│  Flask (app.py)                                             │
│  Validation · JSON API · Templates                          │
└───────┬─────────────────────────────┬───────────────────────┘
        │                             │
        ▼                             ▼
┌───────────────┐             ┌───────────────────┐
│  SQLite       │             │  Web3.py          │
│  database.py  │             │  blockchain.py    │
│  Properties   │             │  RPC → Ganache    │
│  Transfers    │             │  Smart contract   │
└───────────────┘             └─────────┬─────────┘
                                        │
                                        ▼
                              ┌───────────────────┐
                              │  LandRegistry.sol │
                              │  (Solidity)       │
                              └─────────┬─────────┘
                                        │
                                        ▼
                              ┌───────────────────┐
                              │  Ganache          │
                              │  Local blockchain │
                              └───────────────────┘
```

**Design choice:** Critical ownership and property fields live **on-chain** (source of truth). SQLite stores **convenience data** for the UI: registration tx hash, pagination-friendly lists, and **transfer history** rows synced after each transfer. Verification always reads **live chain state**.

---

## Technology stack — what we used and why

| Technology | Role in this project | Why we used it |
|------------|----------------------|----------------|
| **Python 3** | Backend language | Easy to learn, strong ecosystem, good for academic projects and Web3 libraries. |
| **Flask** | Web server and REST API | Lightweight, minimal setup, ideal for a small dashboard without heavy frameworks. |
| **Web3.py** | Talk to Ethereum/Ganache | Standard Python library to deploy contracts, send transactions, and read contract state. |
| **Solidity** | Smart contract (`LandRegistry.sol`) | Industry language for Ethereum; defines register, read, and transfer rules on-chain. |
| **Ganache** | Local blockchain | Free, offline, fast blocks, pre-funded accounts — perfect for demos and viva without testnet fees. |
| **SQLite** | `data/land_records.db` | Zero-config database for lists, tx metadata, and transfer history; no separate DB server. |
| **HTML / CSS / Bootstrap 5** | UI | Professional look quickly; responsive layout for presentation. |
| **JavaScript (fetch)** | Frontend API calls | Simple async calls to Flask without a heavy SPA framework. |
| **SHA-256** (`utils.py`) | Document fingerprint | Proves a deed/file was not changed without storing large files on-chain (only a hash). |
| **solc** | Compile contract | Produces ABI/bytecode in `build/` for deployment via Web3.py. |
| **python-dotenv** | Optional `.env` | Configure RPC URL and default Ganache account index without hard-coding. |

---

## How the project works

### 1. Register property

1. User fills the form (property number, survey number, owner, location, area, type, optional document hash).
2. Flask validates input (`utils.py`).
3. `blockchain.py` builds a transaction to `registerProperty(...)` on `LandRegistry`.
4. Ganache mines the transaction; Web3 returns **transaction hash** and **block number**.
5. Flask saves a row in SQLite (including tx hash) for fast listing in the dashboard.

On-chain, the **owner wallet** is set to the Ganache account that signed the transaction (`msg.sender`).

### 2. Verify property

1. User enters a **property ID** (on-chain ID from `propertyCount`).
2. Flask calls `getProperty(id)` — a **view** function (no new transaction).
3. Response shows blockchain fields and compares them to SQLite when a local row exists (`records_match`).

Verification proves the record exists on the ledger at that moment.

### 3. Transfer ownership

1. User provides property ID, **new owner wallet** (Ganache address), and new owner name.
2. The contract requires `msg.sender` to be the **current owner wallet**; the app picks the matching unlocked Ganache account.
3. On success, chain updates `ownerWallet` and `ownerName`; SQLite updates the owner and appends a **transfer_history** row.

### 4. Document hash (optional)

1. User uploads a file or pastes text; API returns **SHA-256**.
2. Hash can be sent at registration; stored on-chain as `bytes32` (zero if omitted).
3. Anyone can compare a recomputed hash with the on-chain value to detect document tampering.

### 5. Demo data (two options)

| Script | What it does |
|--------|----------------|
| `seed_database.py` | **SQLite only** — 10 fixed sample properties (PROP-001 … PROP-010) + 5 transfer rows. No Ganache required; good for UI/report demo. |
| `seed_database_bulk.py` | **SQLite only** — random 100+ properties and transfers (`--properties` / `--transfers`). |
| `seed_data.py` | **Blockchain + SQLite** — real transactions on Ganache (`--count`, `--transfers`). |

**Note:** SQLite-only seeds do not create on-chain records. Use **Verify** only for IDs that exist on the contract, or run `seed_data.py` for full chain + DB alignment.

---

## Smart contract summary (`contracts/LandRegistry.sol`)

| Function | Purpose |
|----------|---------|
| `registerProperty(...)` | Creates a new property; increments `propertyCount`. |
| `getProperty(id)` | Returns all stored fields for verification. |
| `transferOwnership(id, newWallet, newName)` | Only current owner; emits `OwnershipTransferred`. |
| `propertyExists(id)` | Guard for invalid IDs. |

**Events:** `PropertyRegistered`, `OwnershipTransferred` — useful for auditing and future indexing.

Contracts are compiled with **`--evm-version paris`** so bytecode runs on typical Ganache builds (avoids newer opcode issues).

---

## Project structure

```text
land-record-system/
├── app.py                 # Flask routes and API
├── blockchain.py          # Web3 connection, register/transfer/verify
├── database.py            # SQLite schema and queries
├── config.py              # RPC URL, paths
├── utils.py               # Validation and SHA-256
├── compile_contract.py    # solc → build/LandRegistry.abi|.bin
├── deploy_contract.py     # Deploy to Ganache; saves contract address
├── seed_database.py       # Fixed SQLite sample (10 properties)
├── seed_database_bulk.py  # Large SQLite-only dataset
├── seed_data.py           # On-chain + SQLite bulk seed
├── test_blockchain.py     # Quick Ganache connectivity check
├── contracts/
│   └── LandRegistry.sol
├── build/
│   ├── LandRegistry.abi
│   └── LandRegistry.bin
├── config/
│   └── contract_address.txt   # Created after deploy (gitignored)
├── data/
│   └── land_records.db        # Created at runtime (gitignored)
├── templates/
│   └── index.html
├── static/css/
│   └── style.css
├── requirements.txt
├── .env.example
└── README.md
```

---

## Prerequisites

- **Python 3.9+**
- **Ganache** (GUI or CLI) listening on `http://127.0.0.1:8545`
- **Solidity compiler (`solc`)** — [Install guide](https://docs.soliditylang.org/en/latest/installing-solidity.html)

---

## Setup and run

```bash
cd land-record-system
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # optional
```

**1. Start Ganache** (default RPC `8545`, chain ID often `1337`).

**2. Compile and deploy the contract:**

```bash
python compile_contract.py
python deploy_contract.py --force
```

Use `--force` after recompiling so a new contract is deployed and the address file is updated.

**3. (Optional) Seed demo data:**

```bash
# SQLite-only (your 10 fixed records + transfers)
python seed_database.py

# Or many random SQLite rows
python seed_database_bulk.py --properties 100 --transfers 50

# Real blockchain transactions (Ganache must be running)
python seed_data.py --count 50 --transfers 10
```

**4. Run the web app:**

```bash
python app.py
```

Open **http://127.0.0.1:5000**

If port 5000 is busy (common on macOS with AirPlay), run:

```bash
FLASK_RUN_PORT=5001 python app.py
```

**5. Check blockchain connection:**

```bash
python test_blockchain.py
```

---

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Ganache connection, contract address, property count |
| GET | `/api/properties?limit=&offset=` | Paginated list from SQLite |
| POST | `/api/properties` | Register on chain + SQLite |
| GET | `/api/properties/<id>` | DB + chain + transfer history |
| GET | `/api/properties/<id>/verify` | Chain-only verification + match flag |
| POST | `/api/properties/<id>/transfer` | Transfer ownership |
| GET | `/api/properties/<id>/history` | Transfer history from SQLite |
| POST | `/api/documents/hash` | SHA-256 of file or JSON `text` |

---

## Presentation demo flow (suggested)

1. Show **status bar** — connected, contract address, on-chain count.
2. **Register** one property — highlight **transaction hash**.
3. **Verify** by ID — show blockchain JSON and “records match”.
4. **Document hash** tab — generate hash, mention optional integrity check.
5. **Transfer** to a second Ganache account — show new tx hash and **history**.
6. **All Records** — paginated list after `seed_data.py`.

---

## Limitations (important for viva)

- Runs on **local Ganache only**; not mainnet or real government integration.
- **Gas and keys** are simplified (unlocked Ganache accounts).
- SQLite can **drift** from chain if changed manually; **verify** always uses chain data.
- No role-based login, KYC, or legal workflow — scope is **technical proof of concept**.
- Storing large documents on-chain is impractical; only **hashes** are used.

---

## Troubleshooting

| Issue | What to do |
|-------|------------|
| `Blockchain not connected` | Start Ganache; check `GANACHE_RPC_URL` in `.env`. |
| `Smart contract not deployed` | Run `python deploy_contract.py --force`. |
| `invalid opcode` on register | Recompile (`compile_contract.py`) and redeploy with `--force`. |
| `Not the property owner` on transfer | Use a **new owner address** from Ganache; current owner must be an unlocked account. |
| Port 5000 in use | Use `FLASK_RUN_PORT=5001` or disable AirPlay Receiver (macOS). |

---

## Authors and license

Academic mini-project demo. Smart contract: **MIT** license (see SPDX in `LandRegistry.sol`).

For questions during evaluation, focus on: **immutability of chain records**, **tx hash as proof**, **verify vs database**, and **why SQLite + blockchain together**.
