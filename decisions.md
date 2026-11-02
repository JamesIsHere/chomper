# Decisions

Hand-edited source for the Decisioning page. One entry per decision:

    ## YYYY-MM-DD | Short title
    Group: Scope, Method, Presentation, Evidence and review, or Build and process
    Decision: what was decided
    Why: the reason, one or two sentences
    Status: active (or: superseded by YYYY-MM-DD Short title)

To change a decision, add a new entry and mark the old one superseded; do not delete it.
Then run `python build_history.py`.

## 2026-10-27 | Company and years
Group: Scope
Decision: Old Dominion Freight Line, FY2025 vs FY2024, for the one-year bridge page.
Why: Of 7 carriers screened, the only one where both revenue (-5.5%) and operating income (-11.8%) move materially; single segment, with freight statistics.
Status: active

## 2026-10-27 | Bridge bars
Group: Method
Decision: Every line gets a bar: volume, yield, revenue remainder, then all 9 income-statement expense lines.
Why: A full bridge schedule is what analysts read at work; grouping would hide lines management does not discuss.
Status: active

## 2026-10-27 | AI step
Group: Evidence and review
Decision: A script calls a language model from the command line on plan tokens to draft commentary; James reviews; the page build reads only the approved output.
Why: Plan tokens over API dollars; nothing about this project requires an API.
Status: active

## 2026-10-27 | Stack
Group: Build and process
Decision: Python standard library only; horizontal HTML bridge, one expandable row per bar; JSON data in USD thousands.
Why: Fourteen labels do not fit under vertical bars at phone width.
Status: active

## 2026-10-27 | Citations
Group: Evidence and review
Decision: Verbatim quote plus filing page plus a link that jumps to the sentence on sec.gov; every amount carries its XBRL tag, period and accession.
Why: One tap to the highlighted sentence in the real filing is the credibility.
Status: active

## 2026-10-27 | Repo name
Group: Build and process
Decision: variance-bridge; GitHub Pages serves docs/ from main, no Actions.
Why: Bridge is the standard term in variance analysis, and the name survives extensions.
Status: superseded by 2026-10-30 Project name

## 2026-10-30 | Bar order switch on the one-year page
Group: Presentation
Decision: Default order is the 10-K's line order; a switch reorders bars by cost behavior or by size of change.
Why: Statement order ties to the filing; cost-behavior order shows which costs are volume problems.
Status: active

## 2026-10-30 | Explore five years, additively
Group: Build and process
Decision: Build the five-year view as new files next to the one-year page; roll back by archiving them if it does not work out.
Why: Exploring; the one-year page stays intact while the multi-year idea is tested.
Status: active

## 2026-10-30 | One method for any company, in dollars
Group: Scope
Decision: Build one view that runs on any S&P 500 company the same way; dollars only, no tonnage or other unit data; cross-company comparison deferred.
Why: A base-level look across all industries comes before anything company-specific.
Status: active

## 2026-10-30 | Core measure: flexed budget
Group: Method
Decision: Each line's yearly change is split into what it would have done moving in step with revenue, and the remainder beyond revenue.
Why: Shows which costs move when demand changes without hand-classifying costs as fixed or variable.
Status: active

## 2026-10-30 | Colors
Group: Presentation
Decision: Green for good, red for bad, in shades by size.
Why: Classic finance convention; signed numbers in every cell keep it readable for colorblind readers.
Status: active

## 2026-10-30 | Ratios lead
Group: Method
Decision: Costs as a share of revenue lead each company page; the dollar grid sits underneath as the drill-down.
Why: Percent of revenue is scale-free and the trend reads straight down a row.
Status: active

## 2026-10-30 | Trend at the top
Group: Presentation
Decision: Each company page opens with revenue and income by year with growth rates, plus a small chart indexed to the first year = 100.
Why: Start simple; one axis, and the gap between the lines shows leverage.
Status: superseded by 2026-11-01 Ten years at the top

## 2026-10-30 | Anchor on pre-tax income
Group: Method
Decision: Every company's lines must add up to pre-tax income; operating income is kept as a subtotal where the company reports one.
Why: Banks, insurers and some industrials report no operating income; pre-tax income is reported by every industry.
Status: active

