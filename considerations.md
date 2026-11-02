# Considerations

Hand-edited source for the Considerations page: what the pages do not yet do right, or what comes next,
kept so it is not lost between sessions. Not decisions (those are in decisions.md) and not a to-do list:
each item says when it becomes due. One entry per item:

    ## YYYY-MM-DD | Short title
    Theme: Accounting basis, Acquisitions, Presentation, Coverage, Evidence, or Path forward
    Item: what is not right yet, or what could come next
    Why: why it matters
    Companies: which companies it touches and where each stands (handled, found, not checked), or "all"
    Due: the condition that makes it due
    Status: open (or: closed YYYY-MM-DD, how)

The date is when the item was first raised. Close an item by changing its status; do not delete it.
Then run `python build_history.py`.

## 2026-10-30 | ASC 606 and 842 adopted without recasting
Theme: Accounting basis
Item: A company that adopted ASC 606 (2018) or ASC 842 (2019) by the modified retrospective method never recast earlier years, so the ten-year series changes basis that year and no 10-K shows both bases. The one-basis rule cannot detect it. The page marks each standard in the year it became required, not the year adopted, and not the method: XBRL adoption tagging is inconsistent (PGR and PLD tag none; UNH tags 606 in FY2016).
Why: The ten-year headline promises one accounting basis; in these years the change row looks clean but may not be.
Companies: MSFT: 606 consistent with a fully retrospective adoption (the FY2017 recast), adoption note not read. AAPL, CAT, HD, JNJ, JPM, ODFL, PGR, PLD, UNH: method not read.
Due: before the full S&P 500 run, or before the headline is called complete.
Status: closed 2026-11-02, all 20 adoption notes read into data/adoptions.json; the chart marks each standard in the year adopted and drops it where earlier years were recast

## 2026-11-02 | Adoption record is hand-read
Theme: Accounting basis
Item: data/adoptions.json was read by hand from the 10 companies' 10-Ks. Both gaps are closed (2026-11-02): JPM's FY2019 10-K states its ASC 842 method (modified retrospective, no prior periods revised); PGR's FY2016 10-K says insurance contracts are outside ASC 606, so PGR shows no 606 marker. The full S&P 500 run needs about 1,000 such reads.
Why: The key's adoption years and "not recast" claims are only as good as a reading that does not yet scale.
Companies: at 500 companies, all.
Due: before the full S&P 500 run.
Status: open

## 2026-10-30 | A recast that coincides with a tag change is missed
Theme: Accounting basis
Item: When a company recasts a year and changes the XBRL tag in the same filing, the figure as first reported sits under the old tag, which the series never reads, so the recast is not listed.
Why: A restated year can go unmarked in the breaks list.
Companies: MSFT: FY2017 revenue (first reported under SalesRevenueNet); the year is still marked through pre-tax income. Others: not checked.
Due: before the full S&P 500 run.
Status: open

## 2026-11-01 | Acquisitions below 10% are not marked
Theme: Acquisitions
Item: Only deals of at least 10% of prior total assets are marked. A serial acquirer making many smaller deals reads as organic growth; the run only stops when unexplained acquisition spend in a single year reaches 10%.
Why: The headline marks acquisitions so readers know when growth is bought; many small deals add up to the same thing.
Companies: all; none checked for cumulative small deals.
Due: before the full S&P 500 run.
Status: open

## 2026-11-01 | Same-business (organic) growth is not measured
Theme: Acquisitions
Item: The ten-year headline promises the same accounting basis, not the same business. Organic growth would come from each deal's ASC 805 pro forma disclosure (revenue and earnings as if acquired at the start of the prior year), read and approved company by company.
Why: Reported growth after a large deal mixes bought and grown revenue.
Companies: MSFT, HD, JNJ, PLD (the companies with significant deals): pro formas not read.
Due: when a reader needs organic growth, or when I1 starts.
Status: open

## 2026-10-30 | Year labels for 52/53-week years
Theme: Presentation
Item: Year labels come from the period end date, so a fiscal year ending in early January shows as, for example, "Jan 2022", which reads like the next fiscal year.
Why: A reader can misplace a year by one.
Companies: HD, JNJ (Jan labels); AAPL (Sep), MSFT (Jun) labels read correctly but differ in style.
Due: before the full S&P 500 run.
Status: closed 2026-11-02, labels read a week before the period end (JNJ now 2016 to 2025); HD keeps end-month labels by James's choice ("Jan 2025" is the year HD calls fiscal 2024)

