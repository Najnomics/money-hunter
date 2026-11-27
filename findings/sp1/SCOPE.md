# SP1 (Succinct) — public Immunefi scope

Sources (public pages only; **never submit; never contact anyone**):

- https://immunefi.com/bug-bounty/sp1/information/
- https://immunefi.com/bug-bounty/sp1/scope/
- https://docs.succinct.xyz/docs/sp1/security/security-model
- https://docs.succinct.xyz/docs/sp1/security/safe-precompile-usage

Captured 2026-11-27 UTC. Latest GitHub release at capture: **v6.10.0**.

## Program

| Field | Value |
|---|---|
| Program | SP1 bug bounty |
| Live since | 21 Sep 2026; last updated 20 Nov 2026 |
| Max bounty | $15,000 |
| Policy | Primacy of Impact for listed Blockchain/DLT impacts |
| PoC | Runnable end-to-end PoC required; ≤10 minutes on Apple M3-class hardware |
| KYC | Not required |
| Publication | Category 3: Approval Required |
| Harness | Money Hunter `strict` + four gates. No submit. No keys. |

## Assets in scope (entire list)

| Target | Path on `succinctlabs/sp1` |
|---|---|
| sp1-core-executor | `crates/core/executor` |
| sp1-core-machine | `crates/core/machine` |
| sp1-hypercube | `crates/hypercube` |
| sp1-recursion | `crates/recursion` |
| sp1-zkvm | `crates/zkvm/entrypoint` |
| sp1-lib | `crates/zkvm/lib` |
| slop (Succinct Library of Polynomials) | `slop/crates/` **excluding** whir, veil, spartan, pgspcs |
| sp1-prover verifier | `crates/prover` (`verify.rs` / `sp1_sdk::prover::Prover::verify`) |
| Primacy of Impact | placeholder asset |

## Severity table (in-scope impacts)

We prioritize soundness on Groth16 and Plonk. Severity may change with class of programs affected.

| Severity | Impact |
|---|---|
| Critical | Soundness: malicious prover forges a false proof for **all 4** proof types (core, compressed, Plonk, Groth16) for a **general class** of programs |
| High | Soundness: forge a false **Compressed** proof for a general class of programs |
| High | Soundness: forge a false **Groth16 and Plonk** proof for a general class of programs |
| Medium | Completeness affecting all proof types and a general class of programs |
| Medium | Soundness that forges a false **core** proof but not compressed or SNARK proofs |

Rewards (Blockchain/DLT, Primacy of Impact): Crit $5k–$15k; High $2k–$5k; Med $1k–$2k.

## Out of scope

- Must reproduce on **latest release** with **production circuits and verification keys** and default production security checks.
- Cargo features/paths solely for `experimental`, `mprotect`, `may_dump_elf`, debug, profiling, dummy, testing, benchmarking, or in-development circuits.
- `proof_nonce` findings.
- Non-zero `exit_code` verification (being marked experimental).
- Compiler feature-set of the Docker images: `sp1-prover/experimental` **off**, `sp1-prover/mprotect` **off**, `sp1-prover/native-gnark` **on**. Demonstrate completeness or soundness in `sp1_sdk::prover::Prover::verify`.
- `whir`, `veil`, `spartan`, `pgspcs` inside `slop`. slop-only bugs that do not affect in-scope SP1 proving/verification.
- Completeness that is not an inherent deterministic incorrectness inside an AIR constraint, recursive circuit, or production verifier. Backend/hardware/resources/concurrency/timeouts/env/user-config failures OOS.
- Soundness without an end-to-end PoC that production verifier accepts a false claim about execution (public outputs that cannot arise from any valid execution consistent with bound inputs).
- Security model / safe precompile usage: must use a memory-safe non-malicious program; ELF from the provided SP1 toolchain; safe precompiles/patched crates; must **not** request a Core proof for an ELF that invokes `VERIFY_SP1_PROOF`. Guest should be standard (Fibonacci / RSP). Findings must apply to a general class of programs using an opcode/syscall normally.
- DoS of prover/verifier, service availability.
- Default Immunefi: third-party oracle data (manipulation still valid), 51%, liquidity, Sybil, centralization, already-exploited, leaked keys, privileged addresses, external depeg, GitHub secrets without production proof, best practices, feature requests, test/config files, phishing.

## Known issues

Program page:

- Security Advisories (9 Sep 2026)
- Previous Bug Bounty Submissions (9 Sep 2026)
- List of Publicly Known Issues (10 Sep 2026)
- Audits: https://github.com/succinctlabs/sp1/tree/main/audits (completed 10 Sep 2026) — unpatched items in those reports are ineligible

v6.10.0 release notes include a JIT `remw` RDX fix (`succinctlabs/sp1#3010`). That class on the **release pin** is a patched/known item for later main, not a new bounty on unfixed prior tags unless it still reproduces **on v6.10.0**.

## PoC / G3 rules for this campaign

- Production verifier settings. No mocks of the verifier contract/property.
- Honest regression: reproduces on pinned release; dies after a minimal fix.
- Never submit.
