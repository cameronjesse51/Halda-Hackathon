import json
import logging

from backend.agent.profile import merge_profile_update
from backend.agent.internship import (
    start_internship,
    get_active_internship,
    get_next_probe,
    record_probe_score,
)

log = logging.getLogger(__name__)


def handle_tool_call(name: str, tool_input: dict, profile: dict) -> tuple[str, dict]:
    handler = HANDLERS.get(name)
    if not handler:
        return f"Unknown tool: {name}", profile
    return handler(tool_input, profile)


def _handle_update_profile(tool_input: dict, profile: dict) -> tuple[str, dict]:
    profile = merge_profile_update(profile, tool_input)
    updated_fields = [k for k, v in tool_input.items() if v]
    return f"Profile updated: {', '.join(updated_fields)}", profile


def _handle_probe_concept(tool_input: dict, profile: dict) -> tuple[str, dict]:
    domain = tool_input.get("domain", "")
    concept = tool_input.get("concept", "")
    probe_type = tool_input.get("probe_type", "")
    difficulty = tool_input.get("difficulty", 0.3)

    internship = get_active_internship(profile)
    if not internship or internship["domain"] != domain:
        internship = start_internship(profile, domain)
        if not internship:
            return f"Unknown domain: {domain}. Cannot start micro-internship.", profile
        log.info("Started micro-internship: %s for domain %s", internship["internship_id"], domain)

    next_probe = get_next_probe(internship)

    profile.setdefault("behavioral", {}).setdefault("probe_responses", []).append({
        "domain": domain,
        "concept": concept,
        "probe_type": probe_type,
        "difficulty": difficulty,
        "response": None,
    })

    instructions = (
        f"Micro-internship active: {domain}, module {internship['current_module']}. "
        f"Deliver a {probe_type} on '{concept}' at difficulty {difficulty}. "
    )
    if probe_type == "intuition_probe":
        instructions += "Ask BEFORE teaching — get their gut feeling first."
    elif probe_type == "comprehension_check":
        instructions += "Teach the concept first, then check understanding."
    elif probe_type == "retention_check":
        instructions += "Revisit the concept with different framing."
    elif probe_type == "transfer_probe":
        instructions += "Ask them to apply the concept to a completely new context."

    return instructions, profile


def _handle_score_probe_response(tool_input: dict, profile: dict) -> tuple[str, dict]:
    domain = tool_input.get("domain", "")
    concept = tool_input.get("concept", "")
    probe_type = tool_input.get("probe_type", "")
    score = tool_input.get("score", 0.0)
    reasoning = tool_input.get("reasoning", "")

    internship = get_active_internship(profile)
    if not internship:
        return "No active micro-internship to score.", profile

    record_probe_score(internship, probe_type, concept, score)
    log.info(
        "Probe scored: %s/%s %s = %.2f (%s)",
        domain, concept, probe_type, score, reasoning,
    )

    next_probe = get_next_probe(internship)
    if not next_probe:
        velocity = internship.get("overall_domain_velocity")
        traits = internship.get("inferred_traits", [])
        return (
            f"Micro-internship complete for {domain}! "
            f"Overall velocity: {velocity}. Traits: {', '.join(traits) if traits else 'computing...'}. "
            "Share insights about what you learned about this student's learning style."
        ), profile

    return (
        f"Score recorded: {probe_type}={score}. "
        f"Next: {next_probe['probe_type']} on '{next_probe['concept']}' "
        f"(module {next_probe['module']}, difficulty {next_probe['difficulty']}). "
        "Continue the conversation naturally and deliver the next probe."
    ), profile


def _handle_search_colleges(tool_input: dict, profile: dict) -> tuple[str, dict]:
    # Stub — replace with Simon's College Scorecard wrapper + Qdrant query
    query = tool_input.get("query", "")
    filters = tool_input.get("filters", {})
    log.info("search_colleges called: query=%s filters=%s", query, json.dumps(filters))

    return json.dumps({
        "results": [
            {
                "name": "Utah Valley University",
                "location": "Orem, UT",
                "avg_net_price": 12500,
                "acceptance_rate": 0.99,
                "graduation_rate": 0.38,
                "programs": ["Computer Science", "Nursing", "Environmental Science"],
                "match_reason": "Stub data — replace with real College Scorecard results",
            },
            {
                "name": "University of Utah",
                "location": "Salt Lake City, UT",
                "avg_net_price": 18200,
                "acceptance_rate": 0.85,
                "graduation_rate": 0.69,
                "programs": ["Computer Science", "Nursing", "Biology"],
                "match_reason": "Stub data — replace with real College Scorecard results",
            },
            {
                "name": "Brigham Young University",
                "location": "Provo, UT",
                "avg_net_price": 13400,
                "acceptance_rate": 0.67,
                "graduation_rate": 0.85,
                "programs": ["Computer Science", "Environmental Science"],
                "match_reason": "Stub data — replace with real College Scorecard results",
            },
        ],
        "note": "These are stub results. Wire to College Scorecard API + Qdrant for real data.",
    }), profile


def _handle_schedule_checkin(tool_input: dict, profile: dict) -> tuple[str, dict]:
    # Stub — replace with Supabase insert into scheduled_checkins table
    channel = tool_input.get("channel", "sms")
    send_at = tool_input.get("send_at", "")
    topic = tool_input.get("topic", "")
    message_body = tool_input.get("message_body", "")
    log.info(
        "schedule_checkin: channel=%s send_at=%s topic=%s body=%s",
        channel, send_at, topic, message_body,
    )

    return (
        f"Check-in scheduled: {topic} via {channel} at {send_at}. "
        "Message will be delivered by the backend job runner."
    ), profile


HANDLERS = {
    "update_profile": _handle_update_profile,
    "probe_concept": _handle_probe_concept,
    "search_colleges": _handle_search_colleges,
    "schedule_checkin": _handle_schedule_checkin,
    "score_probe_response": _handle_score_probe_response,
}
