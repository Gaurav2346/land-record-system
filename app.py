"""Flask dashboard for blockchain land record management."""

from flask import Flask, jsonify, render_template, request

import database as db
from blockchain import (
    BlockchainError,
    chain_status,
    fetch_property_from_chain,
    register_property_on_chain,
    transfer_ownership_on_chain,
    verify_property_on_chain,
)
from utils import sha256_hex, validate_registration_payload

app = Flask(__name__)
db.init_db()


def error_response(message: str, status: int = 400):
    return jsonify({"success": False, "error": message}), status


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    status = chain_status()
    status["total_db_properties"] = db.count_properties()
    status["total_transfers"] = db.count_transfers()
    return jsonify({"success": True, "data": status})


@app.route("/api/properties", methods=["GET"])
def list_properties():
    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", type=int, default=0)
    if offset < 0:
        offset = 0
    if limit is not None and limit < 1:
        limit = 1
    if limit is not None and limit > 500:
        limit = 500
    rows = db.list_properties(limit=limit, offset=offset)
    return jsonify(
        {
            "success": True,
            "data": rows,
            "total": db.count_properties(),
            "limit": limit,
            "offset": offset,
        }
    )


@app.route("/api/properties", methods=["POST"])
def create_property():
    payload = request.get_json(silent=True) or {}
    try:
        fields = validate_registration_payload(payload)
    except ValueError as exc:
        return error_response(str(exc))

    if db.get_property_by_number(fields["property_number"]):
        return error_response("Property number already exists in the database.")

    if not fields.get("document_hash"):
        import time
        seed = f"{fields['property_number']}|{fields['survey_number']}|{fields['owner_name']}|{fields['location']}|{fields['area']}|{fields['property_type']}|{time.time()}"
        fields["document_hash"] = sha256_hex(seed.encode("utf-8"))

    try:
        property_id, receipt, on_chain = register_property_on_chain(**fields)
    except BlockchainError as exc:
        return error_response(str(exc), 503)

    db.insert_property(
        property_id=property_id,
        property_number=fields["property_number"],
        survey_number=fields["survey_number"],
        owner_name=fields["owner_name"],
        location=fields["location"],
        area=fields["area"],
        property_type=fields["property_type"],
        owner_wallet=on_chain["owner_wallet"],
        document_hash=fields["document_hash"],
        register_tx_hash=receipt.transactionHash.hex(),
        register_block_number=receipt.blockNumber,
    )

    return jsonify(
        {
            "success": True,
            "message": "Property registered on blockchain and saved to SQLite.",
            "property_id": property_id,
            "transaction_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
            "blockchain_record": on_chain,
            "local_record": {
                "property_id": property_id,
                "property_number": fields["property_number"],
                "survey_number": fields["survey_number"],
                "owner_name": fields["owner_name"],
                "location": fields["location"],
                "area": fields["area"],
                "property_type": fields["property_type"],
                "document_hash": fields["document_hash"],
                "owner_wallet": on_chain["owner_wallet"],
            },
        }
    )


@app.route("/api/properties/<int:property_id>", methods=["GET"])
def show_property(property_id: int):
    local = db.get_property_by_id(property_id)
    try:
        on_chain = verify_property_on_chain(property_id)
    except BlockchainError as exc:
        if local:
            return jsonify(
                {
                    "success": True,
                    "warning": str(exc),
                    "database_record": local,
                    "blockchain_record": None,
                }
            )
        return error_response(str(exc), 404)

    history = db.get_transfer_history(property_id)
    return jsonify(
        {
            "success": True,
            "database_record": local,
            "blockchain_record": on_chain,
            "transfer_history": history,
            "records_match": _records_match(local, on_chain) if local else None,
        }
    )


@app.route("/api/properties/<int:property_id>/verify", methods=["GET"])
def verify_property(property_id: int):
    try:
        on_chain = verify_property_on_chain(property_id)
    except BlockchainError as exc:
        return error_response(str(exc), 404)

    local = db.get_property_by_id(property_id)
    history = db.get_transfer_history(property_id)
    return jsonify(
        {
            "success": True,
            "verified_on_blockchain": True,
            "blockchain_record": on_chain,
            "database_record": local,
            "records_match": _records_match(local, on_chain) if local else None,
            "transfer_history": history,
        }
    )


@app.route("/api/properties/<int:property_id>/transfer", methods=["POST"])
def transfer_property(property_id: int):
    payload = request.get_json(silent=True) or {}
    new_wallet = str(payload.get("new_owner_wallet", "")).strip()
    new_name = str(payload.get("new_owner_name", "")).strip()

    if not new_wallet or not new_name:
        return error_response("new_owner_wallet and new_owner_name are required.")

    local = db.get_property_by_id(property_id)
    if not local:
        return error_response("Property not found in database.", 404)

    try:
        before = fetch_property_from_chain(property_id)
        receipt = transfer_ownership_on_chain(
            property_id=property_id,
            new_owner_wallet=new_wallet,
            new_owner_name=new_name,
            current_owner_wallet=before["owner_wallet"],
        )
        after = fetch_property_from_chain(property_id)
    except BlockchainError as exc:
        return error_response(str(exc), 503)

    db.update_property_owner(
        property_id=property_id,
        owner_name=new_name,
        owner_wallet=new_wallet,
    )
    db.insert_transfer(
        property_id=property_id,
        from_wallet=before["owner_wallet"],
        to_wallet=new_wallet,
        from_owner_name=before.get("owner_name", ""),
        to_owner_name=new_name,
        tx_hash=receipt.transactionHash.hex(),
        block_number=receipt.blockNumber,
    )

    return jsonify(
        {
            "success": True,
            "message": "Ownership transferred on blockchain.",
            "property_id": property_id,
            "transaction_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
            "previous_owner": before["owner_wallet"],
            "previous_owner_name": before.get("owner_name", ""),
            "new_owner": after["owner_wallet"],
            "new_owner_name": new_name,
            "blockchain_record": after,
        }
    )


@app.route("/api/properties/<int:property_id>/history", methods=["GET"])
def property_history(property_id: int):
    if not db.get_property_by_id(property_id):
        return error_response("Property not found.", 404)
    return jsonify(
        {
            "success": True,
            "data": db.get_transfer_history(property_id),
        }
    )


@app.route("/api/documents/hash", methods=["POST"])
def hash_document():
    """Compute SHA-256 for optional document verification (text upload demo)."""
    if request.files.get("file"):
        content = request.files["file"].read()
        filename = request.files["file"].filename
    else:
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("text", ""))
        if not text.strip():
            return error_response("Provide a file or JSON field 'text'.")
        content = text.encode("utf-8")
        filename = "inline-text"

    digest = sha256_hex(content)
    return jsonify(
        {
            "success": True,
            "filename": filename,
            "sha256": digest,
            "sha256_prefixed": f"0x{digest}",
        }
    )


def _records_match(local: dict, on_chain: dict) -> bool:
    if not local:
        return False
    checks = [
        local["property_number"] == on_chain["property_number"],
        local["survey_number"] == on_chain["survey_number"],
        local["owner_name"] == on_chain["owner_name"],
        local["location"] == on_chain["location"],
        int(local["area"]) == int(on_chain["area"]),
        local["property_type"] == on_chain["property_type"],
        local["owner_wallet"].lower() == on_chain["owner_wallet"].lower(),
    ]
    local_doc = (local.get("document_hash") or "").lower().replace("0x", "")
    chain_doc = (on_chain.get("document_hash") or "").lower().replace("0x", "")
    if local_doc or chain_doc:
        checks.append(local_doc == chain_doc)
    return all(checks)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
