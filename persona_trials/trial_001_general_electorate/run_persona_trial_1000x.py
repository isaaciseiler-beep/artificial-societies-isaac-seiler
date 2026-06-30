import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import run_persona_trial as base


TRIAL_RUNS = 1000
METHOD = "poll_excluded_1000x_10x_modal_with_undecided"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


RCP_AVERAGES = {
    "q1_elsayed_vs_rogers": {
        "Abdul El-Sayed": 43.3,
        "Mike Rogers": 43.0,
        "unallocated": 13.7,
        "margin": 0.3,
    },
    "q2_stevens_vs_rogers": {
        "Haley Stevens": 43.7,
        "Mike Rogers": 43.3,
        "unallocated": 13.0,
        "margin": 0.4,
    },
    "q3_mcmorrow_vs_rogers": {
        "Mallory McMorrow": 42.3,
        "Mike Rogers": 42.7,
        "unallocated": 15.0,
        "margin": -0.4,
    },
}


DETROIT_CHAMBER = {
    "q1_elsayed_vs_rogers": {
        "Abdul El-Sayed": 39.8,
        "Mike Rogers": 44.7,
        "Undecided": 15.5,
        "margin": -4.9,
    },
    "q2_stevens_vs_rogers": {
        "Haley Stevens": 41.5,
        "Mike Rogers": 43.8,
        "Undecided": 14.7,
        "margin": -2.3,
    },
    "q3_mcmorrow_vs_rogers": {
        "Mallory McMorrow": 40.7,
        "Mike Rogers": 42.8,
        "Undecided": 16.5,
        "margin": -2.1,
    },
}


def new_bucket():
    return {"count": Counter(), "weight": defaultdict(float)}


def add_row(bucket, row):
    answer = row["selected_answer"]
    bucket["count"][answer] += 1
    bucket["weight"][answer] += float(row["persona_weight"])


def summarize_bucket(bucket):
    total = sum(bucket["count"].values()) or 1
    weighted_total = sum(bucket["weight"].values()) or 1
    answers = sorted(bucket["count"], key=lambda answer: (-bucket["count"][answer], answer))
    return {
        answer: {
            "count": bucket["count"][answer],
            "pct": round(bucket["count"][answer] / total * 100, 1),
            "weighted_count": round(bucket["weight"][answer], 2),
            "weighted_pct": round(bucket["weight"][answer] / weighted_total * 100, 1),
        }
        for answer in answers
    }


def margin_for(question_id, summary):
    matchup = next(item for item in base.MATCHUPS if item["id"] == question_id)
    dem = matchup["democrat"]
    dem_pct = summary.get(dem, {}).get("pct", 0)
    rep_pct = summary.get("Mike Rogers", {}).get("pct", 0)
    dem_weighted = summary.get(dem, {}).get("weighted_pct", 0)
    rep_weighted = summary.get("Mike Rogers", {}).get("weighted_pct", 0)
    return {
        "candidate": dem,
        "margin": round(dem_pct - rep_pct, 1),
        "weighted_margin": round(dem_weighted - rep_weighted, 1),
    }


