def empty_profile(student_id: str) -> dict:
    return {
        "student_id": student_id,
        "contact": {
            "first_name": "",
            "last_name": "",
            "email": "",
            "phone": "",
            "zip": "",
            "high_school": "",
        },
        "academic": {
            "grade": "",
            "gpa": None,
            "test_scores": {},
            "intended_major": "",
            "transfer_credits": None,
        },
        "stated": {
            "interests": [],
            "career_goals": [],
            "location_pref": [],
            "school_size_pref": "",
        },
        "inferred": {
            "learning_style": "",
            "risk_tolerance": "",
            "collaboration_pref": "",
            "ambiguity_tolerance": "",
        },
        "behavioral": {
            "probe_responses": [],
            "micro_internship_results": [],
            "velocity_signals": {
                "causal_reasoning": None,
                "quantitative": None,
                "ambiguity_tolerance": None,
            },
            "domain_affinities": {},
        },
        "hard_constraints": {
            "max_cost": None,
            "visa_required": False,
            "transfer_student": False,
            "commuter": False,
        },
        "confidence_scores": {
            "career_clarity": 0.0,
            "major_fit": 0.0,
            "culture_fit": 0.0,
            "financial_fit": 0.0,
        },
        "stage": "sophomore",
        "session_history": [],
    }


def merge_profile_update(profile: dict, updates: dict) -> dict:
    for key, value in updates.items():
        if key not in profile:
            continue
        if isinstance(value, dict) and isinstance(profile.get(key), dict):
            if key == "confidence_scores":
                for k, v in value.items():
                    if v is not None:
                        profile[key][k] = v
            elif key == "test_scores":
                profile[key].update(value)
            else:
                for k, v in value.items():
                    if v is not None and v != "" and v != []:
                        profile[key][k] = v
        elif isinstance(value, list) and isinstance(profile.get(key), list):
            existing = set(profile[key])
            for item in value:
                if item not in existing:
                    profile[key].append(item)
        elif value is not None and value != "" and value != []:
            profile[key] = value
    return profile
