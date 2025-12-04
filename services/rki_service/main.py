from flask import Flask, request, jsonify
import random

app = Flask(__name__)


@app.get("/health")
def health():
    return {"status": "ok", "service": "rki_service"}


@app.post("/rki/check")
def rki_check():
    """
    Simpel mock:
    - Vi kigger på customer_email eller customer_phone
    - Hvis summen af char-codes er lige -> APPROVED
      ellers -> REJECTED
    - Hvis vi mangler data -> PENDING
    """
    data = request.get_json() or {}

    identifier = (
        data.get("customer_email")
        or data.get("customer_phone")
        or data.get("customer_name")
    )

    if not identifier:
        return jsonify(
            {
                "status": "PENDING",
                "reason": "insufficient_data",
                "score": None,
            }
        )

    score = sum(ord(c) for c in identifier) % 100
    status = "APPROVED" if score % 2 == 0 else "REJECTED"

    return jsonify(
        {
            "status": status,
            "reason": "mock_rule_even_score",
            "score": score,
        }
    ), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
