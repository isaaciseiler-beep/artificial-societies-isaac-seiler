# Trial 001: Michigan General Electorate

This trial models likely Michigan general-election voters and asks which Democrat looks strongest against Mike Rogers.

## Result In One Line

Stevens looks strongest. El-Sayed looks weakest. McMorrow is competitive, but her matchup has the most undecided voters.

## Voter Group

This is a likely general-election electorate, not a Democratic primary electorate.

I started from the population of Michigan, then adjusted toward likely voters. Recent Michigan Senate exit polls are the main guide because the decision is about beating Rogers in November. Census and ACS data are used as a check on county, education, income, and population balance.

## Persona Setup

- 100 personas total
- 3 single-select matchup questions
- `Undecided` included as an answer
- 10 responses per persona per question
- 1000 aggregate trial runs

## Methods Used

1. Demographic scaffold
   - The 100-person file is modeled after Michigan, then calibrated to likely-voter targets for age, race, and gender.
   - Current weights are all `1.000000`, so the model is not leaning on reweighting.

2. Human profile layer
   - Each persona has county, region, education, income, party lean, ideology, voting history, turnout likelihood, top issues, and a short profile.
   - The point is to make the personas specific enough to behave differently, without pretending they are real people.

3. Repeated-answer simulation
   - Each persona answers each matchup 10 times with stable variation.
   - The modal answer becomes that persona's answer for that trial.
   - The full process repeats 1000 times.

4. Size check
   - I also ran 100, 1000, 10000, and 100000 trial-run versions.
   - The 1000-run version was already stable against the larger runs.
   - That is why the main runner uses 1000 runs instead of the much slower 10000 or 100000 versions.

## Iteration

- First, I built a 100-person Michigan electorate and ran the matchups.
- Then I checked the personas against the demographic files in the repo.
- I found that a full-population target was not quite right for a likely general electorate.
- I moved the targets toward recent Senate exit polls.
- I tested run size to make sure the result was not just noise from too few runs.
- I kept the weighting code, but changed the persona file so the weights are all flat.

## Weighting

The code still calculates weights for age, race, and gender.

The final persona file already matches the targets:

- Age: 14 aged 18-29, 21 aged 30-44, 37 aged 45-64, 28 aged 65+
- Race/ethnicity: 78 White non-Hispanic, 13 Black, 5 Hispanic, 1 Asian, 3 multiracial/other
- Gender: 54 female, 46 male

Because the file matches the targets directly, every persona has `persona_weight = 1.000000`. Weighted and unweighted results are identical.

## Polling Check

Polling is not used to answer the survey questions.

After the run, the script compares the persona margins against RCP and Detroit Chamber polling. This is the main external check on whether the simulated electorate is directionally reasonable.

## Files

- `personas_100.csv`: persona table
- `personas_100.json`: same personas as structured JSON
- `run_persona_trial.py`: persona scoring and trial logic
- `run_persona_trial_1000x.py`: aggregate runner and polling comparison
- `results/`: generated outputs after a run

## Run

```bash
python3 persona_trials/trial_001_general_electorate/run_persona_trial_1000x.py
```
