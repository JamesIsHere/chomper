# Ideas (future work, not scheduled)

Parked ideas for after the ODFL page ships. Nothing here is decided or planned.

## I1. Multi-year bridges as a quality-of-earnings read (2026-10-30)

Source: James's email to himself, 2026-10-29 (from Ed), captured in a
rust-econ session on 2026-10-30. James's words, verbatim:

> If we had 5 years of data and every year we looked at what they were using
> to justify what happened, you might be able to see if it's a core trend
> that's changing or if there's stuff bouncing up and down all the time (such
> as this insurance stuff). Where did that come from? Does that happen all
> the time? Is that what they use to adjust earnings if they're trying to
> manipulate earnings or pad it? Is that their cookie jar? Is that one of the
> cookie jars they go to?
>
> I think back to General Electric when I look at this stuff and all the
> stuff they did with GE Capital to short up earnings. I want to see the core
> earnings. What funny stuff is happening? If you look at this over time,
> that would just fall out if you see a bunch of different levers that
> they're using to smooth things. Now that's a negative place.
>
> What you might find out also is that the core things are growing at a good
> pace and there's a little noise around it and that's fine. You only really
> get that if you look at 5 years and kind of do the same thing we're doing.

Short form: run the same bridge plus MD&A-coverage check every year, then
separate persistent drivers (core trend) from lines that swing back and forth
and that MD&A leaves undiscussed (candidate smoothing levers). The trigger was
insurance and claims: +$17.9M to operating income in FY25, not discussed in
MD&A (`review.md`, `plan.md`).

Notes (proposals, not decisions):

- Estimate-driven lines are where a cookie jar can sit. Whether ODFL's
  insurance and claims line is mostly a self-insurance accrual: unverified.
  Check the 10-K's claims-liability note. If it is, the reserve roll-forward
  (opening balance, accruals, payments, prior-year development) is a sharper
  test than MD&A silence, because prior-year development shows releases
  directly.
- Five 10-Ks give four year-over-year bridges, which is a small sample to call
  a pattern. XBRL companyfacts goes back further for the standard tags, so more
  years may cost little. Extension tags need the instance files (see the
  plan.md gotcha on companyfacts).

Second pass (2026-10-30 session), James adds:

> What I would not want to see is a GE in the early 2000s, where GE Capital
> is just supporting a big machine. It's just pulling out gains whenever
> they're needed to throw up to the mothership.

- Read: the test is two series, not one. Core (recurring, discussed,
  persistent sign) vs. a residue of small swinging lines. Good = core grows,
  residue is noise around zero. Bad = residue reliably fills the gap
  between core and the number they needed.
- GE Capital's share cap (James recalls ~40% of earnings): unverified. The
  working prior is that a 40% target was announced around 2008, not in the early
  2000s, when the share ran higher. Check before it goes on any page.

Status (2026-10-30): partly started. The five-year cost-response pages (docs/history/) are the first build of this idea; the 10-year headline is the next step.
