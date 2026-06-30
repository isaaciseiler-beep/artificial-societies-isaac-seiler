import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import michigan_senate_persona_model as base
import run_michigan_senate_1000_trial_aggregate as aggregate


TRIAL_RUNS = 1000
METHOD_BASE = "poll_excluded_1000x_10x_modal_with_undecided"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def new_bucket():
    return {"count": Counter(), "weight": defaultdict(float)}


def write_results_readme(path: Path, summary: dict, title: str) -> None:
    lines = [
        f"# {title}",
        "",
        "Main read: Stevens strongest; El-Sayed weakest; McMorrow close with high undecided.",
        "",
        "## Full Results",
        "",
    ]
    for matchup in base.MATCHUPS:
        question_id = matchup["id"]
        lines.extend([f"### {question_id}", ""])
        for answer, stats in summary["full_results"][question_id].items():
            lines.append(f"- {answer}: {stats['pct']}%")
        lines.append("")

    lines.extend(["## Decided-Voter Results", ""])
    for matchup in base.MATCHUPS:
        question_id = matchup["id"]
        lines.extend([f"### {question_id}", ""])
        for answer, stats in summary["decided_voter_results"][question_id].items():
            lines.append(f"- {answer}: {stats['pct']}%")
        lines.append("")

    lines.extend(["## Polling Check", ""])
    for row in summary["polling_comparison"]:
        lines.append(
            f"- {row['matchup']}: persona margin {row['weighted_persona_margin']}; RCP margin {row['rcp_margin']}; Detroit Chamber margin {row['detroit_chamber_margin']}"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run(label: str, start_trial_run: int) -> dict:
    RESULTS_DIR.mkdir(exist_ok=True)
    method = f"{METHOD_BASE}_{label}"
    end_trial_run = start_trial_run + TRIAL_RUNS - 1
    personas = base.load_personas()
    full = defaultdict(new_bucket)
    decided = defaultdict(new_bucket)
    subgroup = defaultdict(new_bucket)
    undecided_reasons = defaultdict(Counter)

    for trial_run in range(start_trial_run, end_trial_run + 1):
        _, final_long_rows, _ = base.build_trial_run(personas, trial_run, method)
        for row in final_long_rows:
            question_id = row["question_id"]
            aggregate.add_row(full[question_id], row)
            if row["selected_answer"] != "Undecided":
                aggregate.add_row(decided[question_id], row)
            else:
                undecided_reasons[question_id][row["undecided_reason"]] += 1
            for field in base.SUBGROUP_FIELDS:
                aggregate.add_row(subgroup[(field, row[field], question_id)], row)

    summary = {
        "method": method,
        "trial_runs": TRIAL_RUNS,
        "trial_run_start": start_trial_run,
        "trial_run_end": end_trial_run,
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
        full_summary = aggregate.summarize_bucket(full[question_id])
        decided_summary = aggregate.summarize_bucket(decided[question_id])
        summary["full_results"][question_id] = full_summary
        summary["decided_voter_results"][question_id] = decided_summary
        margin = aggregate.margin_for(question_id, full_summary)
        rcp = aggregate.RCP_AVERAGES[question_id]
        chamber = aggregate.DETROIT_CHAMBER[question_id]
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
        for answer, stats in aggregate.summarize_bucket(bucket).items():
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

    prefix = f"current_1000_run_{label}"
    (RESULTS_DIR / f"{prefix}_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (RESULTS_DIR / f"{prefix}_config.json").write_text(
        json.dumps({k: v for k, v in summary.items() if k not in {"full_results", "decided_voter_results", "polling_comparison"}}, indent=2),
        encoding="utf-8",
    )
    aggregate.write_csv(RESULTS_DIR / f"{prefix}_subgroup_results.csv", subgroup_rows)
    aggregate.write_csv(RESULTS_DIR / f"{prefix}_undecided_reasons.csv", reason_rows)
    write_results_readme(RESULTS_DIR / f"{prefix}_results_summary.md", summary, f"Current 1,000-Run Results {label}")
    return summary


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 run_michigan_senate_independent_1000_trial_aggregate.py <label> <start_trial_run>")
    label = sys.argv[1]
    if not label.replace("_", "").replace("-", "").isalnum():
        raise SystemExit("Label must contain only letters, numbers, hyphens, or underscores.")
    summary = run(label, int(sys.argv[2]))
    print(json.dumps({k: summary[k] for k in ("method", "trial_runs", "trial_run_start", "trial_run_end", "question_level_runs")}, indent=2))


if __name__ == "__main__":
    main()
