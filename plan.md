# HALDA AI COLLEGE COUNSELOR — HACKATHON BUILD HANDOFF

You are helping build a winning hackathon submission for the HITLAB World Cup 2026, Track 2 at Utah Valley University. This is a 24-hour build window with a $10K prize. The submission is judged 40% student experience, 35% technical execution, 25% creativity.

## What we are building

An always-on AI college counselor called Halda that meets students where they are (web chat, SMS, email) and builds a rich profile over time. Free for students. Schools purchase matched student profiles as leads. The core value prop: most tools ask students what they want. Halda figures out who they actually are through conversation, probing, and behavioral signals — then matches them to the right school.

## Hard requirements from the brief

- Multi-channel: web chat is primary, SMS handoff via Twilio once phone number is captured
- Real college data pulled from the College Scorecard API (https://collegescorecard.ed.gov/data/documentation/) — no mocked college data in the demo
- Student accounts with fully isolated multi-tenant architecture — no shared state between students
- Profile builds progressively across sessions — every conversation adds signal
- Live working demo on Thursday, judges will interact directly

## The six test personas — the demo must feel meaningfully different for each

These are the judge's test cases. If two feel the same, the agent is not personalizing enough.

- **Maya, 17, first-gen** — wants nursing, family can't pay more than $15K/year, needs the agent to lead her
- **Caleb, 18, high achiever** — 3.9 GPA, wants CS at a top-20 school, comparing 6 schools, wants data not encouragement
- **Rosa, 24, transfer** — community college, working full-time, needs credit transfer info before anything else
- **Devon, 16, career-first** — interested in environmental science but unsure if it's a real career, agent must lead with career exploration before ever mentioning schools
- **Anika, 17, international** — applying from India, needs visa-friendly schools, strong CS programs, international scholarships
- **Jordan, 15, sophomore** — complete blank slate, needs a reason to come back next month, agent should make the process feel non-overwhelming

## The student profile schema

This is the central data object everything reads from and writes to:

```json
{
  "student_id": "",
  "contact": {
    "first_name": "", "last_name": "", "email": "",
    "phone": "", "zip": "", "high_school": ""
  },
  "academic": {
    "grade": "", "gpa": null, "test_scores": {},
    "intended_major": "", "transfer_credits": null
  },
  "stated": {
    "interests": [], "career_goals": [],
    "location_pref": [], "school_size_pref": ""
  },
  "inferred": {
    "learning_style": "", "risk_tolerance": "",
    "collaboration_pref": "", "ambiguity_tolerance": ""
  },
  "behavioral": {
    "probe_responses": [],
    "micro_internship_results": [],
    "velocity_signals": {
      "causal_reasoning": null,
      "quantitative": null,
      "ambiguity_tolerance": null
    },
    "domain_affinities": {}
  },
  "hard_constraints": {
    "max_cost": null,
    "visa_required": false,
    "transfer_student": false,
    "commuter": false
  },
  "confidence_scores": {
    "career_clarity": 0.0,
    "major_fit": 0.0,
    "culture_fit": 0.0,
    "financial_fit": 0.0
  },
  "stage": "sophomore|junior|senior|transfer",
  "session_history": []
}
```

## The agent architecture

The agent uses Claude claude-sonnet-4-6 via the Anthropic API with tool calling. It does not ask direct survey questions — it extracts profile data naturally from conversation using a background extraction tool that fires after each message. The agent has the following tools:

- `update_profile(fields)` — updates any profile fields from conversation inference
- `probe_concept(domain, concept)` — fires an intuition probe question when a profile dimension has low confidence
- `search_colleges(filters)` — queries College Scorecard API with semantic + hard constraint filtering
- `schedule_checkin(date, topic)` — books a future SMS or email touchpoint
- `handoff_to_sms(phone)` — triggers Twilio SMS when phone number is captured

Every session starts by injecting the full current student profile into the system prompt so the agent always remembers everything.

## The micro-internship and probing system (our creativity differentiator)

Rather than asking students what they want (unreliable), we measure learning velocity and intuition across domains. This is our biggest differentiator and goes directly to the 25% creativity score.

Each micro-internship has 3 modules of increasing complexity (0.3 → 0.6 → 0.9 difficulty). During each module the agent fires interaction prompts of four types:

- `intuition_probe` — ask before teaching to get baseline
- `comprehension_check` — ask right after explaining
- `retention_check` — same concept, different framing, asked later
- `transfer_probe` — can they apply the concept somewhere new

The score delta across these four types per concept is the learning velocity signal. Store it as:

```json
{
  "internship_id": "",
  "domain": "",
  "modules_completed": 0,
  "concept_scores": {},
  "velocity_per_concept": {},
  "overall_domain_velocity": null,
  "acceleration": "positive|plateau|negative",
  "strongest_concept_type": "",
  "inferred_traits": []
}
```

Devon (career-first) is the primary demo vehicle for this feature. Start the micro-internship flow when a student expresses career curiosity but has no school intent.

## The college matching logic

Hybrid search: semantic similarity for fit + hard constraint metadata filtering. Use Qdrant for vector search. Enrich ~20 schools with hand-written culture/vibe fields stored locally. Hard data (cost, programs, outcomes, acceptance rate) comes live from College Scorecard API. The match should explain *why* — surfacing which profile signals drove each recommendation.

The agent triggers college search proactively when `confidence_scores.career_clarity > 0.6` AND `confidence_scores.major_fit > 0.5`. Before that threshold it keeps building the profile.

## The stage-aware experience

The agent behavior changes based on student stage:

- **Sophomore (Jordan)** — career exploration, milestone checklist, reason to return. Never pressure about schools.
- **Junior** — deep school comparison, scholarship discovery, SAT/ACT reminders
- **Senior** — essay coaching, deadline tracking, application support, offer comparison
- **Transfer (Rosa)** — credit transfer first, then everything else. Skip the sophomore/junior flow entirely.

## The demo flow for judges (8 minutes)

1. Open as Jordan (blank slate sophomore) — show onboarding, probing, and the "here's what you should do this year" milestone output. Show the reason-to-return hook.
2. Switch to Devon — trigger the career exploration micro-internship for environmental science. Show learning velocity being captured and career clarity score increasing.
3. Switch to Caleb — run a real College Scorecard query for top CS programs filtered by acceptance rate and outcomes. Show real data returned and explained.

## Tech stack

- **Frontend:** React web chat UI
- **Backend:** Node.js or Python FastAPI
- **Database:** Supabase (student profiles, session history, multi-tenant isolation)
- **Vector DB:** Qdrant (college embeddings for semantic search)
- **LLM:** Claude claude-sonnet-4-6 via Anthropic API with tool calling
- **SMS:** Twilio
- **College data:** College Scorecard API (real, live)
- **Hosting:** Whatever deploys fastest — Vercel for frontend, Railway or Render for backend

## What to scaffold first

1. Supabase schema for student profiles with RLS for multi-tenant isolation
2. College Scorecard API wrapper with the filters we need (cost, programs, acceptance rate, outcomes, visa-friendliness)
3. Claude agent with tool calling wired to `update_profile` and `search_colleges`
4. Basic React chat UI that renders agent responses and shows the profile building in a side panel
5. Qdrant setup with 20 seeded college embeddings
6. Twilio SMS webhook that shares the same agent and profile backend as web chat
7. Micro-internship flow triggered by career curiosity detection

## The north star for every decision

The brief says "nobody has built a compelling reason for a 10th grader to start early, stay engaged, and actually enjoy the process." Every feature decision should be evaluated against that. If it doesn't make Jordan want to come back next month or make Maya feel like someone is actually in her corner, deprioritize it.
