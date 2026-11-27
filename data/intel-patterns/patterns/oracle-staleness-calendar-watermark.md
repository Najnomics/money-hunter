# Oracle staleness, calendar, or watermark

Family: `oracle-staleness-calendar-watermark`

Aggregated prices fail closed only if every component is fresh **and** on the
intended calendar.

Probe:

- rotating a feed that resets per-source timestamps
- a batch cache keyed to the newest component instead of the oldest
- holiday/weekend overrides that disagree with max-staleness
- the first post-commit tick landing on a scheduled macro release
