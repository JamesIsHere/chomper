# chomper: plan

Source: `10k-variance-explainer-plan.md` (Downloads, 2026-10-27), reviewed
with James in session fd7b4cbf on 2026-10-27. All six open decisions ruled.
The project was named variance-bridge until 2026-10-30.

## Purpose

An equity research project on James's public GitHub (github.com/JamesIsHere):
read a company's 10-K the way an analyst would, and show what moved earnings,
why, and whether management's explanation holds up.

Most people who open it will read financial statements, not code. They will
judge what they recognize from their own work: a variance bridge, an
explanation of what changed and why, a conclusion.

What it has to show, in James's words: "If I need it and don't have it, I
build it." A finance operator who uses AI to glue public data into the tool
he needs. The finance judgment carries the page: what moved, why, and
whether management's explanation holds up. The building is the evidence
underneath.

Priority: finished and clear beats ambitious. Version 1 is meant to take a
day or two. If it grows, cut scope.

## What version 1 does

- Old Dominion Freight Line (CIK 878927), FY2025 vs FY2024, both years from
  the FY2025 10-K (accession 0001193125-26-067161, filed 2026-02-24).
- Financial figures from SEC EDGAR: companyfacts API plus the filing's XBRL
  instance file (see findings).
- One bridge, FY2024 operating income to FY2025 operating income.
- AI reads the MD&A and, per bar, returns the explaining passage (verbatim
  quote, stated amount) and a one- or two-sentence draft. Code decides the
  flags.
- Flags where management's explanation does not account for the change.
  Any unexplained remainder is its own bar, never hidden.
- Output: one static page on GitHub Pages, plus a README with a screenshot
  and the live link.

## Rulings (2026-10-27)

| # | Decision    | Ruling                                                                                            |
|---|-------------|---------------------------------------------------------------------------------------------------|
| 1 | Company     | Old Dominion Freight Line, FY2025 vs FY2024                                                       |
| 2 | Bridge bars | Every line: volume, yield, revenue remainder, then all 9 face-statement expense lines             |
| 3 | AI step     | Script calls a language model (plan tokens); James reviews; build reads only the committed output |
| 4 | Stack       | Python stdlib only; horizontal HTML/SVG bridge, one `<details>` row per bar; JSON, thousands      |
| 5 | Citations   | Verbatim quote + filing page + text-fragment link to sec.gov; XBRL tag/period/accn per amount     |
| 6 | Repo name   | `variance-bridge` (renamed `chomper` 2026-10-30); Pages serves `docs/` from `main`                |

Why, in one line each:
1. Screen of 7 carriers: ODFL is the only one where both revenue (-5.5%) and
   operating income (-11.8%) move materially; single segment, LTL stats.
2. A bridge schedule is what analysts read at work; grouping would hide
   undiscussed lines.
3. Plan tokens over API dollars; the only API constraint (outsider rerun)
   does not bind for this project.
4. Phone width: 14 labels do not fit under vertical bars at 375px.
5. One tap to the highlighted sentence in the real filing is the credibility.
6. Bridge is the standard term in variance analysis; survives extensions.

## Screen findings (verified 2026-10-27)

Walk, $M, as each item affects operating income (rounded; foots exactly
unrounded):

| Step                         | Amount  | Source                                 | MD&A quantifies |
|------------------------------|---------|----------------------------------------|-----------------|
| FY2024 operating income      | 1,544.0 | OperatingIncomeLoss                    |                 |
| Volume (tons -9.1%)          | -527.5  | MD&A stats table                       | yes, in %       |
| Yield (rev/cwt +3.9%)        | +206.1  | MD&A stats table                       | yes, in %       |
| Other revenue / remainder    | +3.1    | reported change minus the two above    | no              |
| Salaries, wages, benefits    | +54.0   | LaborAndRelatedExpense                 | yes             |
| Operating supplies           | +64.3   | OperatingCostsAndExpenses              | yes             |
| Depreciation                 | -20.1   | DepreciationAndAmortization            | yes             |
| Insurance and claims         | +17.9   | OperatingInsuranceAndClaimsCostsProd.  | no              |
| Purchased transportation     | +12.8   | odfl:PurchasedTransportation           | no              |
| General supplies             | +7.4    | odfl:OtherSellingAndGeneralExpense     | no              |
| Operating taxes and licenses | +5.8    | DirectTaxesAndLicensesCosts            | no              |
| Communications and utilities | +1.9    | DirectCommunicationsAndUtilitiesCosts  | no              |
| Miscellaneous, net           | -8.5    | OtherCostAndExpenseOperating           | no              |
| FY2025 operating income      | 1,361.0 | OperatingIncomeLoss                    |                 |

- Volume = change in tons x FY2024 rev/cwt x 20; yield = FY2025 tons x change
  in rev/cwt x 20. Tons 9,000k -> 8,177k; rev/cwt $32.05 -> $33.31.
- MD&A dollar-quantifies 3 of 9 expense lines: -$98.2M of the -$135.5M opex
  change (72%). Insurance and claims (-$17.9M, -19%) is never discussed.
- companyfacts omits extension-taxonomy facts. Purchased transportation and
  general supplies exist only in the instance file
  (`odfl-20251231_htm.xml`); they close the gap exactly
  (FY2025 279.197 = 110.036 + 169.161).
- Tons and rev/cwt are not in XBRL; they come from the MD&A stats table.
- XBRL amounts carry `decimals="-3"`: integer math in thousands; Decimal
  only for the yield calculation.
- The MD&A text carries printed page markers (23 to 30) for citations.
- SEC requires a User-Agent with name and email; James approved his yahoo
  address for it.

## Not in version 1 (planned later)

- FRED context, e.g., revenue against industry demand drivers. First
  extension.
- Ratios, cash conversion, peer comparisons, multi-year trends; likely
  connects to Pharos.
- Other tickers or multiple companies (tag normalization is its own project).
- Quarterly (10-Q) analysis.
- Segment-level bridges.
- Fuel-surcharge split of yield (MD&A gives % only: +3.9% with fuel, +4.8%
  without).

Design for these only to the extent of not blocking them: keep data pull,
analysis and page as separate steps. Build no abstractions for future
features in v1.

## Quality bar

- Every number on the page traces to its source: an XBRL fact (tag, period,
  accession) or an MD&A passage with page.
- The bridge foots exactly: prior year plus the bars equals current year.
- Money in integer thousands; Decimal for rates. No floats in JSON.
- AI output: every quote verified verbatim against the filing by code, every
  stated amount matched to its bar by code, nothing published without
  James's review. Flags come from arithmetic, never from the model.
- Unexplained remainders are shown, never absorbed into another bar.
- The page works on a phone and reads clearly to someone who doesn't read
  code.
- No secrets in the repo.

## Done means

- A live GitHub Pages URL showing the bridge, commentary and flags.
- One command regenerates the page from the source data and the committed,
  reviewed commentary (it never calls the AI).
- A README in James's own words: what it is, a screenshot, the live link,
  how it was built (including the AI's role), and status.
- Pinned on his GitHub profile.

## Milestones

Written one at a time.

1. (draft next) Data pull: companyfacts + instance file + MD&A stats table
   into JSON; the walk foots exactly to the -182,953 thousand change
   (1,361,045 - 1,543,998).