def write_csv(path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_results_readme(summary):
    lines = [
        "# Trial 001 Results",
        "",
        "This is a 1000-run simulation of likely Michigan general-election voters.",
        "",
        "The main read: Stevens looks strongest against Rogers. El-Sayed looks weakest. McMorrow is close to Rogers, but with the largest undecided group.",
        "",
        "This is not a poll. Polling is not used in the persona answers. It is only used afterward as a check.",
        "",
        "## Full Results",
        "",
    ]
    for matchup in base.MATCHUPS:
        question_id = matchup["id"]
        lines.extend([f"### {question_id}", ""])
        for answer, stats in summary["full_results"][question_id].items():
            lines.append(
                f"- {answer}: {stats['pct']}% unweighted; {stats['weighted_pct']}% weighted"
            )
        lines.append("")

    lines.extend(["## Decided-Voter Results", ""])
    for matchup in base.MATCHUPS:
        question_id = matchup["id"]
        lines.extend([f"### {question_id}", ""])
        for answer, stats in summary["decided_voter_results"][question_id].items():
            lines.append(
                f"- {answer}: {stats['pct']}% unweighted; {stats['weighted_pct']}% weighted"
            )
        lines.append("")

    lines.extend(["## Polling Check", ""])
    lines.append("These are the persona margins compared with the held-out polling references in the dataset.")
    lines.append("")
    for row in summary["polling_comparison"]:
        lines.append(
            f"- {row['matchup']}: weighted persona margin {row['weighted_persona_margin']}; RCP margin {row['rcp_margin']}; Detroit Chamber margin {row['detroit_chamber_margin']}"
        )
    lines.append("")
    (RESULTS_DIR / "README_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def write_polling_comparison(summary):
    lines = [
        "# Polling Check",
        "",
        "This is the external check on the simulation.",
        "",
        "Polling was not included in persona responses. The model answers first, then this file compares those answers with RCP and Detroit Chamber polling.",
        "",
        "The comparison is useful because it shows where the persona model lines up with public polling and where it may be too soft or too hard on a candidate.",
        "",
        "| Matchup | Weighted persona | RCP average | Detroit Chamber | Read |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in summary["polling_comparison"]:
        lines.append(
            f"| {row['matchup']} | {row['weighted_persona_result']} | {row['rcp_result']} | {row['detroit_chamber_result']} | {row['read']} |"
        )
    lines.append("")
    lines.append("Bottom line: Stevens is the clearest general-election profile in this model. El-Sayed is the weakest. McMorrow is close to Rogers, but the high undecided share means I would not overread that matchup.")
    lines.append("")
    (RESULTS_DIR / "POLLING_COMPARISON.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    personas = base.load_personas()
    full = defaultdict(new_bucket)
    decided = defaultdict(new_bucket)
    subgroup = defaultdict(new_bucket)
    undecided_reasons = defaultdict(Counter)

    for trial_run in range(1, TRIAL_RUNS + 1):
        _, final_long_rows, _ = base.build_trial_run(personas, trial_run, METHOD)
        for row in final_long_rows:
            question_id = row["question_id"]
            add_row(full[question_id], row)
            if row["selected_answer"] != "Undecided":
                add_row(decided[question_id], row)
            else:
                undecided_reasons[question_id][row["undecided_reason"]] += 1
            for field in base.SUBGROUP_FIELDS:
                add_row(subgroup[(field, row[field], question_id)], row)

    summary = {
        "method": METHOD,
        "trial_runs": TRIAL_RUNS,
        "persona_count": len(personas),
        "runs_per_persona_per_trial": base.RUNS_PER_PERSONA,
        "persona_level_runs": len(personas) * TRIAL_RUNS * base.RUNS_PER_PERSONA,
        "question_level_runs": len(personas) * TRIAL_RUNS * base.RUNS_PER_PERSONA * len(base.MATCHUPS),
        "polling_used_in_response_model": False,
        "full_results": {},
        "decided_voter_results": {},
        "polling_comparison": [],
    }

    for matchup in base.MATCHUPS:
        question_id = matchup["id"]
        full_summary = summarize_bucket(full[question_id])
        decided_summary = summarize_bucket(decided[question_id])
        summary["full_results"][question_id] = full_summary
        summary["decided_voter_results"][question_id] = decided_summary
        margin = margin_for(question_id, full_summary)
        rcp = RCP_AVERAGES[question_id]
        chamber = DETROIT_CHAMBER[question_id]
        und = full_summary.get("Undecided", {}).get("weighted_pct", 0)
        read = "weaker than polling for Democrat"
        if margin["weighted_margin"] > rcp["margin"] + 5:
            read = "stronger than polling for Democrat"
        elif abs(margin["weighted_margin"] - rcp["margin"]) <= 5:
            read = "broadly close to polling"
        summary["polling_comparison"].append(
            {
                "matchup": f"{matchup['democrat']} vs Mike Rogers",
                "weighted_persona_margin": margin["weighted_margin"],
                "rcp_margin": rcp["margin"],
                "detroit_chamber_margin": chamber["margin"],
                "weighted_persona_result": f"{matchup['democrat']} {full_summary.get(matchup['democrat'], {}).get('weighted_pct', 0)} / Rogers {full_summary.get('Mike Rogers', {}).get('weighted_pct', 0)} / Undecided {und}",
                "rcp_result": f"{matchup['democrat']} {rcp[matchup['democrat']]} / Rogers {rcp['Mike Rogers']} / Unallocated {rcp['unallocated']}",
                "detroit_chamber_result": f"{matchup['democrat']} {chamber[matchup['democrat']]} / Rogers {chamber['Mike Rogers']} / Undecided {chamber['Undecided']}",
                "read": read,
            }
        )

    subgroup_rows = []
    for (field, value, question_id), bucket in sorted(subgroup.items()):
        for answer, stats in summarize_bucket(bucket).items():
            subgroup_rows.append(
                {
                    "subgroup_field": field,
                    "subgroup_value": value,
                    "question_id": question_id,
                    "selected_answer": answer,
                    **stats,
                }
            )

    reason_rows = []
    for question_id, counts in sorted(undecided_reasons.items()):
        total = sum(counts.values()) or 1
        for reason, count in counts.most_common():
            reason_rows.append(
                {
                    "question_id": question_id,
                    "undecided_reason": reason,
                    "count": count,
                    "pct_of_undecided": round(count / total * 100, 1),
                }
            )

    (RESULTS_DIR / "trial_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (RESULTS_DIR / "run_config.json").write_text(
        json.dumps({k: v for k, v in summary.items() if k not in {"full_results", "decided_voter_results", "polling_comparison"}}, indent=2),
        encoding="utf-8",
    )
    write_csv(RESULTS_DIR / "subgroup_results.csv", subgroup_rows)
    write_csv(RESULTS_DIR / "undecided_reasons.csv", reason_rows)
    write_results_readme(summary)
    write_polling_comparison(summary)
    print(json.dumps(summary["full_results"], indent=2))


if __name__ == "__main__":
    main()
