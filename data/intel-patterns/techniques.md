# Techniques

- refundable-receipt-in-nav: Share price / NAV / exchange rate must exclude cash or credit a later action can reclaim (pending yield, rebates, refundable fees, temporary receipts).
- share-supply-overflow: Mint, fee-share, or virtual-offset arithmetic near integer max must not freeze convertToShares / convertToAssets / epoch settlement.
- hwm-recap-accounting: Repeated recapitalization, high-water-mark resets, wiped-tranche bootstrap mints, and unassigned residual buckets must not pay the wrong cohort.
- delayed-order-optionality: After a price/mark/fill is public, add-margin, withdraw, liquidation, recap, or window extension must not turn a committed order into a free option.
- oracle-staleness-calendar-watermark: Feed rotation, holiday/weekend overrides, and batch caches must still gate on the oldest component time and the calendar, not the newest tick.
- false-emergency-mode: Degraded/emergency/pause latches must track cash solvency, not hedged pairs or marked-to-market gains counted as backing.
