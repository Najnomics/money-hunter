# Refundable receipts or fees counted in share price

Family: `refundable-receipt-in-nav`

Vaults and LP tranches often book a temporary inflow (opening fee, pending
yield, rebate, unsettled fill, refundable receipt) into `totalAssets` or the
NAV numerator. An unrelated depositor who mints or redeems while that receipt
is still live transacts at a wrong price. When the receipt is later reclaimed,
the remaining holders eat the difference.

Probe both signs:

- reclaimable **inflow** booked as revenue (inflated share price, redeem-and-run)
- reclaimable **outflow** booked as a loss (deflated share price, mint cheap)

Ignore a nearby hypothesis that died on rounding or a preview-only field. The
question is whether **share price used for settlement** includes reclaimable
amounts.
