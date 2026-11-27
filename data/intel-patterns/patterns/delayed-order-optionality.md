# Delayed-order optionality after the price print

Family: `delayed-order-optionality`

Queued orders that "cannot be cancelled" are still options if, after the
price/mark/fill is public and before execute, someone can:

- withdraw or re-pledge free balance the fill needs
- add margin so a failing order becomes profitable
- liquidate, recapitalize, or stretch the execution window

The committed terms must still bind. A refund-plus-keeper-bounty after a public
print is a free option, not a binding order.