## 2026-11-01 | "Restated" used for recasts
Theme: Presentation
Item: The breaks list calls every changed figure "restated". In accounting a restatement corrects an error (ASC 250); most of these are retrospective changes in principle, presentation changes or discontinued operations.
Why: The wrong word claims an error the company never made.
Companies: PLD, CAT, MSFT, JNJ, JPM: wording on the page; cause read only by inference.
Due: when the breaks list gets its permanent place.
Status: closed 2026-11-01, Note 1 bullets say "as later recast", matching the Recast Figures heading

## 2026-11-01 | Breaks list is at the bottom for now
Theme: Presentation
Item: The ten-year breaks (acquisitions, standards, restatements) moved from the opener to the bottom of each company page as a temporary place.
Why: A reader who sees a marked change at the top has to scroll to the bottom to learn why.
Companies: all
Due: the next pass on the company page layout.
Status: closed 2026-11-01, acquisitions and standards are numbered on the chart with a key under it; only recasts stay at the bottom, as Note 1

## 2026-11-01 | Two headings stacked
Theme: Presentation
Item: "Five years: which costs moved with revenue" now sits directly on "Costs as a share of revenue", with nothing between them.
Why: Reads as an empty section.
Companies: all
Due: the next pass on the company page layout.
Status: closed 2026-11-01, the two grids became collapsed sections under the five-year heading

## 2026-11-01 | Deal names in the filer's own capitalization
Theme: Presentation
Item: Deal names come from the filing's documentation label as written, so some show in lowercase ("liberty property trust and liberty property limited partnership").
Why: Looks like a bug on the page.
Companies: PLD (Liberty, Duke). Others: not checked.
Due: the next pass on the breaks list.
Status: closed 2026-11-02, deal names come from data/deal_names.json, read from each buyer's 10-K prose

## 2026-11-01 | Ten-year chart depends on the first year
Theme: Presentation
Item: The chart shows each line as a multiple of the first year. When that year is unusually small, the line explodes and the other line goes flat: CAT's 2016 pre-tax income was $139.0M, so pre-tax income reads 83x by 2025 and revenue (1.75x) is a flat line at the bottom. A negative first year drops the chart entirely.
Why: The chart's shape then reflects one odd year, not the decade.
Companies: CAT (83x); PGR (pre-tax 0.63x to 9.67x) stretched; others read normally. At 500 companies, more.
Due: before the full S&P 500 run.
Status: closed 2026-11-01, the chart now plots dollars on a log scale, which has no first year to depend on

## 2026-11-01 | Log chart drops on a loss year
Theme: Presentation
Item: A log scale cannot show zero or a negative number, so a company with any year of zero or negative pre-tax income gets a one-line note instead of the ten-year chart. None of the 10 companies has one; across the S&P 500 over ten years, many will (2020 alone).
Why: The companies whose decade most needs a picture, the ones with a loss year, would lose it.
Companies: none of the 10; at 500 companies, many.
Due: before the full S&P 500 run.
Status: closed 2026-11-02, the income line now breaks at a loss year and the year sits on a loss strip under the plot with its amount; checked on test data only, since no real loss company has passed history.py yet

## 2026-11-01 | Phone layout unchecked
Theme: Presentation
Item: Every visual check is at desktop width; the screenshots James gets are the desktop layout. How the pages read on a phone is unchecked.
Why: Readers of a shared link will often be on a phone.
Companies: all
Due: before the site is shared.
Status: open

## 2026-10-28 | Sentence links tested in Chrome only
Theme: Coverage
Item: The one-year bridge links into the 10-K at the quoted sentence (text fragments). Only Chrome was tested; Safari and Firefox may just open the 10-K at the top.
Why: The one-tap citation is the bridge's credibility.
Companies: ODFL
Due: before the site is shared.
Status: open

## 2026-10-30 | Filer quirks at 500 companies
Theme: Coverage
Item: 10 companies tested; 3 refusal modes seen (bank before the revenue fix, no pre-tax calculation link, ticker with a new CIK). The full run will meet more; each must stop the run with an error, never degrade to a wrong number.
Why: A quiet wrong number at scale is worse than a refusal.
Companies: all
Due: the full S&P 500 run.
Status: open

## 2026-11-02 | BA statement does not foot
Theme: Coverage
Item: history.py stops on Boeing's FY2025 10-K (0001628280-26-004357): its 2023 lines foot to +$68.07B against pre-tax income of -$2.005B. About $70B of costs are missing, so a whole branch of the statement is not being read. Cause not yet looked at.
Why: Boeing is a loss company the loss-year chart needs; it cannot reach the chart until it foots.
Companies: BA
Due: before the full S&P 500 run.
Status: closed 2026-11-02, the cost line is tagged only in parts (product and service) with no total; history.py now sums the parts (decisions.md, "A line tagged only in parts is shown summed") and BA foots in every year. Its page still needs ASC 606/842 adoption records before it can be built

