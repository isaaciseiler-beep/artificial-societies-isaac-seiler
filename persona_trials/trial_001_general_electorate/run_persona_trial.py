import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PERSONAS_PATH = ROOT / "personas_100.csv"
RESULTS_DIR = ROOT / "results"
RUNS_PER_PERSONA = 10
METHOD = "poll_excluded_10x_modal_with_undecided"
MODEL_NAME = "local-persona-engine-v1"
TEMPERATURE = "hash-varied"


MATCHUPS = [
    {
        "id": "q1_elsayed_vs_rogers",
        "key": "elsayed_vs_rogers",
        "democrat": "Abdul El-Sayed",
        "republican": "Mike Rogers",
        "question": "If the general election for Michigan's 2026 U.S. Senate race were held today and the candidates were Abdul El-Sayed and Mike Rogers, who would you most likely support?",
    },
    {
        "id": "q2_stevens_vs_rogers",
        "key": "stevens_vs_rogers",
        "democrat": "Haley Stevens",
        "republican": "Mike Rogers",
        "question": "If the general election for Michigan's 2026 U.S. Senate race were held today and the candidates were Haley Stevens and Mike Rogers, who would you most likely support?",
    },
    {
        "id": "q3_mcmorrow_vs_rogers",
        "key": "mcmorrow_vs_rogers",
        "democrat": "Mallory McMorrow",
        "republican": "Mike Rogers",
        "question": "If the general election for Michigan's 2026 U.S. Senate race were held today and the candidates were Mallory McMorrow and Mike Rogers, who would you most likely support?",
    },
]


PERSONA_FIELDS = [
    "persona_id",
    "first_name",
    "age_group",
    "race_ethnicity",
    "gender",
    "county",
    "region",
    "urban_suburban_rural",
    "education",
    "income_band",
    "party_lean",
    "ideology",
    "past_vote_pattern",
    "turnout_likelihood",
    "top_issues",
    "human_profile",
    "persona_weight",
]


SUBGROUP_FIELDS = [
    "party_lean",
    "region",
    "urban_suburban_rural",
    "age_group",
    "race_ethnicity",
    "ideology",
    "education",
    "income_band",
]


BASE_DEM_SCORE = {
    "Strong Democrat": 0.86,
    "Lean Democrat": 0.68,
    "Independent / swing": 0.50,
    "Lean Republican": 0.32,
    "Strong Republican": 0.14,
}


IDEOLOGY_DEM_MOD = {
    "Progressive": 0.08,
    "Liberal": 0.05,
    "Moderate": 0.00,
    "Conservative": -0.06,
    "Very conservative": -0.10,
}


COUNTY_DEM_MOD = {
    "Wayne County": 0.04,
    "Washtenaw County": 0.05,
    "Ingham County": 0.03,
    "Oakland County": 0.02,
    "Kent County": 0.01,
    "Genesee County": 0.01,
    "Macomb County": -0.02,
    "Ottawa County": -0.05,
    "Livingston County": -0.05,
    "Hillsdale County": -0.06,
    "Barry County": -0.04,
    "St. Clair County": -0.04,
}


WEIGHT_TARGETS = {
    "age_group": {"18-29": 0.14, "30-44": 0.21, "45-64": 0.37, "65+": 0.28},
    "race_ethnicity": {
        "White non-Hispanic": 0.78,
        "Black": 0.13,
        "Hispanic": 0.05,
        "Asian": 0.01,
        "Multiracial / other": 0.03,
    },
    "gender": {"Female": 0.54, "Male": 0.46},
}


def stable_variation(*parts, width: float = 0.035) -> float:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    value = int(digest[:8], 16) / 0xFFFFFFFF
    return (value - 0.5) * 2 * width


def stable_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def issue_text(persona: dict) -> str:
    issues = [issue.strip().lower() for issue in persona["top_issues"].split(";")]
    return "; ".join(issues[:2])


