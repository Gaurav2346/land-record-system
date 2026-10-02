"""Generate large SQLite-only demo datasets (no Ganache required)."""

import random

from database import get_property_by_id, init_db, insert_property, insert_transfer


FIRST_NAMES = [
    "Aarav", "Aditi", "Akash", "Amit", "Ananya", "Anjali", "Arjun", "Gaurav",
    "Neha", "Priya", "Rahul", "Rohan", "Sneha", "Suresh", "Vikram",
]

LAST_NAMES = [
    "Bhoir", "Sharma", "Patil", "Joshi", "Deshmukh", "Kulkarni", "Mehta", "Shah",
]

LOCATIONS = [
    "Mumbai, Maharashtra",
    "Pune, Maharashtra",
    "Nashik, Maharashtra",
    "Thane, Maharashtra",
    "Nagpur, Maharashtra",
]

PROPERTY_TYPES = ["Residential", "Commercial", "Agricultural", "Industrial"]


def random_wallet(seed: int) -> str:
    random.seed(seed)
    return "0x" + "".join(random.choice("0123456789abcdef") for _ in range(40))


def random_hash(seed: int) -> str:
    random.seed(seed)
    return "".join(random.choice("0123456789abcdef") for _ in range(64))


def seed_properties(total: int = 100) -> int:
    inserted = 0
    for property_id in range(1, total + 1):
        try:
            insert_property(
                property_id=property_id,
                property_number=f"PROP-{property_id:04d}",
                survey_number=f"SUR-{random.randint(10000, 99999)}",
                owner_name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                location=random.choice(LOCATIONS),
                area=random.choice([500, 1200, 1800, 2500, 3200]),
                property_type=random.choice(PROPERTY_TYPES),
                owner_wallet=random_wallet(property_id),
                document_hash=random_hash(property_id + 1000),
                register_tx_hash="0x" + random_hash(property_id + 2000),
                register_block_number=property_id + 1,
            )
            inserted += 1
        except Exception as err:
            print(f"Skipped PROP-{property_id:04d}: {err}")
    return inserted


def seed_transfers(total_properties: int = 100, count: int = 50) -> int:
    inserted = 0
    ids = list(range(1, total_properties + 1))
    random.shuffle(ids)
    for property_id in ids[:count]:
        row = get_property_by_id(property_id)
        if not row:
            continue
        try:
            insert_transfer(
                property_id=property_id,
                from_wallet=row["owner_wallet"],
                to_wallet=random_wallet(property_id + 5000),
                from_owner_name=row["owner_name"],
                to_owner_name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                tx_hash="0x" + random_hash(property_id + 6000),
                block_number=row["register_block_number"] + random.randint(5, 50),
            )
            inserted += 1
        except Exception as err:
            print(f"Skipped transfer {property_id}: {err}")
    return inserted


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--properties", type=int, default=100)
    parser.add_argument("--transfers", type=int, default=50)
    args = parser.parse_args()

    init_db()
    p = seed_properties(args.properties)
    t = seed_transfers(args.properties, args.transfers)
    print(f"Inserted {p} properties, {t} transfers.")