## 2026-11-02 | CCL statement off by $1M
Theme: Coverage
Item: history.py stops on Carnival's 10-K (0000815097-26-000007): its 2023 lines foot to -$63M against pre-tax income of -$62M. Footing demands an exact match; a $1M gap looks like the filing's own rounding. Whether to allow rounding slack, and how much, is James's ruling.
Why: An exact footing rule that refuses rounding will stop real companies; a loose one could hide a missing line.
Companies: CCL
Due: before the full S&P 500 run.
Status: closed 2026-11-02, footing allows half a rounding unit per figure summed (decisions.md, "Footing allows the filing's own rounding"); CCL's four $1M gaps pass as rounding rows

## 2026-11-01 | Visual checks are a sample
Theme: Coverage
Item: Searches and arithmetic cover every page; screenshots cover one or two pages per change. A problem of looks on a page not screenshot can slip through.
Why: The sample covers less as the number of pages grows.
Companies: all
Due: the full S&P 500 run.
Status: open

## 2026-10-28 | ODFL revenue remainder split
Theme: Evidence
Item: The +$3.1M revenue remainder on the one-year bridge is attributed to non-LTL revenue, the undelivered-freight deferral and rounding of the freight statistics; the split is not verified.
Why: An unverified attribution on an approved page.
Companies: ODFL. Check: the revenue disaggregation note in the 10-K.
Due: the next time the one-year bridge is opened for changes, or before the site is shared.
Status: open

## 2026-10-28 | ODFL miscellaneous expenses
Theme: Evidence
Item: Miscellaneous expenses (-$8.5M) may include the swing in gains and losses on asset sales (+3.4 to -2.9); not verified.
Why: An unverified attribution on an approved page.
Companies: ODFL. Check: Note 1 and the income statement footnotes.
Due: the next time the one-year bridge is opened for changes, or before the site is shared.
Status: open

## 2026-10-30 | ODFL cost-behavior groups
Theme: Evidence
Item: The one-year bridge's cost-behavior bar order puts each line in a group by judgment, flagged on the page. Checked against the 10-K: operating supplies holds; operating taxes and general supplies fit only partly. Not swapped.
Why: A judgment presented as an ordering.
Companies: ODFL
Due: the next time the one-year bridge is opened for changes.
Status: open

## 2026-10-30 | Quality of earnings (I1)
Theme: Path forward
Item: Run the bridge and the MD&A check every year; persistent drivers are the core trend, and lines that swing back and forth and go undiscussed are candidate cookie jars. Long form in ideas.md, I1, including the GE Capital fact to check.
Why: James's original question: is the core growing, or is something smoothing it?
Companies: ODFL first (insurance and claims, +$17.9M undiscussed in FY2025).
Due: when the ten-year page is settled.
Status: open

