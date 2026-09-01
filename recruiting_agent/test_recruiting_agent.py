import os
import sys
from pathlib import Path

repo_dir = Path(__file__).parent
sys.path = [str(repo_dir.parent)] + [path for path in sys.path if path != str(repo_dir)]
os.environ.setdefault("OPENAI_API_KEY", "test-key")

from recruiting_agent import recruiting_agent as agent_module


REJECTED_RECORD = {
    "candidate_id": "CAND-REJECTED",
    "name": "Rejected Candidate",
    "email": "rejected@example.com",
    "rejected": True,
}


def test_send_candidate_email_requires_candidate_id(monkeypatch):
    send_calls = []
    monkeypatch.setattr(agent_module.data_service, "get_candidate_record", lambda candidate_id: send_calls.append(candidate_id))

    result = agent_module.send_candidate_email.invoke({
        "candidate": {"name": "Rejected Candidate", "email": "rejected@example.com"},
        "subject": "Interview",
        "body": "Please interview.",
    })

    assert result["status"] == "failed"
    assert "Candidate ID is required" in result["error"]
    assert send_calls == []


def test_send_candidate_email_does_not_send_to_rejected_candidate(monkeypatch):
    monkeypatch.setattr(agent_module.data_service, "get_candidate_record", lambda candidate_id: REJECTED_RECORD)

    result = agent_module.send_candidate_email.invoke({
        "candidate": REJECTED_RECORD,
        "subject": "Interview",
        "body": "Please interview.",
    })

    assert result == {
        "status": "needs_confirmation",
        "reason": "candidate is marked rejected",
        "candidate_id": "CAND-REJECTED",
    }


def test_send_candidate_email_sends_rejected_candidate_with_override(monkeypatch):
    monkeypatch.setattr(agent_module.data_service, "get_candidate_record", lambda candidate_id: REJECTED_RECORD)

    result = agent_module.send_candidate_email.invoke({
        "candidate": REJECTED_RECORD,
        "subject": "Interview",
        "body": "Please interview.",
        "override_rejected": True,
        "from_recruiter": {"email": "recruiter@example.com", "name": "Recruiter"},
    })

    assert result["status"] == "sent"
    assert result["to"] == "rejected@example.com"