def issue_mod(persona: dict, candidate: str) -> float:
    issues = persona["top_issues"].lower()
    mod = 0.0
    if "abortion" in issues:
        mod += 0.03 if candidate in {"Haley Stevens", "Mallory McMorrow"} else 0.02
    if "labor" in issues or "unions" in issues:
        mod += 0.03 if candidate in {"Haley Stevens", "Abdul El-Sayed"} else 0.01
    if "social security" in issues or "medicare" in issues or "health" in issues:
        mod += 0.04 if candidate == "Abdul El-Sayed" else 0.01
    if "economy" in issues or "cost of living" in issues:
        mod -= 0.015
    if "immigration" in issues or "crime" in issues or "border" in issues:
        mod -= 0.04
    if "environment" in issues or "water" in issues:
        mod += 0.02 if candidate in {"Haley Stevens", "Mallory McMorrow"} else 0.01
    if "israel" in issues or "foreign policy" in issues:
        mod += 0.02 if candidate == "Haley Stevens" else -0.015
    return mod


def candidate_fit_mod(persona: dict, candidate: str) -> float:
    ideology = persona["ideology"]
    party = persona["party_lean"]
    age = persona["age_group"]
    gender = persona["gender"]
    area = persona["urban_suburban_rural"]
    county = persona["county"]
    education = persona["education"]

    if candidate == "Abdul El-Sayed":
        mod = {
            "Progressive": 0.08,
            "Liberal": 0.03,
            "Moderate": -0.035,
            "Conservative": -0.075,
            "Very conservative": -0.10,
        }[ideology]
        if age == "18-29":
            mod += 0.03
        if age == "65+":
            mod -= 0.02
        if county in {"Wayne County", "Washtenaw County"}:
            mod += 0.025
        if area in {"rural", "rural/small-town"}:
            mod -= 0.025
        if party == "Independent / swing":
            mod -= 0.025
        return mod

    if candidate == "Haley Stevens":
        mod = {
            "Progressive": -0.015,
            "Liberal": 0.02,
            "Moderate": 0.055,
            "Conservative": 0.02,
            "Very conservative": -0.015,
        }[ideology]
        if county in {"Oakland County", "Macomb County", "Kent County"}:
            mod += 0.035
        if area == "suburban":
            mod += 0.025
        if education in {"College degree", "Postgraduate"}:
            mod += 0.01
        if party == "Independent / swing":
            mod += 0.02
        return mod

    if candidate == "Mallory McMorrow":
        mod = {
            "Progressive": 0.04,
            "Liberal": 0.04,
            "Moderate": 0.005,
            "Conservative": -0.055,
            "Very conservative": -0.08,
        }[ideology]
        if gender == "Female":
            mod += 0.02
        if age in {"18-29", "30-44"}:
            mod += 0.02
        if county in {"Oakland County", "Washtenaw County", "Ingham County"}:
            mod += 0.025
        if area in {"rural", "rural/small-town"}:
            mod -= 0.03
        if party == "Independent / swing":
            mod -= 0.005
        return mod

    raise ValueError(f"Unknown candidate: {candidate}")


def undecided_window(persona: dict) -> float:
    window = 0.045
    if persona["party_lean"] == "Independent / swing":
        window += 0.035
    if persona["ideology"] == "Moderate":
        window += 0.015
    if persona["turnout_likelihood"] == "Medium":
        window += 0.01
    if persona["turnout_likelihood"] == "Low":
        window += 0.02
    return window


def undecided_reason(persona: dict, matchup: dict, score: float) -> str:
    issues = persona["top_issues"].lower()
    if persona["turnout_likelihood"] == "Low":
        return "turnout uncertainty"
    if persona["party_lean"] == "Independent / swing" and persona["ideology"] == "Moderate":
        return "persuadable moderate"
    if "economy" in issues or "cost of living" in issues:
        return "issue conflict"
    if persona["party_lean"] in {"Lean Democrat", "Lean Republican"}:
        return "party conflict"
    if abs(score - 0.50) < 0.03:
        return "low candidate familiarity"
    return "dislikes both options"