## 2026-11-01 | Industries, then the economy (I2)
Theme: Path forward
Item: Add companies up into sub-industries, sectors and the S&P 500, then compare with macro series for elasticities and drivers. Must handle survivorship (today's membership only), fiscal years that do not line up, acquisitions inside the index, GICS changes, foreign revenue, and only ten annual points per company. Long form in ideas.md, I2.
Why: Where James sees the project going.
Companies: all
Due: after the full S&P 500 run.
Status: open

## 2026-10-27 | One-command rebuild
Theme: Path forward
Item: The definition of done names a one-command rebuild; today it is 11 separate scripts run in order.
Why: Part of done.
Companies: all
Due: before the site is shared.
Status: open

## 2026-10-30 | Ship: repo, Pages, README, pin
Theme: Path forward
Item: Create the GitHub repo JamesIsHere/chomper (private or public), serve docs/ on GitHub Pages, write the README in James's words, pin it.
Why: The definition of done, and the way to open the real site on a phone.
Companies: all
Due: James's call on the repo.
Status: open

## 2026-11-01 | Breaks on a stock price chart
Theme: Path forward
Item: Event markers (deals announced and closed, recasts, accounting changes, 10-K filing dates) read most naturally on a chart of the share price, where the market's reaction sits next to the event. Needs a price source; none is in the project today.
Why: James's read while comparing the four break renderings: these markers look better on a price chart than on revenue and income.
Companies: all
Due: after the ten-year breaks have a settled design on the company page.
Status: open

## 2026-11-01 | Company pages link to their considerations
Theme: Path forward
Item: Each company page could list the considerations that touch it.
Why: A reader of one company would see its open items without the full list.
Companies: all
Due: once this list has proven useful.
Status: open

## 2026-11-02 | A renamed tag splits one line into two rows
Theme: Coverage
Item: Carnival tags interest expense us-gaap_InterestExpense in its FY2023 10-K (0000815097-24-000011) and us-gaap_InterestExpenseNonoperating in its FY2025 10-K (0000815097-26-000007), both labeled "Interest expense, net of capitalized interest". history.py keys lines by tag, so the five-year grid shows two rows of that name, each with a value only in its own filing's years; the change columns read the switch as the line vanishing and a new one appearing (+$8.60B and -$2.07B beyond revenue in the Nov 2022 and Nov 2023 columns), which did not happen.
Why: The grid's beyond-revenue amounts for those years are wrong on the page, and a tag change between filings will recur across 500 companies.
Companies: CCL
Due: before CCL's page is called settled, and before the full S&P 500 run.
Status: open

## 2026-11-02 | Five-year in-step split after a loss year
Theme: Presentation
Item: The five-year grid splits each change into what would have happened if every cost moved in step with revenue, and the rest. After a loss year that split scales a negative margin, as the ten-year bars did before they were dropped after loss years: Carnival's Nov 2022 column shows -$51.20B in step and +$54.65B beyond revenue against a +$3.44B pre-tax change, and its line effects (payroll +$6.17B, depreciation +$11.97B beyond revenue) inherit the same scaling.
Why: The grid's beyond-revenue amounts after a loss year do not mean what the page says; the ten-year bars now skip such years, and the grid does not.
Companies: CCL; any company with a loss year in its five.
Due: before CCL's page is called settled, and before the full S&P 500 run.
Status: closed 2026-11-02, decisions.md "No ratio or growth on a loss base"

## 2026-11-02 | Percent change on a loss base in the ten-year table
Theme: Presentation
Item: The ten-year table's change rows print a percent even when the prior year is a loss or the sign flips: Carnival's pre-tax income shows +3188.7% for Nov 2024 (-$62.0M to $1.92B) and +7.1% for Nov 2021 (-$10.25B to -$9.52B), and its operating income -370.6% for Nov 2020. Growth is not defined across a change of sign, which is why the chart's income line already breaks there.
Why: The table states growth the chart refuses to draw; a reader comparing the two sees the contradiction.
Companies: CCL; any company with a loss year in its ten.
Due: before CCL's page is called settled, and before the full S&P 500 run.
Status: closed 2026-11-02, decisions.md "No ratio or growth on a loss base"

## 2026-11-02 | A tighter rule for a loss base
Theme: Presentation
Item: The loss-base rule blanks every split and percent whose base year is zero or a loss. That is broad: a near-zero loss (Carnival Nov 2023, -$62.0M on $21.59B revenue) loses its whole column split, though its scaling barely moves anything. James will look through the loss cases for a tighter rule.
Why: The broad rule is safe but hides some columns that could carry meaning.
Companies: CCL; every company with a loss year.
Due: after the failure census shows how many loss cases there are.
Status: open

## 2026-11-02 | A line summed from parts in some years, whole in others
Theme: Coverage
Item: On 10 companies a line is tagged only in parts in one 10-K and as a single total in the other, and the parts are often one segment ("Insurance and Other", "Truck, Parts and Other"), so their sum may be only a slice of the line. history.py stops on these ("reported by member in ... and whole in ...", census class Member slice) rather than show a jump that is not real.
Why: Summing a slice against a total would put a false change on the page.
Companies: APO BRK-B CTAS DE EL KKR PCAR PSA T WAT
Due: when the census works through Member slice by frequency.
Status: open

## 2026-11-02 | A line printed whole in one 10-K, broken out in the other
Theme: Coverage
Item: Some companies change the statement's layout between the two 10-Ks: RTX prints one "Total costs and expenses" for 2021 and 2022, then Cost of Sales, R&D and SG&A from 2023; FANG's cost of goods and services sold becomes two separate lines. Every year still foots, but the five-year grid shows the old row falling to nothing and the new rows rising from nothing in the column that crosses the change. The census does not count this yet (its split-row signal only catches identical labels).
Why: The crossing column shows changes that are layout, not business.
Companies: RTX FANG (seen); size unknown
Due: before the full S&P 500 run.
Status: open
