# SP1 campaign log

Never submit. Pin `v6.10.0` `d83ed91f96701209613720708f36ffce0e98ed33`. Four gates. No FINDING without G3 on production `Prover::verify`.

## Pin

`git -C /agent/repos/sp1 rev-parse HEAD` = `d83ed91f96701209613720708f36ffce0e98ed33`. Matches latest GitHub release tag. `main` is **not** the pin.

## Passes

| Pass | Method | Surfaces |
|---|---|---|
| 1 | Money Hunter `strict` on `verify.rs`, zkvm lib verify, `crates/core/executor/src` | Apex: 2 DIV (unmapped name matcher), 1 H-*, 1 prepared E-*, H-0001 disproved, **0 verified** |
| 2 | Boss-skill executor/syscalls | `VERIFY_SP1_PROOF` (`0x1B`), nested verify lib, minimal ecall `Ok(None)` for nested/commit |
| 3 | Boss-skill recursion/hypercube/slop | `crates/recursion`, `crates/hypercube`, `slop/crates` excluding whir/veil/spartan/pgspcs; v6.10.0 REMW JIT note |

## Leads

| ID | Claim | Gate | Disposition |
|---|---|---|---|
| L-EXIT | Non-zero exit_code verifies | G1 kill | `verify.rs:295` rejects unless `experimental`. Immunefi OOS. DP-0001. |
| L-NONCE | proof_nonce soundness | G1 kill | Program OOS. Cross-shard equality checked at 301–314. |
| L-NEST | Core proof of `VERIFY_SP1_PROOF` ELF | G1 kill | Security model OOS. Minimal ecall returns `Ok(None)` for that syscall (deferred). |
| L-REMW | x86 JIT remw i32::MIN % -1 | G1 kill | Completeness must be AIR/circuit/verifier, not JIT backend. v6.10.0 changelog lists this as a **fix in the pin**. |
| L-SLOP | slop whir/veil/spartan/pgspcs | G1 kill | Named OOS crates. |
| L-EXP | experimental / mprotect / dummy circuits | G1 kill | Feature OOS. |
| L-DIV-MAP | Apex unmapped F-VER/F-EXEC | n/a | Matcher noise; functions exist at `verify.rs:109`. |

No G3 SNARK/core end-to-end run (`cargo prove` not installed). **Verified: 0.**

## Strongest dropped lead

**L-EXIT:** verifying a failed guest (non-zero exit) as a successful execution. Dies because production verify already requires zero exit_code and Immunefi marks the remaining experimental path OOS.
