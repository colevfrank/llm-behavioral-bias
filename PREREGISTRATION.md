# Preregistration

**Project:** LLM Behavioral Perturbations — Testing whether LLM "behavioral 
biases" are stable preferences or artifacts of autoregressive training dynamics

**Author:** Cole Frank

**Date committed:** 4/22/2026

**Status:** Preregistered — no data collected at time of commit.

---

## 1. Research question

Do LLMs exhibit stable behavioral biases analogous to human cognitive biases, or 
do their responses to canonical behavioral economics scenarios reflect 
autoregressive probability patterns that collapse under perturbation of 
surface features?

## 2. Theoretical framework

Following McCoy et al. (2023), LLM outputs are hypothesized to be sensitive 
to (a) task frequency in training data, (b) input probability, and 
(c) output token probability. Bini et al. (2025) document "behavioral biases" 
in LLM responses to canonical behavioral economics experiments without 
controlling for these autoregressive confounds. This study tests whether 
the effects Bini et al. attribute to preference structure are instead 
artifacts of surface-feature probability.

## 3. Hypotheses

**H1 (probability swamping):** For each of the four experiments studied, 
response distributions under perturbation conditions (A, B, C) will differ 
significantly from the canonical condition (0) in the direction of reduced 
human-like response rates.

*Directional prediction:* `p(human_like | perturbed) < p(human_like | canonical)`

*Operationalization of "swamping":* A perturbation swamps the behavioral 
effect if `|p_perturbed − p_canonical| ≥ |p_canonical − 0.5|`. A perturbation 
that does not swamp but produces a significant shift is interpreted as partial 
attenuation of the behavioral effect.

**H2 (task frequency confound):** Each perturbation condition (A, B, C) 
produces response distributions that differ significantly from the canonical 
condition (0) within each experiment. No directional prediction is made 
about the relative magnitudes of effects across conditions A, B, C; the 
theory does not specify which surface features the model is most sensitive to.

## 4. Design

**Model:** Claude Opus 4.7 (`claude-opus-4-7`), accessed via Anthropic API.

**Factors:**
- Experiment (4 levels): Q1 diminishing sensitivity, Q4 narrow framing, 
  Q5 hyperbolic discounting, Q13 Wason selection task
- Condition (4 levels): 0 (canonical Bini prompt), A (numerical perturbation), 
  B (non-numeric token perturbation), C (experiment-specific third perturbation)

**Held constant:**
- Reasoning effort: low (Claude adaptive thinking, `effort: "low"`)
- Temperature: 0.5 (matching Bini et al.)
- top-p: 0.9; top-k: 50 (Bini defaults)
- Prompt structure: verbatim Bini format including JSON output instructions

**Sample size:** 50 responses per cell × 16 cells = 800 total responses.

**Perturbation definitions (specified ex ante):**

*Q1 — Diminishing sensitivity:*
- Condition 0: Verbatim Kahneman & Tversky 1979 / Bini prompt
- Condition A: Dollar amounts replaced ($1,000 → $1,037; $500 → $517; 
  $2,000 → $2,041). Probabilities and labels unchanged.
- Condition B: Probability 0.5 replaced with 0.47. Dollar amounts and labels unchanged.
- Condition C: Option labels "A"/"B" replaced with "the gamble"/"the certain amount." 
  Numbers unchanged.

*Q4 — Narrow framing:*
- Condition 0: Verbatim Tversky & Kahneman 1981 / Bini prompt (jacket $125 / 
  calculator $15 vs. jacket $15 / calculator $125, save $5)
- Condition A: Prices replaced ($125 → $127; $15 → $17). $5 savings preserved. 
  Objects unchanged.
- Condition B: "Jacket" and "calculator" replaced with "headphones" and "plant"
  [two objects of similar expensive/cheap character but less canonical in the KT
  tradition]. Prices unchanged.
- Condition C: Response format "Yes"/"No" replaced with "make the trip"/"don't 
  make the trip."

*Q5 — Hyperbolic discounting:*
- Condition 0: Verbatim Frederick et al. 2002 / Bini prompt ($100 today vs. 
  $110 tomorrow; $100 in 30 days vs. $110 in 31 days)
- Condition A: Dollar amounts replaced ($100 → $97; $110 → $109). Time 
  structure unchanged.
- Condition B: Option labels "A"/"B" replaced with "the sooner payment"/"the 
  later payment." Numbers unchanged.
- Condition C: Both perturbations from A and B combined.

*Q13 — Wason selection task:*
- Condition 0: Verbatim Wason / Bini prompt (cards E, K, 4, 7; rule about 
  vowels and even numbers)
- Condition A: Cards replaced with {U, M, 6, 3}. Correct answer: U and 3. 
  Rule structure unchanged.
- Condition B: Cards replaced with {I, Q, 8, 83}. Correct answer: I and 83. 
  Tests McCoy's output-probability hypothesis via low-frequency numerical token.