## 2026-10-30 | Main menu
Group: Presentation
Decision: The horizontal menu is the main header: All and Decisioning. Companies are listed vertically on the All page, not in the menu.
Why: 500 tickers do not fit across a header.
Status: superseded by 2026-11-01 Menu: Chomper and Decisioning

## 2026-10-30 | Industry grouping
Group: Scope
Decision: The All page lists all S&P 500 companies by GICS sector, then sub-industry, from Wikipedia's list, with every SEC identifier checked against the SEC's own file.
Why: The grouping readers already know; sort out the grouping before any further analysis.
Status: active

## 2026-10-30 | Full S&P 500 run
Group: Scope
Decision: Not yet; settle the grouping and the page first.
Why: The run is about 1,000 filings of downloads; no point until the page is right.
Status: active

## 2026-10-30 | Time windows
Group: Method
Decision: A window must contain at least one revenue contraction and no undisclosed regime break. Long: 10-year headline only. Medium: 5-year line-by-line detail. Short: 1-year bridge. Acquisitions and accounting changes are marked, never used to shorten a window.
Why: Settles the recurring 10-year question: give each time frame its own window instead of forcing all three into one table.
Status: active

## 2026-10-30 | Decisioning page
Group: Presentation
Decision: A main-menu page lists every decision with its date, built from this file.
Why: To see every decision in one place and come back to change one.
Status: active

## 2026-10-30 | Decision groups
Group: Presentation
Decision: The Decisioning page groups decisions by type (Scope, Method, Presentation, Evidence and review, Build and process), then by date, newest first.
Why: One flat list was too much to piece through; the type says which question a decision answers.
Status: active

## 2026-10-30 | Project name
Group: Build and process
Decision: The project is chomper, an equity research project; the GitHub repo is JamesIsHere/chomper.
Why: The work grew from one bridge into reading any S&P 500 company's filings for what moves earnings; the name fits where it is going.
Status: active

## 2026-10-30 | One-year page approved
Group: Evidence and review
Decision: James reviewed the ODFL one-year bridge (wording, layout, the three findings) and approved it as it stands.
Why: Good in its current form; work moves on to the longer windows.
Status: active

## 2026-10-30 | Ten-year breaks
Group: Method
Decision: An acquisition is marked when its price is at least 10% of the buyer's total assets at the prior year end (SEC Regulation S-X Rule 1-02(w), the investment test), read from each 10-K's own XBRL. ASC 606 and 842 are marked in the year they became required. Every restatement is shown with the figure as first reported.
Why: Marking breaks must be correct, not a judgment call: the SEC's own significance test replaces a threshold of ours, and each deal's size comes from the filing.
Status: active

## 2026-11-01 | Menu: Chomper and Decisioning
Group: Presentation
Decision: The menu across the top has two items, Chomper (the company list) and Decisioning. The separate All item is gone; the name is capitalized.
Why: The name and All linked to the same page.
Status: superseded by 2026-11-01 Considerations page

## 2026-11-01 | Ten years at the top
Group: Presentation
Decision: Each company page opens with ten years of revenue, operating income (where the company reports it), pre-tax income and pre-tax margin, then the same ten years as the indexed chart. The five-year revenue and income table is removed; the five-year section starts at the cost grids. The list of breaks sits at the bottom of the page for now.
Why: The five-year table repeated the last five columns of the ten-year one; operating income moved up so it does not drop off the page.
Status: superseded by 2026-11-01 Ten years at the top, charted in log dollars

## 2026-11-01 | Ten years on one accounting basis
Group: Method
Decision: The ten-year headline promises the same accounting basis, with acquisitions marked; it does not promise the same business. Each year's change comes from the latest 10-K that shows both years, and the chart chains those changes. A change that does not match the dollar figures above it, because a later 10-K recast one of the years, is marked with an asterisk. Modified retrospective adoptions (most ASC 606, nearly all ASC 842) recast nothing and stay marked breaks until the adoption notes are read.
Why: Every 10-K shows its comparative year on its own basis, so same-filing growth handles restatements, retrospective changes, reclassifications and discontinued operations for every company without reading; same business needs the pro forma notes, company by company.
Status: superseded by 2026-11-01 Ten years on one accounting basis, chart in dollars

