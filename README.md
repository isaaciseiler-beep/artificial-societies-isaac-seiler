# Artificial Societies Michigan Senate Trial

This experiment tests which Democratic candidate looks strongest against Mike Rogers in a likely 2026 Michigan U.S. Senate general election.

I modeled likely Michigan general-election voters, not Democratic primary voters. The goal was to test general election viability of the leading Democratic candidates.

## Why Michigan

I chose Michigan because I have worked in Michigan politics and saw how hard it is to get useful public opinion data. Private polling is expensive, and smaller campaigns often either spend a large share of their budget on it or go without it. Artificial Societies solves a problem I've experienced in the field: and I wanted to use my domain expertise to put the concept of synthetic polling into action.

For context on the current status of the race, check out these articles:

[Michigan’s U.S. Senate primary highlights divisions within Democratic Party, _Michigan Advance_
]([url](https://michiganadvance.com/2026/06/09/stevens-mcmorrow-el-sayed-clash-over-foreign-policy-party-leadership-as-primary-approaches/?utm_source=chatgpt.com&__cf_chl_f_tk=QDSv4YBHDQoeefRidAgClIaXDmdKHLUzs01UUaRgC9Y-1782798991-1.0.1.1-GSM0auWIIQ_kYpMsuLXQnYXvlMYwap7xHPChDjXdIec))

[Ballotpedia Overview]([url](https://ballotpedia.org/United_States_Senate_election_in_Michigan%2C_2026_%28August_4_Democratic_primary%29?))

## Main Finding

The model points to Haley Stevens as the strongest general-election candidate.

- Stevens performs best against Rogers.
- McMorrow is close to Rogers, but with the largest undecided pool.
- El-Sayed performs weakest against Rogers in this general-election electorate.

This is not a primary forecast. El-Sayed may be strong with Democratic primary voters while still looking weaker with a broader general electorate.

## Survey Questions

Each persona answered these single-select questions:

1. If the general election for Michigan's 2026 U.S. Senate race were held today and the candidates were Abdul El-Sayed and Mike Rogers, who would you most likely support?
2. If the general election for Michigan's 2026 U.S. Senate race were held today and the candidates were Haley Stevens and Mike Rogers, who would you most likely support?
3. If the general election for Michigan's 2026 U.S. Senate race were held today and the candidates were Mallory McMorrow and Mike Rogers, who would you most likely support?

Each question allowed the Democrat, Mike Rogers, or `Undecided`.

## How The Personas Were Built

I started with 100 personas modeled after Michigan.

The final persona file is calibrated by GPT 5.5 Codex to a likely general-election electorate:

- Age: 14 aged 18-29, 21 aged 30-44, 37 aged 45-64, 28 aged 65+
- Race/ethnicity: 78 White non-Hispanic, 13 Black, 5 Hispanic, 1 Asian, 3 multiracial/other
- Gender: 54 female, 46 male

Data used to model population:

- Census and ACS (American Community Survey) data for population, county, age, race, gender, education, and income context
- Recent Michigan Senate exit polls to adjust from full population toward likely voters
- Election returns and geography to make county and region choices more realistic
- Candidate materials, local reporting, FEC data, and issue context to shape candidate fit

The source files are not tracked in git because they consist of large PDFs, ZIPs, and spreadsheets. This repository features the code, personas, results, and documentation.

Each persona has a name, county, region, age, race/ethnicity, gender, education, income band, party lean, ideology, past voting pattern, turnout likelihood, top issues, and a short profile. All of these demographics across all 100 personas are tailored to match the statewide population.

## A Note on Weighting

I initially tried weighting because a 100-person sample can drift quickly.

The problem was that with only 100 personas, weights could end up influencing the end outcome too much. Instead of relying on heavy weights, I adjusted the raw 100-person file to match the target electorate upfront. 

## How The Run Works

The main run uses:

```text
100 personas
x 3 matchup questions (listed above)
x 10 repeated answers per persona-question (most common answer is counted as the persona response)
x 1,000 trial runs
= 3,000,000 question-level simulated responses
```

For each persona-question pair, the persona answers 10 times. The most common answer becomes that persona's answer for that trial. This, in theory, controls outliers without changing the persona set.

I utilized this approach because I wanted to correct for potential outliers, twice: first at the 

## Determining Optimal Run Size

I tested smaller and larger versions of the same experiment. These runs use the same personas and questions, but different trial counts. They also use separate trial-id ranges, so they are independent experiments.

| Size | Trial runs | Question-level runs | El-Sayed margin | Stevens margin | McMorrow margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| 10% current | 100 | 300,000 | -6.5 | +17.4 | 0.0 |
| Current | 1,000 | 3,000,000 | -6.6 | +17.7 | -0.2 |
| 1000% current | 10,000 | 30,000,000 | -6.6 | +17.7 | -0.1 |
| 10000% current | 100,000 | 300,000,000 | -6.6 | +17.7 | -0.1 |

The 1,000-run version is my preferred version because it is much cheaper and less time intensive than the very large runs and already stable. The largest run, featuring 300,000,000 question-level runs, took over 75 minutes to complete. Going from 10,000 to 100,000 runs did not change the one-decimal margins, and does not meaningfully alter the results.

## Testing Repeatability

I also ran two additional full-size checks after the initial 1,000-trial run. These runs were isolated and not influenced by the initial output files.

| Run | Trial runs | Question-level runs | El-Sayed margin | Stevens margin | McMorrow margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Initial current run | 1,000 | 3,000,000 | -6.6 | +16.4 | -0.3 |
| Independent A | 1,000 | 3,000,000 | -6.6 | +16.5 | -0.3 |
| Independent B | 1,000 | 3,000,000 | -6.6 | +16.6 | -0.3 |

These results are repeatable within a slim margin. Across three independent full-size runs, the El-Sayed and McMorrow margins are unchanged at one-decimal precision, and the Stevens margin moves only from +16.4 to +16.6. The data produced by the additional runs support the core data.

## Polling Comparison

Real-world polling is not used in the dataset that informs persona answers. It is only used afterward as a check.

| Matchup | 10000% run | RCP margin | Detroit Chamber margin |
| --- | ---: | ---: | ---: |
| El-Sayed vs Rogers | -6.6 | +0.3 | -4.9 |
| Stevens vs Rogers | +17.7 | +0.4 | -2.3 |
| McMorrow vs Rogers | -0.1 | -0.4 | -2.1 |

The model is closest to polling on McMorrow, somewhat close to Detroit Chamber on El-Sayed, and much more bullish on Stevens than either polling source.

## Iteration

The work moved through a few stages:

1. Built an initial 100-person Michigan electorate.
2. Ran the three head-to-head survey questions.
3. Tried weighting, then moved away from relying on it because the sample size was only 100.
4. Rebuilt the persona file to better match the electorate upfront.
5. Switched from full-population targets to likely-voter targets using Senate exit polls.
6. Removed polling from the response inputs and kept it only for validation.
7. Ran size checks from 300,000 to 300,000,000 question-level responses.

## Important Limitation

The personas are built from public data, not real voter interviews.

Census, ACS, election returns, local reporting, candidate positions, and FEC data create useful context, but they cannot fully replace a high-quality voter panel or recent Michigan-specific survey data. If I had more time or access, I would add interviews with real Michigan voters and use those to improve the profiles.

I also saw one major LLM failure during iteration: when polling was present in the working context, the assistant sometimes tried to steer the model toward what looked like the "correct" polling answer. I removed polling from the persona-response side and kept it only as a final validation check.

## Conclusion

Results generated by the 100 synthetic personas diverge sharply from the limited public polling available, but I believe that's what makes them worth at least considering.

This experiment attempts to measure a voting population that is becoming increasingly difficult to measure accurately. Traditional political polling in the United States has grown less reliable over the last decade, often depending on substantial weighting to account for underrepresented populations that are unreachable via traditional mechanisms. That challenge is even more pronounced for polling below the presidential level, where public polling is sparse, public awareness is low, and results can be inaccurate even when produced by reputable pollsters.

Given the size of the gap between results and the public data, I would want to test a much larger synthetic sample before making stronger claims. I would also have more confidence in the synthetic result if the quantitative outputs were supplemented with qualitative data from real Michigan voters.

## Run

```bash
python3 persona_trials/trial_001_general_electorate/run_persona_trial_1000x.py
```

Generated outputs are written to `persona_trials/trial_001_general_electorate/results/`.

## Main Files

- `Data/`: source dataset
- `Data/`: raw source dataset, kept locally and ignored by git because of file size
- `persona_trials/trial_001_general_electorate/personas_100.csv`: final 100-person persona file
- `persona_trials/trial_001_general_electorate/personas_100.json`: same personas as JSON
- `persona_trials/trial_001_general_electorate/run_persona_trial.py`: persona scoring and trial logic
- `persona_trials/trial_001_general_electorate/run_persona_trial_1000x.py`: main aggregate runner and polling comparison
- `persona_trials/trial_001_general_electorate/results/EXPERIMENT_SIZE_COMPARISON.md`: run-size comparison
