import unittest
from datetime import datetime, timezone

from backend.agent.college_recommendations import normalize_college_results


NOW = datetime(2026, 6, 18, 18, 30, tzinfo=timezone.utc)


def profile(*, budget=None, gpa=None, major=""):
    return {
        "academic": {"gpa": gpa, "intended_major": major},
        "hard_constraints": {"max_cost": budget},
    }


class CollegeRecommendationNormalizationTests(unittest.TestCase):
    def test_normalizes_aliases_budget_rates_and_source(self):
        payload = normalize_college_results(
            [{
                "unit_id": 230764,
                "school_name": "Example University",
                "school_city": "Orem",
                "school_state": "UT",
                "avg_net_price": "$13,250",
                "acceptance_rate": 65,
                "completion_rate": 0.71,
                "median_earnings": "58,400",
                "programs": ["Registered Nursing", "Biology"],
                "similarity": 0.873,
            }],
            profile=profile(budget=15000, gpa=3.5),
            filters={"programs": ["Nursing"], "location_state": ["UT"]},
            query="Affordable nursing programs in Utah",
            now=NOW,
        )

        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["event"], "college_results")
        self.assertEqual(payload["generated_at"], "2026-06-18T18:30:00Z")
        card = payload["colleges"][0]
        self.assertEqual(card["college_id"], "230764")
        self.assertEqual(card["financials"]["net_price"], 13250)
        self.assertEqual(card["financials"]["budget_difference"], 1750)
        self.assertTrue(card["financials"]["within_budget"])
        self.assertEqual(card["admissions"]["admission_rate"], 0.65)
        self.assertEqual(card["program"]["status"], "available")
        self.assertEqual(card["match_score"], 87.3)
        self.assertIn("College Scorecard", card["sources"][0]["name"])
        self.assertIn("financials.net_price", card["sources"][0]["fields"])

    def test_unknown_data_stays_null_or_unknown(self):
        payload = normalize_college_results(
            [{"id": "school-1", "name": "Sparse College"}],
            profile=profile(),
            filters={},
            query="A good college",
            now=NOW,
        )
        card = payload["colleges"][0]
        self.assertIsNone(card["financials"]["net_price"])
        self.assertIsNone(card["financials"]["within_budget"])
        self.assertIsNone(card["admissions"]["admission_rate"])
        self.assertEqual(card["program"]["status"], "unknown")
        self.assertEqual(card["classification"]["label"], "unknown")

    def test_student_gpa_drives_classification_when_comparison_exists(self):
        payload = normalize_college_results(
            [{
                "id": "school-2",
                "name": "Academic College",
                "admission_rate": 0.55,
                "average_gpa": 3.4,
            }],
            profile=profile(gpa=3.8),
            filters={},
            query="Computer science",
            now=NOW,
        )
        classification = payload["colleges"][0]["classification"]
        self.assertEqual(classification["label"], "likely")
        self.assertEqual(classification["basis"], "student_academic_profile")

    def test_filter_budget_is_used_when_profile_budget_is_missing(self):
        payload = normalize_college_results(
            [{"id": "school-3", "name": "Budget College", "net_price": 12000}],
            profile=profile(),
            filters={"max_net_price": 10000},
            query="Affordable colleges",
            now=NOW,
        )
        financials = payload["colleges"][0]["financials"]
        self.assertEqual(financials["student_budget"], 10000)
        self.assertEqual(financials["budget_difference"], -2000)
        self.assertFalse(financials["within_budget"])


if __name__ == "__main__":
    unittest.main()