## 2026-11-01 | Considerations page
Group: Build and process
Decision: A third menu page, Considerations, lists what the pages do not yet do right or what comes next, from considerations.md: one entry per item with a theme, the companies it touches, and the condition that makes it due. The menu is Chomper, Decisioning, Considerations.
Why: Items raised in passing (in chat, in the local notes) get lost; a due condition on each says when "done" is not done yet.
Status: active

## 2026-11-01 | Ten years at the top, charted in log dollars
Group: Presentation
Decision: Each company page opens with ten years of revenue, operating income (where the company reports it), pre-tax income and pre-tax margin, then a chart of revenue and pre-tax income in dollars on a log scale. Each year with a significant acquisition or a newly required accounting standard gets a numbered marker on the chart, explained in a numbered key under it. Under the lines, a band of bars shows each year's cost gap: pre-tax income at the prior year's pre-tax margin minus actual pre-tax income, both years from the same 10-K; red when costs grew faster than revenue, green when revenue grew faster. Figures a later 10-K changed are listed at the bottom as Note 1 - Recast Figures, and a starred change in the table reads "See Note 1". The chart and the five-year grids carry no explanatory notes. The five-year revenue and income table stays removed.
Why: A chart in multiples of the first year depends on that year (CAT's small 2016 pre-tax income made it read 83x); a log scale keeps one axis, and equal slopes still mean equal growth, without a base year. The bars put a dollar size on costs outrunning revenue. The numbered markers were chosen from four trial displays (markers, shaded bands, labels, swim lanes).
Status: active

## 2026-11-01 | Ten years on one accounting basis, chart in dollars
Group: Method
Decision: The ten-year headline promises the same accounting basis, with acquisitions marked; it does not promise the same business. Each year's change comes from the latest 10-K that shows both years. The dollar figures and the chart's lines are the latest reported; the cost-gap bars take both years from that same 10-K. A change that does not match the dollar figures above it, because a later 10-K recast one of the years, is starred and points to Note 1. Modified retrospective adoptions (most ASC 606, nearly all ASC 842) recast nothing and stay marked breaks until the adoption notes are read.
Why: Every 10-K shows its comparative year on its own basis, so same-filing growth handles restatements, retrospective changes, reclassifications and discontinued operations for every company without reading; same business needs the pro forma notes, company by company. The chart moved to dollars on a log scale, so it no longer chains the changes.
Status: active

## 2026-11-02 | Standards marked in the year adopted
Group: Method
Decision: ASC 606 and ASC 842 are marked on the ten-year chart in the year each company adopted them, as read from its own 10-K into data/adoptions.json (year, whether earlier years were recast, accession, verbatim quote). A standard adopted with earlier years recast gets no marker, since the series has no break there. Where no adoption note was found, the marker stays on the year the standard became required; where the 10-K does not state the method, the key says only "adopted".
Why: The required year was wrong for early adopters (MSFT, UNH), and a fully retrospective adoption (AAPL, JPM and MSFT 606, MSFT 842) is not a break; the company's own adoption note is the only source that says which.
Status: active

## 2026-11-02 | Company names: one source, one rule
Group: Presentation
Decision: Every company name on the site comes from the S&P 500 list (data/sp500.json) through one function, display_name: a trailing legal suffix is dropped ("Apple Inc." becomes Apple), except a bare "Company" that would leave one word ("Southern Company" stays); words that are part of the name stay (Group, Holdings, Trust, Bancorp); "Home Depot (The)" becomes The Home Depot. Company pages and the Chomper list use the same function.
Why: SEC filer names mix capitals and suffixes ("HOME DEPOT, INC.", "PROGRESSIVE CORP/OH/"), and the list's own names are not uniform; one rule over one source can be checked against a single cell per company.
Status: active

## 2026-11-02 | Fiscal year labels
Group: Presentation
Decision: A fiscal year is labeled from its end date read a week early: a year ending in December shows as the year (2020), any other as month and year (Sep 2020, Jan 2025). The week keeps 52/53-week years on one month: JNJ's year ended 2021-01-03 is 2020, and HD's years all read Jan. Labels name the month a year ends in, not the company's own fiscal-year name (James, 2026-11-02): HD's "Jan 2025" is the year HD calls fiscal 2024.
Why: Labeled by the raw end date, JNJ's years jumped between "Jan 2021" and "2020" and HD's between Jan and Feb, so fiscal years looked missing or doubled.
Status: active

## 2026-11-02 | Rounding is not a disagreement
Group: Method
Decision: When two filings give the same figure at different precision, and the coarser one equals the finer one rounded to its unit (PGR: $62,109M against $62,108.5M), the difference is not listed as a disagreement; the footer says the filings agree apart from rounding. Any other difference is listed with both values.
Why: Listing rounding as disagreement printed pairs like "$62.11B vs $62.11B", which reads as an error; recording real disagreements with both values still holds.
Status: active

## 2026-11-02 | Recast, not restated
Group: Presentation
Decision: A figure that a later 10-K changed is called recast ("Note 1 - Recast Figures", "as later recast"), never restated.
Why: In accounting a restatement corrects an error (ASC 250); most of these changes are new standards, presentation changes or discontinued operations, and calling them restatements claims an error the company never made.
Status: active

## 2026-11-02 | Deal names from the buyer's 10-K
Group: Presentation
Decision: The chart key names each significant acquisition as the buyer's own 10-K prose names the acquired company, with a trailing legal suffix dropped (HD Supply, SRS, Liberty Property Trust, Duke Realty), read by hand into data/deal_names.json with a verbatim quote and the accession. A significant deal with no record stops the build.
Why: The XBRL member label is not the company's name: HD tags HD Supply as "HD Holdings Inc", and PLD's labels came out lowercase and doubled ("Liberty property trust and liberty property limited partnership").
Status: active

## 2026-11-02 | Loss years break the income line
Group: Presentation
Decision: The ten-year chart stays on a log scale for every company. A year with zero or negative pre-tax income breaks the pre-tax income line and sits on a strip labeled Loss under the plot, with its amount; the line runs only through consecutive profitable years. The axis is set from the profitable years. A year with zero or negative revenue stops the build.
Why: A log scale cannot show zero or a negative, and growth is not defined across a change of sign, so the break marks exactly where slope stops meaning growth. Chosen over a symlog axis (slopes near zero would not mean growth), a linear axis for loss companies only (two chart grammars and the first-year problem back), and a margin axis (repeats the table). Checked on test data, Caterpillar's revenue with invented losses in five patterns.
Status: active

## 2026-11-02 | No marker where the standard does not reach the business
Group: Method
Decision: A standard gets no marker on the ten-year chart when the company's own 10-K says it falls outside the standard's scope and no adoption note follows (data/adoptions.json, out_of_scope, with that statement quoted). PGR's FY2016 10-K says insurance contracts are outside ASC 606; its FY2018 adoption section lists no revenue standard; PGR shows no 2018 marker.
Why: Every marker cites the company's own words. A "required this year" marker on PGR asserted a break the filing never claims, while the FY2016 sentence says why there is none (James, 2026-11-02).
Status: active

## 2026-11-02 | Footing allows the filing's own rounding
Group: Method
Decision: A year foots when the reported lines miss pre-tax income (or operating income) by no more than half a rounding unit for each figure summed, the subtotal included, with each unit read from the fact's own XBRL decimals. Any gap allowed this way becomes its own row, "Rounding in the filing" (a second row, "within operating income", when the operating subtotal is the one off), so the five-year grid and every later check still add exactly; history.py also records each gap with both values in footing_gaps, and the page footer names each one (year, subtotal, lines against reported, in millions). Rounding rows are not costs, so they do not scale with revenue: their whole change counts as beyond revenue, and pre-tax income's in-step change is taken from the figures that foot. A gap beyond the allowance still stops the build.
Why: Carnival's lines miss by $1M in years where every figure is rounded to the million; an exact rule stopped a real company over the filing's own rounding, while a flat dollar or percent tolerance would be arbitrary across company sizes. Boeing's $70B gap stays a hard stop (James, 2026-11-02).
Status: active

## 2026-11-02 | No cost-gap bar after a loss year
Group: Presentation
Decision: The ten-year chart draws no cost-gap bar for a year whose prior year had zero or negative pre-tax income (prior year as shown in the 10-K that reports both). The Loss strip above already marks those years.
Why: The bar is the pre-tax income at last year's margin minus what was earned; after a loss, last year's margin is negative and scaling it by revenue is not a cost gap. Carnival's Nov 2022 bar read $54.6B "revenue ran ahead of costs" from a -499% margin on 6.4x revenue, against an actual pre-tax change of +$3.44B (James, 2026-11-02).
Status: active

## 2026-11-02 | No ratio or growth on a loss base
Group: Method
Decision: Nothing on a company page divides or scales by a base at or below zero. The ten-year table leaves the percent change blank when the prior year is zero or negative (a fall from a positive year into a loss still shows, e.g. Carnival Nov 2020 -435.1%). The five-year dollar grid, in a column that starts from a loss year, leaves "if every cost moved in step with revenue" and "beyond revenue" blank and shows each line's whole change instead; a note under the grid names those columns. Together with "No cost-gap bar after a loss year", this is one rule. James will look through the loss cases for a tighter rule later.
Why: Scaling a loss by revenue gave Carnival -$51.20B "in step" against a +$3.44B change in Nov 2022, and percent changes like +3188.7% across a sign flip; the chart's income line already breaks at losses (James, 2026-11-02: "If you get a loss on the base here, I think we need to do something").
Status: active

## 2026-11-02 | One line under two tags is one row
Group: Method
Decision: When a line carries the same label in the filing but a different XBRL tag in the two 10-Ks, it is shown as one row, only when every tag carries figures, the years never overlap, and the line's sign and section (above or below operating income) agree. The row keeps the latest tag; history.py records every tag with its years in `retagged`, and the page footer names each one ("tagged InterestExpense for 2021 to 2022, then InterestExpenseNonoperating for 2023 to 2025"). The year both 10-Ks show is compared across the tag change, as for any line. No matching on similar labels and no company-specific rules; anything short of the test stays two rows.
Why: Keyed by tag, the line became two rows each jumping to or from nothing: Carnival's interest expense showed -$2.07B and +$1.61B where the real change was -$457M. The census found the pattern on 158 of 322 passing companies; the rule merges every split row on 135 of them (164 rows; 97 are InterestExpense to InterestExpenseNonoperating). 23 rows on 23 companies stay split, 20 where the line changes section or sign between the filings (James, 2026-11-02).
Status: active

## 2026-11-02 | A line tagged only in parts is shown summed
Group: Method
Decision: When a line on the income statement has no tagged total in a year, and the filing tags it in parts on an axis the statement itself shows (Boeing's cost of goods and services sold, by product and by service), the line is the sum of those parts, as one row under the line's own label. The footer names the parts by the filing's labels. If the parts sit on more than one such axis the build stops; if a line is summed in some years and a single total in others, the build stops ("Member slice"), since the parts may be only a slice of the total. Footing to pre-tax income stays the check, with no new tolerance.
Why: 39 of the 55 Footing stops were one cost line tagged only by product and service; reading only totals lost the whole line (Boeing's "$70B gap" is its 2023 cost of goods and services sold, $70,070M). One summed row keeps every label a real filing label and matches how revenue, split the same way on the face, is already shown as one total; per-part rows would have carried revenue labels on cost rows (Boeing's parts are labeled "Sales of products" and "Sales of services"). Of the 55, 36 now pass, 10 stop as Member slice; the 11 built pages are unchanged (James, 2026-11-02).
Status: active


## 2026-11-02 | Pre-tax income found by position
Group: Method
Decision: When neither pre-tax income tag anchors the statement's calculation, pre-tax income is the one subtotal that income tax is subtracted from to reach net income, provided that subtotal has its own calculation; more than one such subtotal stops the build. The page footer names the line by the filing's own label. No list of further tags.
Why: 33 companies print a pre-tax line under some other tag (Costco's "INCOME BEFORE INCOME TAXES" is IncomeLossAttributableToParent; eight different tags across the 33). Of the 52 stopped here, 29 now pass, each with a subtotal labeled as pre-tax income in the filing; the rest still stop. The 11 built pages are unchanged. Made under the standing rule that XBRL plumbing inside the rails is the agent's (James, 2026-11-02).
Status: active

## 2026-11-02 | Every company says whether it can be read
Group: Presentation
Decision: The All page gives every company without a page a status in its row: "Readable" when its filings pass every check of the five-year step, or "Not readable" with the reason in one plain line (one sentence per census class: statement not identified, pre-tax income not found, revenue not one line, figures that disagree, filings not found, lines that do not add up, a line in parts against a total, or an error in the reader). The opening paragraph counts both. Status comes from data/census.json, so a census rerun updates it. The full build of pages for readable companies stays a separate decision: each page also needs ASC 606/842 adoption records read from the company's 10-Ks.
Why: The agreed tail treatment was to exclude openly with reasons rather than add a rule per small class; with 11 pages built, a reader could not otherwise tell a company that cannot be read from one not yet built (James, 2026-11-02).
Status: active

## 2026-11-02 | Revenue in parts is not summed
Group: Method
Decision: Revenue is read like any line, but when the filing tags it only in parts, or leaves a year without it, the build stops with a named Revenue reason rather than summing the parts. Unlike a cost line, which parts make up "revenue" decides how the headline number is defined, so it waits for James's ruling.
Why: Three companies crashed on revenue with no total (APA, LHX, WFC). Summing WFC's parts would have shown three fee lines (advisory, brokerage, investment banking) as Wells Fargo's revenue. All three now stop as Revenue; the 11 built pages are unchanged (agent, under the standing XBRL rule, 2026-11-02).
Status: active

## 2026-11-02 | S&P 500 page, a trial
Group: Presentation
Decision: A new page, S&P 500 in the menu, sums revenue and pre-tax income across today's S&P 500 and each GICS sector, ten calendar years (2016 to 2025), and draws each sum with the company pages' log chart and cost-gap bars, all static, with one line of annual growth (revenue, costs, the gap between them) above each chart. Values come from the SEC's frames data (calendar-aligned, most recently filed); a company counts only with revenue and pre-tax income in all ten years, so every year sums the same companies, and the rest are listed with reasons. Revenue is the largest of the total-revenue tags a company reports in a year; pre-tax income is history.py's two tags, else domestic plus foreign. Sums, not medians: the largest companies dominate, and the page says so. Financials stays in, with a note that its revenue is not comparable. No drill-down yet.
Why: James wanted to see what costs have done across the S&P 500 and its sectors before building anything interactive (James, 2026-11-02: "lay out the main graph and the industry graphs, all static ... on a single new page, like a trial page"). The sectors add to the total in every year; the 11 built companies match their ten-year data. Rollback = move aggregate.py, data/aggregate.json and docs/aggregate.html to archive and drop the menu item.
Status: active

## 2026-11-02 | The S&P 500 as it was
Group: Method
Decision: Membership by month, January 2016 to December 2025, comes from the version of Wikipedia's "List of S&P 500 companies" current on the first of each month (membership.py; a page drawing one row per company and a bar for its months). Companies are matched by SEC identifier; a blank one is taken from the SEC's ticker file, and a new identifier that keeps the ticker the next month is the same company. Every month must list 495 to 510 rows. The S&P 500 page adds the index as it was: each year's change measured on that year's 1 January members that report both years, each company against itself, chained; today's members are chained the same way, so the gap between the two lines is survivorship alone.
Why: Tracing today's members back selects on the outcome: a third of January 2016's members were gone by December 2025, and index entry requires positive earnings. Measured, today's members overstate revenue growth by about half a point a year and the decade's margin gain by half (3.0 points against 2.0) (James, 2026-11-02).
Status: active

## 2026-11-02 | Survivorship by sector
Group: Presentation
Decision: The S&P 500 page shows, for each sector, the pre-tax margin of the sector as it was (members on 1 January of each year) against today's members, chained the same way as the total, with the number of members counted in the first and last year under each chart. Each company sits in its last sector while a member; the old Telecommunication Services is Communication Services. The ten-year dollar charts of today's members stay below, under their own heading.
Why: Split by sector, survivorship is not a uniform haircut: it reverses the decade in Utilities (-2.1 points as it was, +2.6 for today's members) and Consumer Discretionary, and runs through named companies; PG&E was out of the index 2020 to 2022 while it recovered from its wildfire losses, and Vistra turned around two years before joining, so only today's line counts their rebounds (James, 2026-11-02).
Status: active
