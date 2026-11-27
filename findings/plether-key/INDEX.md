# Unique Plether findings (official Immunefi report)

Official unique paid findings are **63** (18 Critical, 10 High, 11 Medium, 24 Low), plus 45 Insights.
The operator asked for 69; that count is **not** the unique-finding total on the published report (63 paid / 108 including Insights / 917 confirmed submissions / 1,391 total reports).

Chief reports were downloaded from reports.immunefi.com into `unique/`.

| ID | Severity | URL |
|---|---|---|
| 97591 | CRITICAL | https://reports.immunefi.com/plether/97591-sc-critical-housepool-prices-junior-entry-and-exit-with-open-positions-refundable-vpi-in-nav-so-a-trading-lp-takes-incumbent-junior-principal-each-cycle |
| 97677 | CRITICAL | https://reports.immunefi.com/plether/97677-sc-critical-uncollected-flat-short-receivable-is-paid-from-the-other-junior-s-cash |
| 97858 | CRITICAL | https://reports.immunefi.com/plether/97858-sc-critical-owner-controlled-solvency-check-in-orderrouter-executeorder-lets-a-trader-void-and-revive-its-own-pending-open-leading-to-direct-theft-of-user-funds-from-lps |
| 97906 | CRITICAL | https://reports.immunefi.com/plether/97906-sc-critical-delayed-orders-fill-at-a-stale-pyth-tick-at-macro-releases-repeatable-net-profitable-lp-extraction |
| 98014 | CRITICAL | https://reports.immunefi.com/plether/98014-sc-critical-oracle-rotation-resets-accepted-per-feed-watermarks |
| 98035 | CRITICAL | https://reports.immunefi.com/plether/98035-sc-critical-unclamped-open-rebate-after-a-depth-collapse-takes-the-remaining-junior-s-usdc |
| 98172 | CRITICAL | https://reports.immunefi.com/plether/98172-sc-critical-unbounded-junior-share-amplification-reaches-terminal-supply-and-permanently-freezes-lp-funds |
| 98209 | CRITICAL | https://reports.immunefi.com/plether/98209-sc-critical-assignunassignedassets-mints-junior-shares-at-zero-nav-while-the-old-shares-are-still-outstanding-so-one-receiver-takes-the-existing-junior-holders-recovery |
| 98854 | CRITICAL | https://reports.immunefi.com/plether/98854-sc-critical-missing-pending-order-check-in-cfdengine-addmargin-lets-a-trader-rescue-an-increase-that-fails-its-initial-margin-check-at-its-pinned-price-leading-to-direct-theft-of-user-funds-from |
| 98941 | CRITICAL | https://reports.immunefi.com/plether/98941-sc-critical-liquidation-cleanup-refunds-a-pending-open-in-orderrouter-so-an-owner-cancels-its-own-pinned-open-for-free-and-takes-lp-funds |
| 99075 | CRITICAL | https://reports.immunefi.com/plether/99075-sc-critical-junior-maintenance-fee-overflows-accruedtotalsupply-once-junior-supply-is-near-2-256-so-every-settlelpepoch-reverts-forever-and-the-owner-cannot-turn-the-fee-off |
| 99136 | CRITICAL | https://reports.immunefi.com/plether/99136-sc-critical-missing-minimum-execution-window-in-the-orderrouter-commit-check-turns-every-pinned-order-into-a-free-option-and-leads-to-direct-theft-of-lp-funds |
| 99280 | CRITICAL | https://reports.immunefi.com/plether/99280-sc-critical-close-admission-in-orderliquidationbatchlogic-counts-the-account-s-pending-increases-so-an-owner-can-cancel-its-own-committed-close-after-the-pinned-price-prints-leading-to-direct-th |
| 99536 | CRITICAL | https://reports.immunefi.com/plether/99536-sc-critical-missing-pending-order-check-in-cfdengine-settletraderclaim-lets-an-owner-cancel-its-own-pinned-open-after-the-fill-price-is-public-leading-to-direct-theft-of-lp-funds |
| 99589 | CRITICAL | https://reports.immunefi.com/plether/99589-sc-critical-pending-historical-open-lets-a-junior-lp-exit-before-its-already-fixed-trader-liability |
| 99756 | CRITICAL | https://reports.immunefi.com/plether/99756-sc-critical-a-zero-value-senior-head-defers-a-junior-exit-while-admitting-a-new-junior-lp |
| 99855 | CRITICAL | https://reports.immunefi.com/plether/99855-sc-critical-gross-pending-trading-revenue-is-never-netted-against-trader-payouts-letting-junior-lps-withdraw-quarantined-unassignedassets |
| 100087 | CRITICAL | https://reports.immunefi.com/plether/100087-sc-critical-a-partial-close-of-a-claim-backed-position-releases-pledge-down-to-maintenance-1-atom-so-any-keeper-can-liquidate-the-residual-in-the-next-block |
| 97590 | HIGH | https://reports.immunefi.com/plether/97590-sc-high-fully-margined-hedged-pair-lets-any-trader-latch-degraded-mode-and-freeze-lp-deposits-and-trader-margin |
| 97592 | HIGH | https://reports.immunefi.com/plether/97592-sc-high-permissionless-atomic-protection-retries-prevent-owners-from-repairing-close-limits-and-freeze-position-margin-for-over-24-hours |
| 97628 | HIGH | https://reports.immunefi.com/plether/97628-sc-high-near-zero-junior-principal-lets-any-depositor-overflow-the-junior-deposit-quote-and-freeze-all-lp-epoch-settlement-including-senior-redemptions |
| 97760 | HIGH | https://reports.immunefi.com/plether/97760-sc-high-a-leftover-pendingrecapitalizationassets-residual-reserves-lp-free-cash-and-makes-settlelpepoch-revert-every-time-so-lp-exits-stay-frozen-after-an-honest-recapitalization |
| 97844 | HIGH | https://reports.immunefi.com/plether/97844-sc-high-repeated-capped-recapitalization-erases-senior-s-recovery-watermark |
| 97881 | HIGH | https://reports.immunefi.com/plether/97881-sc-high-unredeemable-senior-seed-counted-by-the-junior-withdrawal-covenant-in-housepool-leads-to-temporary-freezing-of-funds-for-at-least-24-hours |
| 97903 | HIGH | https://reports.immunefi.com/plether/97903-sc-high-close-vpi-is-unbounded-at-small-nonzero-net-pool-depth-a-healthy-close-or-keeper-triggered-stop-loss-loses-the-whole-account-balance-in-degraded-mode |
| 97968 | HIGH | https://reports.immunefi.com/plether/97968-sc-high-incomplete-med-12-fix-after-partial-senior-impairment-later-lp-revenue-displaces-the-owner-s-recapitalization-into-unassignedassets |
| 98416 | HIGH | https://reports.immunefi.com/plether/98416-sc-high-calendar-override-days-adjacent-to-the-weekend-exceed-fadmaxstaleness-frozen-closes-liquidations-lp-epoch-settlement-and-withdrawals-revert-for-3-24-h-temporary-freezing-of-funds |
| 99735 | HIGH | https://reports.immunefi.com/plether/99735-sc-high-an-extra-permissionless-settlement-pass-lets-senior-exit-with-housepool-junior-principal |
| 97601 | MED | https://reports.immunefi.com/plether/97601-sc-medium-cfdengine-s-whole-utc-day-calendar-cannot-follow-pyth-s-december-24-and-31-fx-early-close-freezing-open-positions-funds-and-matured-lp-redemptions-for-about-7-hours |
| 97603 | MED | https://reports.immunefi.com/plether/97603-sc-medium-executeorderbatch-reverts-as-a-whole-whenever-pyth-component-publish-times-differ-because-batch-cache-reuse-checks-every-stored-feed-against-the-newest-component-time |
| 97605 | MED | https://reports.immunefi.com/plether/97605-sc-medium-open-admission-spends-cash-already-owed-to-open-winners-so-one-same-price-close-latches-degraded-mode-and-blocks-all-new-trading |
| 97649 | MED | https://reports.immunefi.com/plether/97649-sc-medium-missing-keeper-account-check-plus-under-priced-liquidation-lets-a-trader-liquidate-their-own-position-as-a-fee-free-exit-bypassing-the-50-bps-frozen-close-spread-the-4-bps-execution-fe |
| 97748 | MED | https://reports.immunefi.com/plether/97748-sc-medium-vpi-rebate-is-netted-against-the-protocol-execution-fee-on-skew-reducing-closes-so-the-treasury-loses-up-to-the-entire-close-fee-griefing-damage-to-the-protocol |
| 97848 | MED | https://reports.immunefi.com/plether/97848-sc-medium-temporary-deficits-transfer-unassigned-assets-to-lps |
| 98795 | MED | https://reports.immunefi.com/plether/98795-sc-medium-an-open-or-increase-never-lowers-the-liquidation-reserve-to-its-new-target-so-collateral-the-spec-defines-as-pnl-pledge-is-held-as-reserve-positions-are-liquidated-early-and-the-excess |
| 98994 | MED | https://reports.immunefi.com/plether/98994-sc-medium-collecting-a-marked-trader-loss-transfers-quarantined-assets-to-existing-lp-shares |
| 99422 | MED | https://reports.immunefi.com/plether/99422-sc-medium-med-10-fix-misses-frozen-liquidations-a-capped-short-can-be-liquidated-while-solvent |
| 99501 | MED | https://reports.immunefi.com/plether/99501-sc-medium-a-temporary-favorable-mark-at-the-first-lp-settlement-after-a-recapitalization-strands-the-recapitalization-as-ownerless-value-and-leaves-senior-impaired |
| 99795 | MED | https://reports.immunefi.com/plether/99795-sc-medium-a-pending-full-close-allows-margin-withdrawal-that-waives-vpi-charges-owed-to-the-pool |
| 97600 | LOW | https://reports.immunefi.com/plether/97600-sc-low-anyone-can-plant-a-zero-value-redeem-request-under-another-lp-s-name-so-the-victim-s-erc-7540-redeem-withdraw-maxredeem-and-maxwithdraw-all-report-zero-or-revert-over-a-fully-funded-claim |
| 97602 | LOW | https://reports.immunefi.com/plether/97602-sc-low-a-scheduled-treasury-rotation-changes-the-execution-config-hash-with-no-transaction-so-every-pinned-pending-order-becomes-clearable-by-anyone-and-the-clearer-is-paid-each-victim-s-open-bo |
| 97610 | LOW | https://reports.immunefi.com/plether/97610-sc-low-low-59-fix-is-incomplete-cfdengine-and-cfdengineadmin-still-allow-renounceownership-which-makes-degraded-mode-permanent |
| 97622 | LOW | https://reports.immunefi.com/plether/97622-sc-low-positionprotectionbook-stale-accepted-basket-check-after-order-fills-makes-stop-loss-creation-revert |
| 97715 | LOW | https://reports.immunefi.com/plether/97715-sc-low-recap-after-a-full-tranche-wipe-resets-the-senior-high-water-mark-diverting-senior-restoration-value-to-wiped-junior |
| 97733 | LOW | https://reports.immunefi.com/plether/97733-sc-low-committed-minority-side-increases-can-be-cancelled-after-the-fill-print-for-0-20-usdg-cfdengine-funds-vpi-reserve-from-free-settlement-withdrawable-from-marginclearinghouse |
| 97833 | LOW | https://reports.immunefi.com/plether/97833-sc-low-increase-commits-collect-carry-outside-pinned-limits-contract-fails-to-deliver-promised-returns-but-doesn-t-lose-value |
| 97836 | LOW | https://reports.immunefi.com/plether/97836-sc-low-executeliquidationbatch-stops-at-index-0-on-every-call-when-the-calling-keeper-holds-a-position-because-the-per-item-gas-budget-omits-the-keeper-s-curve-sync-and-carry-realization |
| 97893 | LOW | https://reports.immunefi.com/plether/97893-sc-low-order-execution-applies-the-adverse-confidence-shift-to-the-already-cap-clamped-price-execution-liquidation-parity-break |
| 97971 | LOW | https://reports.immunefi.com/plether/97971-sc-low-self-triggered-position-protection-collects-accrued-carry-outside-the-trader-s-retained-close-limits-and-the-close-s-authenticated-receipt |
| 98039 | LOW | https://reports.immunefi.com/plether/98039-sc-low-committed-open-orders-can-be-cancelled-at-no-cost-after-their-fill-price-is-known-because-any-caller-can-shrink-housepool-depth-through-orderrouter-settlelpepoch-incomplete-fix-of-sc-m4-c |
| 98170 | LOW | https://reports.immunefi.com/plether/98170-sc-low-commit-time-open-preflight-ignores-the-account-s-own-queued-opens-causing-false-rejections-of-valid-increases-and-false-acceptances-that-forfeit-the-execution-bounty |
| 98200 | LOW | https://reports.immunefi.com/plether/98200-sc-low-assesscommittedorder-enforces-close-bounds-in-two-passes-commitment-carry-only-in-the-second-the-public-view-and-the-authenticated-receipt-report-a-non-canonical-constraint-and-an-underst |
| 98575 | LOW | https://reports.immunefi.com/plether/98575-sc-low-withdraw-guard-checks-health-at-the-neutral-cached-mark-but-frozen-window-liquidation-applies-a-side-adverse-shift-to-the-same-mark-a-withdrawal-approved-position-is-liquidatable-in-the-s |
| 98727 | LOW | https://reports.immunefi.com/plether/98727-sc-low-collected-execution-fee-is-reported-fully-recovered-but-its-treasury-delivery-is-cash-capped-the-residual-is-credited-to-no-party-and-survives-the-netting-fix-a-profit-close-at-low-pool-c |
| 98762 | LOW | https://reports.immunefi.com/plether/98762-sc-low-commit-time-open-admission-uses-the-unshifted-mark-so-admitted-opens-fail-at-an-unchanged-price-and-forfeit-their-bounty |
| 98961 | LOW | https://reports.immunefi.com/plether/98961-sc-low-senior-redemption-at-a-few-atoms-of-senior-principal-removes-more-high-water-mark-than-the-redeemed-share-an-exit-of-half-the-shares-cancels-2-3-of-the-recovery-protection-99-903-usdg-bey |
| 99392 | LOW | https://reports.immunefi.com/plether/99392-sc-low-trader-controlled-execution-bounds-let-a-trader-cancel-a-binding-order-after-its-fill-price-is-known-turning-queued-closes-into-a-zero-cost-free-option-paid-for-by-lps |
| 99470 | LOW | https://reports.immunefi.com/plether/99470-sc-low-assignunassignedassets-false-has-no-senior-impairment-gate-so-a-routine-owner-call-lets-junior-capital-in-and-out-while-senior-is-still-below-its-high-water-mark |
| 99551 | LOW | https://reports.immunefi.com/plether/99551-sc-low-close-orders-admitted-against-the-queued-position-projection-are-re-checked-by-the-engine-against-the-live-position-so-a-trader-cannot-queue-its-full-exit-behind-its-own-pending-partial-c |
| 99602 | LOW | https://reports.immunefi.com/plether/99602-sc-low-a-close-committed-while-the-oracle-is-live-loses-its-mev-boundary-if-executed-after-the-freeze-and-settles-at-a-mark-published-before-its-own-committime |
| 99663 | LOW | https://reports.immunefi.com/plether/99663-sc-low-incomplete-low-44-fix-allows-a-dust-partial-close-to-bypass-the-configured-minimum-after-an-earlier-queued-close-fails |
| 99931 | LOW | https://reports.immunefi.com/plether/99931-sc-low-attached-tp-sl-is-armed-at-parent-fill-without-re-checking-trigger-prices-so-a-leg-already-crossed-at-fill-lets-any-keeper-force-close-the-fresh-position-one-block-later |
| 99933 | LOW | https://reports.immunefi.com/plether/99933-sc-low-partial-close-erases-unpaid-carry-when-a-vpi-rebate-is-cash-capped |

