import copy

import pytest
from sqlalchemy import text

from app.database import engine

LEAD = {
    "full_name": "Bilal Ahmed",
    "email": "bilal@example.com",
    "message": "I need an online store for my shop.",
    "source": "website",
}

GOOD_ANALYSIS = {
    "category": "Website Development",
    "priority": "High",
    "intent": "Wants an online store",
    "summary": "Customer needs an e-commerce website for a shop.",
    "recommended_action": "Schedule an introductory call.",
    "email_subject": "Thank you for your inquiry",
    "email_draft": "Dear Bilal, thank you for contacting us. Kind regards, The Team",
}


def good_payload():
    return {
        "status": "success",
        "ai_model": "gemini-test",
        "analysis": copy.deepcopy(GOOD_ANALYSIS),
    }


def with_analysis(**changes):
    payload = good_payload()
    payload["analysis"].update(changes)
    return payload


def without_field(name):
    payload = good_payload()
    del payload["analysis"][name]
    return payload


def make_lead(client, auth_headers):
    response = client.post("/leads", json=LEAD, headers=auth_headers)
    assert response.status_code == 201
    return response.json()["id"]


def scalar(query: str):
    with engine.connect() as conn:
        return conn.execute(text(query)).scalar_one()


def test_analysis_requires_api_key(client, auth_headers):
    lead_id = make_lead(client, auth_headers)
    response = client.post(f"/leads/{lead_id}/analysis", json=good_payload())
    assert response.status_code == 401
    assert scalar("SELECT COUNT(*) FROM lead_ai_analyses") == 0


def test_success_saves_analysis_and_draft(client, auth_headers):
    lead_id = make_lead(client, auth_headers)
    response = client.post(
        f"/leads/{lead_id}/analysis", json=good_payload(), headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["lead_status"] == "awaiting_approval"
    assert scalar("SELECT COUNT(*) FROM lead_ai_analyses") == 1
    assert scalar("SELECT COUNT(*) FROM email_drafts WHERE status = 'pending'") == 1
    assert scalar("SELECT COUNT(*) FROM lead_status_history") == 2


def test_second_success_is_rejected(client, auth_headers):
    lead_id = make_lead(client, auth_headers)
    first = client.post(
        f"/leads/{lead_id}/analysis", json=good_payload(), headers=auth_headers
    )
    second = client.post(
        f"/leads/{lead_id}/analysis", json=good_payload(), headers=auth_headers
    )
    assert first.status_code == 201
    assert second.status_code == 409
    assert scalar("SELECT COUNT(*) FROM lead_ai_analyses") == 1
    assert scalar("SELECT COUNT(*) FROM email_drafts") == 1


def test_failure_is_recorded_without_draft(client, auth_headers):
    lead_id = make_lead(client, auth_headers)
    payload = {
        "status": "failed",
        "ai_model": "gemini-test",
        "error_message": "AI response is not valid JSON",
    }
    response = client.post(
        f"/leads/{lead_id}/analysis", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["draft_id"] is None
    assert response.json()["lead_status"] == "new"
    assert scalar("SELECT COUNT(*) FROM lead_ai_analyses WHERE status = 'failed'") == 1
    assert scalar("SELECT COUNT(*) FROM email_drafts") == 0


def test_success_after_failure_is_allowed(client, auth_headers):
    lead_id = make_lead(client, auth_headers)
    failed = {
        "status": "failed",
        "ai_model": "gemini-test",
        "error_message": "timeout",
    }
    client.post(f"/leads/{lead_id}/analysis", json=failed, headers=auth_headers)
    response = client.post(
        f"/leads/{lead_id}/analysis", json=good_payload(), headers=auth_headers
    )
    assert response.status_code == 201
    assert scalar("SELECT COUNT(*) FROM lead_ai_analyses") == 2


def test_unknown_lead_returns_404(client, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/leads/{fake_id}/analysis", json=good_payload(), headers=auth_headers
    )
    assert response.status_code == 404


def test_invalid_lead_id_returns_422(client, auth_headers):
    response = client.post(
        "/leads/not-a-uuid/analysis", json=good_payload(), headers=auth_headers
    )
    assert response.status_code == 422


BAD_PAYLOADS = {
    "invalid_priority": with_analysis(priority="Urgent"),
    "empty_summary": with_analysis(summary=""),
    "too_long_draft": with_analysis(email_draft="a" * 3001),
    "script_in_draft": with_analysis(email_draft="<script>alert(1)</script>"),
    "missing_subject": without_field("email_subject"),
    "unknown_field_inside_analysis": with_analysis(hacker="yes"),
    "unknown_top_level_field": {**good_payload(), "hacker": "yes"},
    "failed_without_error": {"status": "failed", "ai_model": "gemini-test"},
    "success_without_analysis": {"status": "success", "ai_model": "gemini-test"},
}


@pytest.mark.parametrize("payload", BAD_PAYLOADS.values(), ids=BAD_PAYLOADS.keys())
def test_bad_analysis_is_rejected_and_not_saved(client, auth_headers, payload):
    lead_id = make_lead(client, auth_headers)
    response = client.post(
        f"/leads/{lead_id}/analysis", json=payload, headers=auth_headers
    )
    assert response.status_code == 422
    assert scalar("SELECT COUNT(*) FROM lead_ai_analyses") == 0
    assert scalar("SELECT COUNT(*) FROM email_drafts") == 0