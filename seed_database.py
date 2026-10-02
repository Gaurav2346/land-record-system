"""Seed sample land records for the blockchain land registry demo (SQLite only)."""

from database import (
    get_property_by_id,
    init_db,
    insert_property,
    insert_transfer,
)


def seed_properties():
    init_db()

    properties = [
        {
            "property_id": 1,
            "property_number": "PROP-001",
            "survey_number": "SUR-101",
            "owner_name": "Gaurav Bhoir",
            "location": "Mumbai, Maharashtra",
            "area": 1200,
            "property_type": "Residential",
            "owner_wallet": "0x735F7A1102f9CFB9DA7351Ed9a393E8f2B86d675",
            "document_hash": "a1b2c3d4e5f60123456789abcdef1234567890abcdef1234567890abcdef1234",
            "register_tx_hash": "0xabc001",
            "register_block_number": 1,
        },
        {
            "property_id": 2,
            "property_number": "PROP-002",
            "survey_number": "SUR-102",
            "owner_name": "Rahul Sharma",
            "location": "Pune, Maharashtra",
            "area": 1800,
            "property_type": "Residential",
            "owner_wallet": "0x1111111111111111111111111111111111111111",
            "document_hash": "b2c3d4e5f60123456789abcdef1234567890abcdef1234567890abcdef12345678",
            "register_tx_hash": "0xabc002",
            "register_block_number": 2,
        },
        {
            "property_id": 3,
            "property_number": "PROP-003",
            "survey_number": "SUR-103",
            "owner_name": "Priya Patil",
            "location": "Nashik, Maharashtra",
            "area": 2500,
            "property_type": "Agricultural",
            "owner_wallet": "0x2222222222222222222222222222222222222222",
            "document_hash": "c3d4e5f60123456789abcdef1234567890abcdef1234567890abcdef1234567890",
            "register_tx_hash": "0xabc003",
            "register_block_number": 3,
        },
        {
            "property_id": 4,
            "property_number": "PROP-004",
            "survey_number": "SUR-104",
            "owner_name": "Amit Joshi",
            "location": "Thane, Maharashtra",
            "area": 950,
            "property_type": "Commercial",
            "owner_wallet": "0x3333333333333333333333333333333333333333",
            "document_hash": "d4e5f60123456789abcdef1234567890abcdef1234567890abcdef1234567890",
            "register_tx_hash": "0xabc004",
            "register_block_number": 4,
        },
        {
            "property_id": 5,
            "property_number": "PROP-005",
            "survey_number": "SUR-105",
            "owner_name": "Sneha Kulkarni",
            "location": "Nagpur, Maharashtra",
            "area": 3200,
            "property_type": "Agricultural",
            "owner_wallet": "0x4444444444444444444444444444444444444444",
            "document_hash": "e5f60123456789abcdef1234567890abcdef1234567890abcdef12345678901",
            "register_tx_hash": "0xabc005",
            "register_block_number": 5,
        },
        {
            "property_id": 6,
            "property_number": "PROP-006",
            "survey_number": "SUR-106",
            "owner_name": "Vikram Mehta",
            "location": "Aurangabad, Maharashtra",
            "area": 1450,
            "property_type": "Residential",
            "owner_wallet": "0x5555555555555555555555555555555555555555",
            "document_hash": "f60123456789abcdef1234567890abcdef1234567890abcdef123456789012",
            "register_tx_hash": "0xabc006",
            "register_block_number": 6,
        },
        {
            "property_id": 7,
            "property_number": "PROP-007",
            "survey_number": "SUR-107",
            "owner_name": "Neha Deshmukh",
            "location": "Kolhapur, Maharashtra",
            "area": 2100,
            "property_type": "Residential",
            "owner_wallet": "0x6666666666666666666666666666666666666666",
            "document_hash": "0123456789abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "register_tx_hash": "0xabc007",
            "register_block_number": 7,
        },
        {
            "property_id": 8,
            "property_number": "PROP-008",
            "survey_number": "SUR-108",
            "owner_name": "Karan Shah",
            "location": "Ahmedabad, Gujarat",
            "area": 1750,
            "property_type": "Commercial",
            "owner_wallet": "0x7777777777777777777777777777777777777777",
            "document_hash": "123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0",
            "register_tx_hash": "0xabc008",
            "register_block_number": 8,
        },
        {
            "property_id": 9,
            "property_number": "PROP-009",
            "survey_number": "SUR-109",
            "owner_name": "Rohan Verma",
            "location": "Delhi",
            "area": 2800,
            "property_type": "Commercial",
            "owner_wallet": "0x8888888888888888888888888888888888888888",
            "document_hash": "23456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef01",
            "register_tx_hash": "0xabc009",
            "register_block_number": 9,
        },
        {
            "property_id": 10,
            "property_number": "PROP-010",
            "survey_number": "SUR-110",
            "owner_name": "Anjali Singh",
            "location": "Bangalore, Karnataka",
            "area": 1600,
            "property_type": "Residential",
            "owner_wallet": "0x9999999999999999999999999999999999999999",
            "document_hash": "3456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef012",
            "register_tx_hash": "0xabc010",
            "register_block_number": 10,
        },
    ]

    for property_data in properties:
        try:
            insert_property(**property_data)
            print(
                f"Inserted: "
                f"{property_data['property_number']} - "
                f"{property_data['owner_name']}"
            )
        except Exception as error:
            print(
                f"Skipped {property_data['property_number']}: "
                f"{error}"
            )


