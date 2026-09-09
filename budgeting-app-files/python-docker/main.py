import os
from decimal import Decimal, InvalidOperation

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from model import Account, Base, Transaction

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

engine = create_engine(DATABASE_URL, future=True)
Base.metadata.create_all(bind=engine)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:8081"]}})


def tx_to_dict(tx: Transaction) -> dict:
    return {
        "id": tx.id,
        "account_id": tx.account_id,
        "description": tx.description,
        "amount": float(tx.amount),
        "entry_type": tx.entry_type,
        "created_at": tx.created_at.isoformat(),
    }


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.post("/api/accounts")
def create_or_get_account():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    name = str(payload.get("name", "")).strip()

    if not email:
        return jsonify({"error": "Email is required."}), 400
    if not name:
        return jsonify({"error": "Name is required."}), 400

    with Session(engine) as session:
        existing = session.scalar(select(Account).where(Account.email == email))
        if existing:
            return jsonify(
                {
                    "id": existing.id,
                    "name": existing.name,
                    "email": existing.email,
                    "existing": True,
                }
            ), 200

        account = Account(name=name, email=email)
        session.add(account)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            existing = session.scalar(select(Account).where(Account.email == email))
            if existing:
                return jsonify(
                    {
                        "id": existing.id,
                        "name": existing.name,
                        "email": existing.email,
                        "existing": True,
                    }
                ), 200
            return jsonify({"error": "Could not create account."}), 500

        session.refresh(account)
        return jsonify(
            {
                "id": account.id,
                "name": account.name,
                "email": account.email,
                "existing": False,
            }
        ), 201


@app.get("/api/accounts/<int:account_id>/transactions")
def list_transactions(account_id: int):
    with Session(engine) as session:
        account = session.get(Account, account_id)
        if not account:
            return jsonify({"error": "Account not found."}), 404

        rows = session.scalars(
            select(Transaction)
            .where(Transaction.account_id == account_id)
            .order_by(Transaction.created_at.desc())
        ).all()

        return jsonify({"transactions": [tx_to_dict(t) for t in rows]}), 200


@app.post("/api/accounts/<int:account_id>/transactions")
def create_transaction(account_id: int):
    payload = request.get_json(silent=True) or {}
    description = str(payload.get("description", "")).strip()
    entry_type = str(payload.get("entry_type", "")).strip().lower()
    raw_amount = payload.get("amount")

    if not description:
        return jsonify({"error": "Description is required."}), 400
    if entry_type not in {"income", "expense"}:
        return jsonify({"error": "entry_type must be income or expense."}), 400

    try:
        amount = Decimal(str(raw_amount))
    except (InvalidOperation, TypeError):
        return jsonify({"error": "Amount must be a valid number."}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0."}), 400

    with Session(engine) as session:
        account = session.get(Account, account_id)
        if not account:
            return jsonify({"error": "Account not found."}), 404

        tx = Transaction(
            account_id=account_id,
            description=description,
            amount=amount,
            entry_type=entry_type,
        )
        session.add(tx)
        session.commit()
        session.refresh(tx)

        return jsonify({"transaction": tx_to_dict(tx)}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)