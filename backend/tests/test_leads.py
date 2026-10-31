import pytest
from sqlalchemy import text

from app.database import engine

VALID_LEAD = {
    "full_name": "Bilal Ahmed",
    "email": "bilal@example.com",
    "company": "Ahmed Traders",
    "service_interest": "Website Development",
    "message": "I need an online store for my shop.",
    "source": "website",
}


def count_rows(table: str) -> int:
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()


# ---------- Security ----------


def test_missing_api_key_is_rejected(client):
    response = client.post("/leads", json=VALID_LEAD)
    assert response.status_code == 401
    assert count_rows("leads") == 0


def test_wrong_api_key_is_rejected(client):
    response = client.post("/leads", json=VALID_LEAD, headers={"x-api-key": "wrong"})
    assert response.status_code == 401
    assert count_rows("leads") == 0


# ---------- Valid input ----------


def test_valid_lead_is_created(client, auth_headers):
    response = client.post("/leads", json=VALID_LEAD, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "new"
    assert body["email"] == "bilal@example.com"
    assert count_rows("leads") == 1


def test_status_history_is_created(client, auth_headers):
    client.post("/leads", json=VALID_LEAD, headers=auth_headers)
    assert count_rows("lead_status_history") == 1


def test_optional_fields_can_be_left_out(client, auth_headers):
    minimal = {
        "full_name": "Sara Khan",
        "email": "sara@example.com",
        "message": "Please send me a quote.",
    }
    response = client.post("/leads", json=minimal, headers=auth_headers)
    assert response.status_code == 201


# ---------- Duplicates ----------


def test_duplicate_lead_is_rejected(client, auth_headers):
    first = client.post("/leads", json=VALID_LEAD, headers=auth_headers)
    second = client.post("/leads", json=VALID_LEAD, headers=auth_headers)
    assert first.status_code == 201
    assert second.status_code == 409
    assert count_rows("leads") == 1


def test_duplicate_ignores_capitals_and_extra_spaces(client, auth_headers):
    client.post("/leads", json=VALID_LEAD, headers=auth_headers)
    disguised = {
        **VALID_LEAD,
        "email": "BILAL@Example.com",
        "message": "I  need an ONLINE store   for my shop.",
    }
    response = client.post("/leads", json=disguised, headers=auth_headers)
    assert response.status_code == 409
    assert count_rows("leads") == 1


# ---------- Invalid input ----------

BAD_PAYLOADS = {
    "missing_name": {k: v for k, v in VALID_LEAD.items() if k != "full_name"},
    "empty_name": {**VALID_LEAD, "full_name": ""},
    "missing_email": {k: v for k, v in VALID_LEAD.items() if k != "email"},
    "invalid_email": {**VALID_LEAD, "email": "not-an-email"},
    "empty_message": {**VALID_LEAD, "message": ""},
    "whitespace_only_message": {**VALID_LEAD, "message": "     "},
    "extremely_long_message": {**VALID_LEAD, "message": "a" * 5001},
    "script_in_message": {**VALID_LEAD, "message": "<script>alert(1)</script>"},
    "unknown_field": {**VALID_LEAD, "hacker": "yes"},
}


@pytest.mark.parametrize(
    "payload", BAD_PAYLOADS.values(), ids=BAD_PAYLOADS.keys()
)
def test_bad_input_is_rejected_and_not_saved(client, auth_headers, payload):
    response = client.post("/leads", json=payload, headers=auth_headers)
    assert response.status_code == 422
    assert count_rows("leads") == 0


def test_malformed_json_is_rejected(client, auth_headers):
    response = client.post(
        "/leads",
        content="{this is not json",
        headers={**auth_headers, "Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert count_rows("leads") == 0