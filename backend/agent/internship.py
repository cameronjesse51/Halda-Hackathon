import uuid

PROBE_SEQUENCE = ["intuition_probe", "comprehension_check", "retention_check", "transfer_probe"]
MODULE_DIFFICULTIES = {1: 0.3, 2: 0.6, 3: 0.9}

DOMAIN_CONCEPTS = {
    "environmental_science": {
        1: "ecosystems",
        2: "carbon_cycle",
        3: "biodiversity_policy",
    },
    "computer_science": {
        1: "algorithms",
        2: "data_structures",
        3: "system_design",
    },
    "healthcare": {
        1: "patient_triage",
        2: "drug_interactions",
        3: "public_health_policy",
    },
    "business": {
        1: "supply_demand",
        2: "market_segmentation",
        3: "competitive_strategy",
    },
}


def start_internship(profile: dict, domain: str) -> dict:
    concepts = DOMAIN_CONCEPTS.get(domain)
    if not concepts:
        return None

    internship = {
        "internship_id": f"intern_{domain}_{uuid.uuid4().hex[:6]}",
        "domain": domain,
        "modules_completed": 0,
        "current_module": 1,
        "current_probe_index": 0,
        "concept_scores": {},
        "velocity_per_concept": {},
        "overall_domain_velocity": None,
        "acceleration": None,
        "strongest_concept_type": "",
        "inferred_traits": [],
        "status": "active",
    }

    for mod_num, concept in concepts.items():
        internship["concept_scores"][f"module_{mod_num}"] = {
            concept: {p: None for p in PROBE_SEQUENCE}
        }

    profile.setdefault("behavioral", {}).setdefault("micro_internship_results", []).append(internship)
    return internship


def get_active_internship(profile: dict):
    results = profile.get("behavioral", {}).get("micro_internship_results", [])
    for intern in results:
        if intern.get("status") == "active":
            return intern
    return None


def get_next_probe(internship: dict):
    if internship["status"] != "active":
        return None

    module = internship["current_module"]
    probe_index = internship["current_probe_index"]

    if module > 3:
        return None

    domain = internship["domain"]
    concepts = DOMAIN_CONCEPTS.get(domain, {})
    concept = concepts.get(module)
    if not concept:
        return None

    if probe_index >= len(PROBE_SEQUENCE):
        return None

    return {
        "probe_type": PROBE_SEQUENCE[probe_index],
        "concept": concept,
        "difficulty": MODULE_DIFFICULTIES[module],
        "module": module,
    }


def record_probe_score(internship: dict, probe_type: str, concept: str, score: float) -> dict:
    module_key = None
    for mk, concepts in internship["concept_scores"].items():
        if concept in concepts:
            module_key = mk
            break

    if not module_key:
        return internship

    internship["concept_scores"][module_key][concept][probe_type] = score

    scores = internship["concept_scores"][module_key][concept]
    all_done = all(v is not None for v in scores.values())

    if all_done:
        velocity = _compute_concept_velocity(scores)
        internship["velocity_per_concept"][concept] = velocity

        internship["current_probe_index"] = 0
        internship["modules_completed"] = internship["current_module"]
        internship["current_module"] += 1

        if internship["current_module"] > 3:
            internship["status"] = "completed"
            _compute_overall_velocity(internship)
    else:
        current_idx = PROBE_SEQUENCE.index(probe_type) if probe_type in PROBE_SEQUENCE else -1
        internship["current_probe_index"] = current_idx + 1

    return internship


def _compute_concept_velocity(scores: dict) -> dict:
    intuition = scores.get("intuition_probe", 0) or 0
    comprehension = scores.get("comprehension_check", 0) or 0
    retention = scores.get("retention_check", 0) or 0
    transfer = scores.get("transfer_probe", 0) or 0

    return {
        "learning_gain": round(transfer - intuition, 3),
        "comprehension_speed": round(comprehension - intuition, 3),
        "retention_drop": round(comprehension - retention, 3),
        "transfer_ability": round(transfer, 3),
        "raw_scores": {
            "intuition_probe": intuition,
            "comprehension_check": comprehension,
            "retention_check": retention,
            "transfer_probe": transfer,
        },
    }


def _compute_overall_velocity(internship: dict) -> None:
    velocities = internship["velocity_per_concept"]
    if not velocities:
        return

    gains = [v["learning_gain"] for v in velocities.values()]
    internship["overall_domain_velocity"] = round(sum(gains) / len(gains), 3)

    if len(gains) >= 2:
        if gains[-1] > gains[0] + 0.05:
            internship["acceleration"] = "positive"
        elif gains[-1] < gains[0] - 0.05:
            internship["acceleration"] = "negative"
        else:
            internship["acceleration"] = "plateau"

    best_type = None
    best_avg = -1
    for ptype in PROBE_SEQUENCE:
        scores_for_type = []
        for concept_scores in internship["concept_scores"].values():
            for concept, scores in concept_scores.items():
                if scores.get(ptype) is not None:
                    scores_for_type.append(scores[ptype])
        if scores_for_type:
            avg = sum(scores_for_type) / len(scores_for_type)
            if avg > best_avg:
                best_avg = avg
                best_type = ptype
    internship["strongest_concept_type"] = best_type or ""

    traits = []
    overall = internship["overall_domain_velocity"]
    if overall and overall > 0.3:
        traits.append("fast_learner")
    if overall and overall < 0.1:
        traits.append("needs_hands_on_practice")

    for concept, vel in velocities.items():
        if vel["transfer_ability"] > 0.7:
            traits.append(f"strong_transfer_{concept}")
        if vel["retention_drop"] > 0.3:
            traits.append(f"needs_reinforcement_{concept}")

    internship["inferred_traits"] = traits


def build_internship_prompt_section(profile: dict) -> str:
    internship = get_active_internship(profile)
    if not internship:
        return ""

    next_probe = get_next_probe(internship)
    if not next_probe:
        return ""

    module = internship["current_module"]
    domain = internship["domain"].replace("_", " ")

    scores_so_far = []
    module_key = f"module_{module}"
    if module_key in internship["concept_scores"]:
        for concept, probes in internship["concept_scores"][module_key].items():
            for ptype, score in probes.items():
                if score is not None:
                    scores_so_far.append(f"{ptype}={score}")

    velocity_summary = "not enough data yet"
    if internship["velocity_per_concept"]:
        latest = list(internship["velocity_per_concept"].values())[-1]
        velocity_summary = f"learning_gain={latest['learning_gain']}, transfer_ability={latest['transfer_ability']}"

    return f"""
<active_micro_internship>
Domain: {domain}
Module: {module} of 3 (difficulty: {MODULE_DIFFICULTIES.get(module, 0.3)})
Next probe: {next_probe['probe_type']} on "{next_probe['concept']}"
Scores so far this module: {', '.join(scores_so_far) if scores_so_far else 'none yet'}
Velocity: {velocity_summary}

Deliver the next probe naturally in conversation. Frame it as curiosity and
exploration, NEVER as a quiz or test. For intuition_probe, ask BEFORE teaching.
For comprehension_check, teach the concept first, then ask. For retention_check,
revisit later with different framing. For transfer_probe, ask them to apply it
to a new context.

After the student responds, evaluate their reasoning quality (not correctness)
and call score_probe_response with a score from 0.0 to 1.0.
</active_micro_internship>
"""