## Insights (45 unique, not in the 63 paid set)

| ID | URL |
|---|---|
| 97618 | https://reports.immunefi.com/plether/97618-sc-insight-matured-lp-deposit-requests-have-no-cancellation-path-while-activation-is-deferred-extend-the-senior-hold-escape-to-all-deferral-causes-and-both-tranches |
| 97619 | https://reports.immunefi.com/plether/97619-sc-insight-housepool-and-marginclearinghouse-can-recover-mistakenly-sent-tokens-but-tranchevault-has-no-rescue-path-so-usdg-or-erc-20s-sent-to-it-are-stuck-forever |
| 97644 | https://reports.immunefi.com/plether/97644-sc-insight-setterminalnavbook-does-not-validate-the-book-s-size-quantum-contrary-to-its-natspec-and-security-md |
| 97668 | https://reports.immunefi.com/plether/97668-sc-insight-tranchevault-totalassets-converttoassets-flip-between-two-navs-on-the-60-s-mark-freshness-clock-dropping-collected-revenue-and-hiding-lp-losses |
| 97669 | https://reports.immunefi.com/plether/97669-sc-insight-harmonise-the-free-cash-floor-across-the-four-housepool-payout-callers-the-open-path-rebate-is-the-only-one-that-does-not-apply-it |
| 97689 | https://reports.immunefi.com/plether/97689-sc-insight-frozenclosespreadsettled-reports-the-whole-frozen-spread-as-waived-even-when-lps-retained-part-of-it-through-the-vpi-rebate-netting |
| 97723 | https://reports.immunefi.com/plether/97723-sc-insight-caching-loop-boundaries-and-host-state-eliminates-redundant-staticcalls-in-batch-execution-loop-saving-56-gas |
| 97743 | https://reports.immunefi.com/plether/97743-sc-insight-tranchevault-repeated-wipe-recovery-overflows-bootstrap-share-supply |
| 97793 | https://reports.immunefi.com/plether/97793-sc-insight-pletheroracle-invertpythprice-rounds-half-up-at-1e-26-and-then-floors-to-1e-8-so-inverted-basket-components-are-always-truncated |
| 97794 | https://reports.immunefi.com/plether/97794-sc-insight-ipletheroracle-natspec-contradicts-the-implementation-snapshot-publishtime-is-the-newest-component-time-since-the-med-23-fix-and-empty-payloads-are-valid-replays |
| 97796 | https://reports.immunefi.com/plether/97796-sc-insight-orderrouter-natspec-says-the-oracle-refunds-excess-eth-but-the-router-refunds-it-into-a-ledger-that-emits-no-credit-event |
| 97800 | https://reports.immunefi.com/plether/97800-sc-insight-correct-the-liquidation-documentation-excess-price-loss-is-written-off-not-booked-as-protocol-bad-debt |
| 97871 | https://reports.immunefi.com/plether/97871-sc-insight-liquidation-plan-decides-claim-using-stale-keeper-carry-but-live-execution-realizes-the-keeper-s-carry-first-and-pays-cash-so-planliquidation-and-the-executed-liquidation-disagree |
| 97901 | https://reports.immunefi.com/plether/97901-sc-insight-guardian-settlement-hold-natspec-says-lp-request-admission-is-unaffected-but-the-hold-closes-senior-admission-and-unlocks-committed-senior-deposits |
| 98187 | https://reports.immunefi.com/plether/98187-sc-insight-a-rejected-deposit-epoch-or-a-refund-only-redeem-epoch-stays-at-the-head-of-the-controller-s-queue-so-the-standard-erc-4626-7540-claim-surface-reports-0-and-reverts-while-a-later-epoc |
| 98248 | https://reports.immunefi.com/plether/98248-sc-insight-whitepaper-promises-pre-maturity-cancellation-of-firm-senior-deposits |
| 98249 | https://reports.immunefi.com/plether/98249-sc-insight-security-md-says-frozen-closes-retain-confidence-validation-but-the-oracle-replays-a-cached-mark |
| 98253 | https://reports.immunefi.com/plether/98253-sc-insight-flawed-validation-on-order-admissions-for-opposing-sides-when-failure-is-predictable |
| 98370 | https://reports.immunefi.com/plether/98370-sc-insight-docs-and-natspec-disagree-with-the-code-on-settlement-hold-request-gating-the-router-eth-refund-ledger-and-senior-deposit-cancellation |
| 98441 | https://reports.immunefi.com/plether/98441-sc-insight-remove-the-unreachable-housepool-reconciliation-entrypoint-to-recover-100-runtime-bytes |
| 98532 | https://reports.immunefi.com/plether/98532-sc-insight-clarify-that-uncovered-carry-blocks-partial-close-commitment-instead-of-remaining-unsettled |
| 98536 | https://reports.immunefi.com/plether/98536-sc-insight-opens-whose-execution-window-crosses-the-fad-start-can-be-liquidated-as-soon-as-fad-begins-with-no-price-move |
| 98538 | https://reports.immunefi.com/plether/98538-sc-insight-withdrawal-guard-interfaces-omit-four-blockers-and-misstate-flat-account-and-margin-behavior |
| 98539 | https://reports.immunefi.com/plether/98539-sc-insight-reuse-the-deposit-preflight-s-terminal-wipe-result-to-save-49-256-gas-on-a-senior-request |
| 98540 | https://reports.immunefi.com/plether/98540-sc-insight-remove-the-always-no-op-senior-coupon-checkpoint-helper-to-recover-127-housepool-runtime-bytes |
| 98809 | https://reports.immunefi.com/plether/98809-sc-insight-settlement-hold-natspec-gives-conflicting-request-admission-rules-across-tranche-and-request-type |
| 98816 | https://reports.immunefi.com/plether/98816-sc-insight-document-paused-in-iprotocolviews-instead-of-describing-every-remaining-phase-as-active |
| 98820 | https://reports.immunefi.com/plether/98820-sc-insight-document-that-frozen-degraded-and-terminal-deficit-states-reject-lp-entry-requests |
| 98898 | https://reports.immunefi.com/plether/98898-sc-insight-terminal-receipts-stamp-the-l1-ancestor-block-on-arbitrum-diverging-from-the-l2-commit-block |
| 99154 | https://reports.immunefi.com/plether/99154-sc-insight-housepool-cancelpoolconfigproposal-does-not-emit-an-event-breaking-the-consistent-governance-event-pattern-used-by-all-other-admin-cancel-functions |
| 99180 | https://reports.immunefi.com/plether/99180-sc-insight-deposit-is-the-only-user-facing-function-on-marginclearinghouse-without-nonreentrant-breaking-the-contract-s-otherwise-consistent-reentrancy-guard-pattern |
| 99192 | https://reports.immunefi.com/plether/99192-sc-insight-closepreview-executionfeeassets-natspec-says-the-fee-is-assessed-but-the-field-returns-the-capped-and-credited-value-which-is-zero-when-a-vpi-rebate-absorbs-the-fee |
| 99388 | https://reports.immunefi.com/plether/99388-sc-insight-cei-deviation-in-cfdengine-settletraderclaim-claim-ledger-is-decremented-after-the-external-payout |
| 99417 | https://reports.immunefi.com/plether/99417-sc-insight-liquidations-have-no-sequencer-downtime-grace-period-although-the-repository-s-spot-package-already-implements-one-with-a-sequencer-uptime-feed |
| 99452 | https://reports.immunefi.com/plether/99452-sc-insight-positionprotectionbook-storedprotection-can-be-packed-into-11-slots-instead-of-12 |
| 99453 | https://reports.immunefi.com/plether/99453-sc-insight-repeated-curve-and-carry-work-adds-51-574-gas-to-live-position-withdrawals |
| 99454 | https://reports.immunefi.com/plether/99454-sc-insight-repeated-borrow-base-sync-adds-gas-to-valid-close-commitments |
| 99598 | https://reports.immunefi.com/plether/99598-sc-insight-liquidation-previews-understate-the-account-s-post-liquidation-settlement-by-the-keeper-share-when-the-account-liquidates-itself |
| 99769 | https://reports.immunefi.com/plether/99769-sc-insight-four-identical-pyth-fee-quote-and-require-blocks-in-orderliquidationbatchlogic-can-share-one-helper |
| 99916 | https://reports.immunefi.com/plether/99916-sc-insight-missing-per-leg-price-bounds-in-pletheroracle-allows-extreme-pyth-quotes-price-1-to-silently-distort-the-basket-mark |
| 100049 | https://reports.immunefi.com/plether/100049-sc-insight-full-balance-redemption-exemption-is-checked-after-not-before-a-fallible-pool-pricing-view |
| 100082 | https://reports.immunefi.com/plether/100082-sc-insight-queued-position-projection-walk-pays-two-unused-clearinghouse-reservation-reads-per-pending-order |
| 100084 | https://reports.immunefi.com/plether/100084-sc-insight-realized-carry-settlement-routes-through-the-engine-before-reaching-the-pool-adding-an-unnecessary-transfer |
| 100103 | https://reports.immunefi.com/plether/100103-sc-insight-riskparams-occupies-ten-storage-words-though-seven-of-its-ten-fields-are-tightly-bounded-enough-to-pack-into-one |
| 100115 | https://reports.immunefi.com/plether/100115-sc-insight-enforce-engine-clearinghouse-and-router-host-abi-conformance-at-compile-time |