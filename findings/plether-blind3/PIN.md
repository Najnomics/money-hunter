# Plether contest pin

**Never submit.** Dorothy: post-audit `Plether-Fi/plether-core` main may already contain fixes. Every recall run must use the Immunefi contest freeze, not that main.

## Contest commit (source of truth)

| Field | Value |
|---|---|
| Contest | Immunefi Audit Competition \| Plether (2–16 Nov 2026) |
| Freeze hash | `a82d4fefb02768e5b3bddcc97dee371eee24fea8` |
| Short | `a82d4fe` |
| Repo | https://github.com/immunefi-team/audit-comp-plether |
| Default branch (`master`) today | **same** `a82d4fe` (`git ls-remote origin HEAD`) |
| Local clone `HEAD` | `a82d4fefb02768e5b3bddcc97dee371eee24fea8` |
| `packages/perps/src` dirty vs HEAD | no |

**Source URLs (contest pages, not the project’s live main):**

- Code Freeze Assurance: https://immunefi.com/audit-competition/plether/information/ — “Code of the assets in scope is frozen at commit `a82d4fefb02768e5b3bddcc97dee371eee24fea8` while the program is live.”
- Scope: https://immunefi.com/audit-competition/plether/scope/ — “The code in scope is commit `a82d4fefb02768e5b3bddcc97dee371eee24fea8`”
- Resources / clone instructions: https://immunefi.com/audit-competition/plether/resources/ — `git checkout --detach a82d4fefb02768e5b3bddcc97dee371eee24fea8`

v2.0.0 Sepolia was built from `1209ca8a5b94a4fb6323c7c4585846ed93db3932`. Contest docs say `packages/perps/src` at that release equals the freeze. That is **not** a second scope pin.

## Not the contest pin

| Ref | SHA | Match freeze? |
|---|---|---|
| `Plether-Fi/plether-core` `master` (2026-11-27 11:35Z, PR #171) | `0fc3cf5106ffb9d792c1ea31109f38657478a7e7` | **no** — post-audit integration; do not score against this |
| Local SCORE-B “patched pin” | freeze + local overlay (min window 15, `minPublishTime+15`, virtual-share headroom), then `git checkout --` restore | overlay only; base remains `a82d4fe` |

## Commits used per run

| Run | Documented pin | Evidence | Match contest `a82d4fe`? |
|---|---|---|---|
| Blind1 | `a82d4fefb02768e5b3bddcc97dee371eee24fea8` | `findings/plether-blind/SCOPE.md`, `README.md`, `PIPELINE.md` | **yes** |
| Blind2 | `a82d4fefb02768e5b3bddcc97dee371eee24fea8` | `origin/cursor/plether-blind2` `SCORE.md`, `SCOPE.md`, `PIPELINE.md` | **yes** |
| Blind3 | `a82d4fefb02768e5b3bddcc97dee371eee24fea8` | `origin/cursor/plether-blind3` `STATUS.md` | **yes** |
| Blind3b (honest SCORE-B / FALSIFY) | `a82d4fe` | `SCORE-B.md`, `FALSIFY.md`; local forge `--root packages/perps` at clone HEAD | **yes** |
| SCORE-C (in progress) | same clone HEAD | generator writes into this pin | **yes** |
| Oracle “buggy pin” | clone HEAD `a82d4fe` | `tools/g3_harness.py` `plether_perps_root()` | **yes** |

No run used `Plether-Fi/plether-core` `0fc3cf5`. No re-pin or re-score is required. SCORE-B and SCORE-C stay on `a82d4fe`.