def seed_transfers():
    transfers = [
        {
            "property_id": 2,
            "from_wallet": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "to_wallet": "0x1111111111111111111111111111111111111111",
            "from_owner_name": "Suresh Sharma",
            "to_owner_name": "Rahul Sharma",
            "tx_hash": "0xtransfer001",
            "block_number": 12,
        },
        {
            "property_id": 3,
            "from_wallet": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "to_wallet": "0x2222222222222222222222222222222222222222",
            "from_owner_name": "Mahesh Patil",
            "to_owner_name": "Priya Patil",
            "tx_hash": "0xtransfer002",
            "block_number": 15,
        },
        {
            "property_id": 4,
            "from_wallet": "0xcccccccccccccccccccccccccccccccccccccc",
            "to_wallet": "0x3333333333333333333333333333333333333333",
            "from_owner_name": "Raj Joshi",
            "to_owner_name": "Amit Joshi",
            "tx_hash": "0xtransfer003",
            "block_number": 18,
        },
        {
            "property_id": 5,
            "from_wallet": "0xdddddddddddddddddddddddddddddddddddddd",
            "to_wallet": "0x4444444444444444444444444444444444444444",
            "from_owner_name": "Meena Kulkarni",
            "to_owner_name": "Sneha Kulkarni",
            "tx_hash": "0xtransfer004",
            "block_number": 21,
        },
        {
            "property_id": 8,
            "from_wallet": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "to_wallet": "0x7777777777777777777777777777777777777777",
            "from_owner_name": "Harsh Shah",
            "to_owner_name": "Karan Shah",
            "tx_hash": "0xtransfer005",
            "block_number": 25,
        },
    ]

    for transfer in transfers:
        if not get_property_by_id(transfer["property_id"]):
            print(
                f"Skipped transfer for property "
                f"{transfer['property_id']}: property not in database"
            )
            continue
        try:
            insert_transfer(**transfer)
            print(
                f"Transfer added for property "
                f"{transfer['property_id']}"
            )
        except Exception as error:
            print(
                f"Skipped transfer for property "
                f"{transfer['property_id']}: {error}"
            )


if __name__ == "__main__":
    print("=" * 60)
    print("LAND RECORD DATABASE SEEDER")
    print("=" * 60)

    seed_properties()
    seed_transfers()

    print()
    print("=" * 60)
    print("SEEDING COMPLETED")
    print("=" * 60)
