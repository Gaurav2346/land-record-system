#!/usr/bin/env python3
"""
Bulk sample data for demo / presentation.
Registers properties on Ganache + SQLite (skips existing property numbers).

Usage:
  python seed_data.py              # 50 records
  python seed_data.py --count 100
  python seed_data.py --count 30 --transfers 5
"""

import argparse
import random
import sys
import time

import database as db
from blockchain import (
    BlockchainError,
    chain_status,
    fetch_property_from_chain,
    get_web3,
    register_property_on_chain,
    transfer_ownership_on_chain,
)
from utils import sha256_hex

FIRST_NAMES = [
    "Aarav", "Priya", "Rahul", "Sneha", "Vikram", "Ananya", "Rohan", "Kavya",
    "Arjun", "Neha", "Suresh", "Pooja", "Amit", "Divya", "Sanjay", "Meera",
    "Karan", "Isha", "Nikhil", "Tanvi", "Rajesh", "Swati", "Manoj", "Ritu",
]

LAST_NAMES = [
    "Sharma", "Patil", "Desai", "Kulkarni", "Joshi", "Reddy", "Iyer", "Mehta",
    "Singh", "Gupta", "Nair", "Rao", "Pawar", "Chavan", "Bhoir", "Kadam",
]

CITIES = [
    ("Mumbai", "Maharashtra"),
    ("Pune", "Maharashtra"),
    ("Nagpur", "Maharashtra"),
    ("Nashik", "Maharashtra"),
    ("Thane", "Maharashtra"),
    ("Aurangabad", "Maharashtra"),
    ("Kolhapur", "Maharashtra"),
    ("Solapur", "Maharashtra"),
]

PROPERTY_TYPES = ["Residential", "Commercial", "Agricultural", "Industrial"]


def random_owner() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def build_records(count: int, start_index: int) -> list:
    records = []
    for i in range(count):
        n = start_index + i
        city, state = random.choice(CITIES)
        ptype = random.choice(PROPERTY_TYPES)
        area = random.randint(400, 15000)
        if ptype == "Agricultural":
            area = random.randint(20000, 120000)
        prop_num = f"MH-{city[:3].upper()}-{n:05d}"
        survey = f"SRV/{city[:2].upper()}/{2020 + (n % 5)}/{n:04d}"
        location = f"{city}, {state}"
        doc_text = f"deed-{prop_num}-{survey}".encode("utf-8")
        doc_hash = sha256_hex(doc_text) if n % 3 == 0 else None
        records.append(
            {
                "property_number": prop_num,
                "survey_number": survey,
                "owner_name": random_owner(),
                "location": location,
                "area": area,
                "property_type": ptype,
                "document_hash": doc_hash,
            }
        )
    return records


def register_one(fields: dict) -> bool:
    if db.get_property_by_number(fields["property_number"]):
        return False
    property_id, receipt, on_chain = register_property_on_chain(**fields)
    db.insert_property(
        property_id=property_id,
        property_number=fields["property_number"],
        survey_number=fields["survey_number"],
        owner_name=fields["owner_name"],
        location=fields["location"],
        area=fields["area"],
        property_type=fields["property_type"],
        owner_wallet=on_chain["owner_wallet"],
        document_hash=fields.get("document_hash"),
        register_tx_hash=receipt.transactionHash.hex(),
        register_block_number=receipt.blockNumber,
    )
    return True


def seed_transfers(num_transfers: int) -> int:
    w3 = get_web3()
    accounts = w3.eth.accounts
    if len(accounts) < 2:
        print("Need at least 2 Ganache accounts for sample transfers.")
        return 0

    props = db.list_properties(limit=500)
    if not props:
        return 0

    done = 0
    random.shuffle(props)
    for prop in props:
        if done >= num_transfers:
            break
        try:
            before = fetch_property_from_chain(prop["id"])
            new_acc = random.choice(accounts[1:10] if len(accounts) > 10 else accounts[1:])
            new_name = random_owner()
            receipt = transfer_ownership_on_chain(
                property_id=prop["id"],
                new_owner_wallet=new_acc,
                new_owner_name=new_name,
                current_owner_wallet=before["owner_wallet"],
            )
            db.update_property_owner(
                property_id=prop["id"],
                owner_name=new_name,
                owner_wallet=new_acc,
            )
            db.insert_transfer(
                property_id=prop["id"],
                from_wallet=before["owner_wallet"],
                to_wallet=new_acc,
                from_owner_name=before["owner_name"],
                to_owner_name=new_name,
                tx_hash=receipt.transactionHash.hex(),
                block_number=receipt.blockNumber,
            )
            done += 1
        except BlockchainError as err:
            print(f"  Skip transfer #{prop['id']}: {err}")
    return done


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed land record demo data")
    parser.add_argument("--count", type=int, default=50, help="Number of properties to add")
    parser.add_argument("--start", type=int, default=1000, help="Numeric suffix for IDs")
    parser.add_argument("--transfers", type=int, default=8, help="Sample ownership transfers")
    args = parser.parse_args()

    if args.count < 1:
        print("--count must be at least 1")
        sys.exit(1)

    db.init_db()
    status = chain_status()
    if not status.get("connected") or not status.get("contract_deployed"):
        print("Start Ganache and run: python deploy_contract.py --force")
        sys.exit(1)

    print(f"Seeding up to {args.count} properties (blockchain + SQLite)...")
    records = build_records(args.count, args.start)
    added = 0
    skipped = 0
    t0 = time.time()

    for i, fields in enumerate(records, 1):
        try:
            if register_one(fields):
                added += 1
                if added % 10 == 0:
                    print(f"  Registered {added}/{args.count}...")
            else:
                skipped += 1
        except BlockchainError as err:
            print(f"  Failed {fields['property_number']}: {err}")
            break

    elapsed = time.time() - t0
    print(f"Done: {added} added, {skipped} skipped ({elapsed:.1f}s)")
    print(f"SQLite total: {db.count_properties()} properties")

    if args.transfers > 0 and added > 0:
        print(f"Adding up to {args.transfers} sample transfers...")
        t_count = seed_transfers(args.transfers)
        print(f"Transfers recorded: {t_count} (history rows: {db.count_transfers()})")

    print("Refresh dashboard → All Records tab.")


if __name__ == "__main__":
    try:
        main()
    except BlockchainError as err:
        sys.exit(f"Error: {err}")
