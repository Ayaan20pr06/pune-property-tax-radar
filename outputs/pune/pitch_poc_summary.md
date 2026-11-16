# Pune operational POC

## What was built

A reproducible workflow that turns historical municipal tax records and satellite building layers into a ward-level screening queue.

- 24/24 Sampark tax rows mapped into 15/15 historical administrative wards.
- 15/15 administrative wards matched to satellite building-area and volume measures.
- 15/15 wards have positive building measures.
- Tax-roll totals reconcile after aggregation: built properties 870,655; total ARV ₹10,062,841,704; annual demand ₹10,431,565,925.
- The workflow produces a ranked, human-review queue rather than an automated assessment.

## What the Pune run says

The data-integration workflow is operational. The small Pune sample does **not** establish that built form alone can rank tax-base gaps: n=15, built-area Spearman rho=0.300, and location value differences are not controlled.

## Product thesis to test next

With a larger multi-city training set, a location-aware expected-ARV baseline, and independently observed inspection outcomes, the same workflow can prioritize field checks where observed value is low relative to built form and local market context.

## Honest pitch line

“Instead of commissioning a city-wide resurvey before knowing where to look, municipalities can begin with a repeatable screening layer that directs scarce inspection capacity. Pune demonstrates the end-to-end data and decision workflow; the next phase measures ranking quality across cities and inspection outcomes.”

## Do not claim

- That Pune’s current ranking identifies omissions.
- That residuals represent non-compliance or tax evasion.
- That 15 wards establish a general relationship.
