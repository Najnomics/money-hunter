# High-water-mark and recapitalization accounting

Family: `hwm-recap-accounting`

After a loss, recapitalization, residual-intent buckets, and high-water marks
decide who owns the recovery. Repeated partial recaps, zero-NAV bootstrap
mints, and unassigned-asset sweeps commonly reset the mark so a later depositor
or a different tranche captures the recovery that the recap funder paid for.

Probe:

- recap, then another recap, then new revenue
- bootstrap mint at zero NAV that dilutes the recap claim
- residual / unassigned buckets paid to the wrong cohort
