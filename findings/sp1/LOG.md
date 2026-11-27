# SP1 campaign log

Never submit. Pin `v6.10.0` `d83ed91f96701209613720708f36ffce0e98ed33`. Four gates. No FINDING without G3 on production `Prover::verify`.

## Pin

`git -C /agent/repos/sp1 rev-parse HEAD` = `d83ed91f96701209613720708f36ffce0e98ed33`. Matches latest GitHub release tag. `main` is **not** the pin.

## Passes

| Pass | Method | Surfaces | G3 |
|---|---|---|---|
| 1 | cargo verifier/prover | wrap VK deserialize; `test_vk_root_bytes` | both ok |
| 2 | cargo recursion circuit | `test_sumcheck`, `test_sumcheck_failure` | both ok |
| 3 | cargo runner + JIT | panic exit_code; remw i32::MIN%-1 | both ok; L-EXIT still OOS |

## Leads

| ID | Claim | Gate | Disposition |
|---|---|---|---|
| L-EXIT | Non-zero exit_code verifies | G3 kill / OOS | Runner panic exit_code==1; `verify.rs:295` still experimental-gated. |
| L-NONCE | proof_nonce soundness | G1 kill | Program OOS. Cross-shard equality checked at 301–314. |
| L-NEST | Core proof of `VERIFY_SP1_PROOF` ELF | G1 kill | Security model OOS. Minimal ecall returns `Ok(None)` for that syscall (deferred). |
| L-REMW | x86 JIT remw i32::MIN % -1 | G3 kill | `test_remw_overflow_int_min_mod_minus_one` PASS on pin. |
| L-SLOP | slop whir/veil/spartan/pgspcs | G1 kill | Named OOS crates. |
| L-EXP | experimental / mprotect / dummy circuits | G1 kill | Feature OOS. |
| L-DIV-MAP | Apex unmapped F-VER/F-EXEC | n/a | Matcher noise; functions exist at `verify.rs:109`. |

G3 executed 2026-11-27 after `sp1up`. Commands: `G3-EXECUTED.md`. Full Groth16/core prove+verify not run (timeout 300). **Verified: 0.**

## Strongest dropped lead (executed)

**L-EXIT:** verifying a failed guest as successful. G3: `test_guest_stderr_forwarding` **PASS** (panic `exit_code==1`). `verify.rs:295` still rejects non-zero without `experimental` (OOS). **L-REMW:** `test_remw_overflow_int_min_mod_minus_one` **PASS** on v6.10.0.
