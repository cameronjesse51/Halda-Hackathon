import unittest

from backend.agent.tool_handlers import (
    _add_peer_interest_counts,
    _peer_interest_counts,
    _recommendation_record,
)


class _RpcResult:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return self


class _FakeDb:
    def __init__(self, data):
        self.data = data
        self.params = None

    def rpc(self, name, params):
        assert name == "peer_college_interest_counts"
        self.params = params
        return _RpcResult(self.data)


class RecommendationPersistenceTests(unittest.TestCase):
    def test_record_is_tenant_scoped_and_excludes_contact_and_history(self):
        payload = {
            "recommendation_set_id": "rec_123",
            "schema_version": "2.0",
            "generated_at": "2026-06-18T18:30:00Z",
            "query": {"text": "Nursing", "requested_program": "Nursing"},
            "colleges": [{"college_id": "230764", "name": "Example"}],
        }
        profile = {
            "student_id": "123e4567-e89b-12d3-a456-426614174000",
            "contact": {"phone": "+18015551234", "email": "student@example.com"},
            "academic": {"gpa": 3.8},
            "stated": {"interests": ["healthcare"]},
            "hard_constraints": {"max_cost": 15000},
            "confidence_scores": {"career_clarity": 0.8},
            "stage": "senior",
            "session_history": [{"role": "user", "content": "private"}],
        }

        record = _recommendation_record(payload, profile)

        self.assertEqual(record["id"], "rec_123")
        self.assertEqual(record["student_id"], profile["student_id"])
        self.assertEqual(record["recommendations"], payload["colleges"])
        self.assertNotIn("contact", record["profile_snapshot"])
        self.assertNotIn("session_history", record["profile_snapshot"])

    def test_peer_counts_request_only_aggregates_for_current_school(self):
        db = _FakeDb([
            {"college_id": "230764", "peer_count": 2},
            {"college_id": "999", "peer_count": 0},
        ])
        profile = {
            "student_id": "123e4567-e89b-12d3-a456-426614174000",
            "contact": {"high_school": "Salt Lake City High School"},
        }

        counts = _peer_interest_counts(db, profile, [{"college_id": "230764"}])

        self.assertEqual(counts, {"230764": 2})
        self.assertEqual(db.params["current_student_id"], profile["student_id"])
        self.assertEqual(db.params["current_high_school"], "Salt Lake City High School")
        self.assertEqual(db.params["requested_college_ids"], ["230764"])

    def test_peer_counts_are_omitted_without_a_high_school(self):
        db = _FakeDb([])
        counts = _peer_interest_counts(
            db,
            {"student_id": "123", "contact": {"high_school": ""}},
            [{"college_id": "230764"}],
        )
        self.assertEqual(counts, {})
        self.assertIsNone(db.params)

    def test_only_positive_counts_are_added_to_colleges(self):
        payload = {"colleges": [
            {"college_id": "230764", "name": "Example"},
            {"college_id": "999", "name": "Other"},
        ]}

        enriched = _add_peer_interest_counts(payload, {"230764": 3})

        self.assertEqual(
            enriched["colleges"][0]["community"],
            {"high_school_peer_count": 3},
        )
        self.assertNotIn("community", enriched["colleges"][1])


if __name__ == "__main__":
    unittest.main()