- Condition C: Original cards {E, K, 4, 7} retained; rule rephrased from 
  "Every card with a vowel on one side has an even number on the other side" 
  to "If a card shows a vowel on one side, then the reverse side shows an 
  even number."

## 5. Outcome variables

**Primary outcomes (binary):**
- Q1: `human_like` = (Scenario A choice == "B") AND (Scenario B choice == "A")
- Q4: `human_like` = (Scenario A choice == "Yes") AND (Scenario B choice == "No")
- Q5: `human_like` = (Scenario A choice == "A") AND (Scenario B choice == "B")
- Q13: `correct` = selected card set equals {canonical_vowel, canonical_odd} 
  for the relevant condition

**Secondary outcomes:**
- Q13: `human_like_error` = selected card set equals {canonical_vowel, 
  canonical_even} (confirmation-bias pattern)
- All experiments: Model-reported confidence level
- All experiments: Model-reported reasoning type ("A" = intuitive, "B" = analytical)
- All experiments: Token counts and latency, for cost/compute reporting

**Response exclusion:** Responses for which the parser cannot extract the 
required fields (set `parsed_ok = False`) are excluded from primary analysis. 
Exclusion rate will be reported per cell. If exclusion exceeds 10% in any 
cell, the cell's results will be flagged in the paper.

## 6. Statistical analysis plan

**Primary analysis:** One logistic regression per experiment (4 total):

`logit(P(human_like = 1)) = β₀ + β₁·condition_A + β₂·condition_B + β₃·condition_C`

- Condition 0 is the reference category
- For Q13, outcome is `correct` rather than `human_like`
- Standard (non-robust) SEs reported; within-cell independence is the 
  justifying assumption

**Hypothesis tests:**
- H1: One-sided tests on β₁, β₂, β₃ (prediction: negative). Report p-values 
  and marginal effects (percentage-point differences from condition 0).
- H2: Same tests as H1; the hypothesis is that each perturbation differs 
  from canonical, not a ranking among them.

**Swamping criterion (H1, operationalized):** A perturbation is classified 
as "swamping" the behavioral effect if the estimated proportion human_like 
(or correct) in that cell satisfies `|p̂_perturbed − p̂_canonical| ≥ 
|p̂_canonical − 0.5|`. This is descriptive, not a formal hypothesis test.

**Significance threshold:** α = 0.05, two-sided unless otherwise noted. 
No multiplicity correction across the four experiments; each is treated 
as an independent test of the same theoretical claim on different stimuli. 
Within each experiment, the three perturbation contrasts (A, B, C vs. 0) 
are interpreted jointly — consistent directional shifts across A, B, C 
constitute evidence for the framework; any single significant effect is 
weaker evidence.

## 7. Replication check (condition 0)

Before interpreting any perturbation effects, the canonical condition (0) 
results for each experiment will be compared against the proportions Bini 
et al. report for Claude 3 Opus (their closest available predecessor model). 

**Pre-specified decision rules:**
- If condition 0 proportions in the current study fall within 15 percentage 
  points of Bini's reported proportions for all four experiments: proceed 
  with the planned analysis using our own condition 0 as the baseline.
- If condition 0 proportions differ by more than 15 percentage points from 
  Bini for one or more experiments: the paper's framing shifts to 
  foreground the non-replication as itself evidence against stable 
  preference interpretation. The perturbation analysis proceeds using our 
  own condition 0 as baseline, and Bini's non-replication is reported as 
  a primary finding.
- If condition 0 shows no human-like bias at all (e.g., >50% rational 
  responses where Bini reports >50% human-like): that experiment is 
  reported as a failed replication; perturbation analyses for that 
  experiment are reported descriptively but not interpreted as evidence 
  for the autoregressive framework, since there is no behavioral effect 
  to collapse.

## 8. Deviations and amendments

**Amendment 1 — [4/22/2026]:** The original design included reasoning effort 
(low vs. high) as a second factor, producing a 4 (experiment) × 4 (condition) 
× 2 (effort) design with 1,600 responses. Due to time constraints on the 
assignment deadline, the reasoning-effort factor has been removed prior to 
data collection. All responses will be collected at `effort: "low"`, chosen 
because it is the closer match to Bini et al.'s original experimental setup 
(which used models without explicit reasoning traces). The original H3 
(reasoning effort attenuates perturbation effects) is removed from the 
confirmatory hypotheses and relocated to the paper's future-work discussion. 
Total response count is reduced from 1,600 to 800.

---

## Appendix: What this preregistration does NOT cover

The following analyses, if conducted, will be clearly labeled as exploratory 
in the paper and not treated as confirmatory tests:

- Analysis of reasoning traces (content of the `thinking` field)
- Analysis of model-reported confidence and reasoning-type variables
- Any reanalysis under alternative outcome definitions
- Post-hoc subgroup comparisons
- Effects of perturbations not specified in §4
- Comparisons across reasoning effort levels