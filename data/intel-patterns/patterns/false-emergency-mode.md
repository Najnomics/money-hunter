# False degraded or emergency-mode trigger

Family: `false-emergency-mode`

Circuit breakers, degraded mode, and emergency pause must track **cash
solvency**, not marked-to-market fiction.

Probe:

- hedged / offsetting pairs that cancel in cash but trip a per-side predicate
- admission that counts unrealized gains as backing
- a latch that freezes LP settlement while trader surplus can still leave
- the inverse: backing is gone and the latch never fires