def dem_score(persona: dict, candidate: str, run_index) -> float:
    score = BASE_DEM_SCORE[persona["party_lean"]]
    score += IDEOLOGY_DEM_MOD[persona["ideology"]]
    score += COUNTY_DEM_MOD.get(persona["county"], 0.0)
    score += 0.015 if persona["urban_suburban_rural"] == "urban" else 0.0
    score += -0.015 if persona["urban_suburban_rural"] == "rural" else 0.0
    score += candidate_fit_mod(persona, candidate)
    score += issue_mod(persona, candidate)
    score += stable_variation(persona["persona_id"], candidate, "matchup")
    score += stable_variation(persona["persona_id"], candidate, str(run_index), width=0.055)
    return max(0.01, min(0.99, score))


def prompt_payload(persona: dict, matchup: dict, run_index, trial_run) -> dict:
    return {
        "system": "Answer as the given Michigan voter persona. Do not use polling toplines. Return strict JSON.",
        "persona": {field: persona[field] for field in PERSONA_FIELDS if field in persona},
        "question": matchup["question"],
        "options": [matchup["democrat"], matchup["republican"], "Undecided"],
        "trial_run": trial_run,
        "inner_run": run_index,
    }


def local_persona_answer(persona: dict, matchup: dict, run_index, trial_run, prompt_id: str) -> dict:
    score = dem_score(persona, matchup["democrat"], f"{trial_run}:{run_index}")
    distance = abs(score - 0.50)

    if distance <= undecided_window(persona):
        answer = "Undecided"
        reason = undecided_reason(persona, matchup, score)
        confidence = 1.0 - min(0.49, distance)
        rationale = (
            f"{persona['first_name']} is undecided because their {persona['party_lean'].lower()} and {persona['ideology'].lower()} profile does not clearly resolve this matchup, "
            f"especially given concerns about {issue_text(persona)} and living in {persona['county']}."
        )
    elif score > 0.50:
        answer = matchup["democrat"]
        reason = ""
        confidence = 0.50 + distance
        rationale = (
            f"{persona['first_name']}'s {persona['party_lean'].lower()} and {persona['ideology'].lower()} profile points more toward "
            f"{matchup['democrat']}, especially given concerns about {issue_text(persona)} and living in {persona['county']}."
        )
    else:
        answer = matchup["republican"]
        reason = ""
        confidence = 0.50 + distance
        rationale = (
            f"{persona['first_name']}'s {persona['party_lean'].lower()} and {persona['ideology'].lower()} profile points more toward "
            f"Mike Rogers, especially given concerns about {issue_text(persona)} and living in {persona['county']}."
        )

    return {
        "selected_answer": answer,
        "rationale": rationale,
        "confidence": round(confidence, 2),
        "undecided_reason": reason,
        "model": MODEL_NAME,
        "temperature": TEMPERATURE,
        "response_engine": "local_persona_engine",
        "prompt_hash": prompt_id,
    }


def matchup_answer(persona: dict, matchup: dict, run_index, trial_run=1) -> dict:
    prompt = prompt_payload(persona, matchup, run_index, trial_run)
    prompt_id = stable_hash(prompt)
    return local_persona_answer(persona, matchup, run_index, trial_run, prompt_id)


def load_personas() -> list[dict]:
    with PERSONAS_PATH.open(newline="") as f:
        personas = list(csv.DictReader(f))
    apply_persona_weights(personas)
    return personas


def apply_persona_weights(personas: list[dict]) -> None:
    counts = {
        field: Counter(persona[field] for persona in personas)
        for field in WEIGHT_TARGETS
    }
    total = len(personas)
    raw_weights = []
    for persona in personas:
        weight = 1.0
        for field, targets in WEIGHT_TARGETS.items():
            current_share = counts[field][persona[field]] / total
            target_share = targets.get(persona[field], current_share)
            weight *= target_share / current_share
        raw_weights.append(weight)

    mean_weight = sum(raw_weights) / len(raw_weights)
    for persona, weight in zip(personas, raw_weights):
        persona["persona_weight"] = f"{weight / mean_weight:.6f}"


