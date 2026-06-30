# Trial 001: Michigan Senate General Electorate

This folder contains the 100-person Michigan likely-voter persona trial.

For the full explanation of the project, methods, run-size check, and limitations, see the top-level `README.md`.

## Files

- `michigan_likely_voter_personas_100.csv`: final 100-person persona table
- `michigan_likely_voter_personas_100.json`: same personas as JSON
- `michigan_likely_voter_persona_demographic_summary.json`: demographic counts for the persona file
- `michigan_senate_persona_model.py`: persona scoring and repeated-answer logic
- `run_michigan_senate_1000_trial_aggregate.py`: main script that runs the 1,000-trial aggregate
- `results/`: generated result files

## Run

```bash
python3 persona_trials/trial_001_general_electorate/run_michigan_senate_1000_trial_aggregate.py
```