def choose_modal_answer(question_rows: list[dict]) -> tuple[str, int]:
    counts = Counter(row["selected_answer"] for row in question_rows)
    top_count = max(counts.values())
    tied = [answer for answer, count in counts.items() if count == top_count]
    if len(tied) == 1:
        return tied[0], top_count
    average_confidence = {
        answer: sum(float(row["confidence"]) for row in question_rows if row["selected_answer"] == answer)
        / counts[answer]
        for answer in tied
    }
    return max(tied, key=lambda answer: average_confidence[answer]), top_count


def build_trial_run(personas: list[dict], trial_run: int, method: str) -> tuple[list[dict], list[dict], list[dict]]:
    raw_rows = []
    final_long_rows = []
    final_wide_rows = []

    for persona in personas:
        persona_raw_rows = []
        for inner_run in range(1, RUNS_PER_PERSONA + 1):
            for matchup in MATCHUPS:
                response = matchup_answer(persona, matchup, inner_run, trial_run)
                row = {
                    "method": method,
                    "trial_run": trial_run,
                    "persona_id": persona["persona_id"],
                    "inner_run": inner_run,
                    "question_id": matchup["id"],
                    "selected_answer": response["selected_answer"],
                    "confidence": response["confidence"],
                    "undecided_reason": response["undecided_reason"],
                    "response_engine": response["response_engine"],
                    "model": response["model"],
                    "temperature": response["temperature"],
                    "prompt_hash": response["prompt_hash"],
                    "rationale": response["rationale"],
                    "raw_response_json": json.dumps(response, sort_keys=True),
                    "matchup": f"{matchup['democrat']} vs {matchup['republican']}",
                    "question_text": matchup["question"],
                }
                raw_rows.append(row)
                persona_raw_rows.append(row)

        wide = {field: persona[field] for field in PERSONA_FIELDS}
        wide["method"] = method
        wide["trial_run"] = trial_run
        wide["runs_per_persona"] = RUNS_PER_PERSONA

        for matchup in MATCHUPS:
            question_rows = [row for row in persona_raw_rows if row["question_id"] == matchup["id"]]
            counts = Counter(row["selected_answer"] for row in question_rows)
            undecided_reasons = Counter(
                row["undecided_reason"] for row in question_rows if row["undecided_reason"]
            )
            modal_answer, modal_count = choose_modal_answer(question_rows)
            modal_row = next(row for row in question_rows if row["selected_answer"] == modal_answer)
            modal_share = round(modal_count / RUNS_PER_PERSONA, 2)

            final_long_rows.append(
                {
                    **{field: persona[field] for field in PERSONA_FIELDS},
                    "method": method,
                    "trial_run": trial_run,
                    "runs_per_persona": RUNS_PER_PERSONA,
                    "question_id": matchup["id"],
                    "question_text": matchup["question"],
                    "matchup": modal_row["matchup"],
                    "selected_answer": modal_answer,
                    "modal_count": modal_count,
                    "modal_share": modal_share,
                    "run_answer_counts": json.dumps(dict(sorted(counts.items())), sort_keys=True),
                    "undecided_reason": modal_row["undecided_reason"] if modal_answer == "Undecided" else "",
                    "undecided_reason_counts": json.dumps(dict(sorted(undecided_reasons.items())), sort_keys=True),
                    "rationale": modal_row["rationale"],
                    "response_engine": modal_row["response_engine"],
                    "model": modal_row["model"],
                    "temperature": modal_row["temperature"],
                    "prompt_hash": modal_row["prompt_hash"],
                }
            )
            wide[f"{matchup['key']}_answer"] = modal_answer
            wide[f"{matchup['key']}_modal_count"] = modal_count
            wide[f"{matchup['key']}_modal_share"] = modal_share
            wide[f"{matchup['key']}_run_answer_counts"] = json.dumps(
                dict(sorted(counts.items())), sort_keys=True
            )
            wide[f"{matchup['key']}_undecided_reason"] = modal_row["undecided_reason"] if modal_answer == "Undecided" else ""

        final_wide_rows.append(wide)

    return raw_rows, final_long_rows, final_wide_rows
