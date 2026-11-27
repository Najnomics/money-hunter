# SP1 — executed G3 (pin v6.10.0 `d83ed91`)

Never submit. `timeout 300`. Toolchain: cargo-prove `d83ed91` via `sp1up`; rustc 1.83; protoc from `protobuf-compiler`.

## Pass 1 — production verifier artifacts

```
cargo test -p sp1-prover wrap_vk_bytes_deserialize
cargo test -p sp1-verifier test_vk_root_bytes
```

Outcomes: **both ok**. Wrap VK bytes deserialize; recursion VK root matches `VK_ROOT_BYTES`. Not a distinguishing attack (happy-path/code-fact), but proves verifier crate on the pin builds and its pinned keys parse.

## Pass 2 — recursion circuits

```
cargo test -p sp1-recursion-circuit test_sumcheck --lib
```

Outcome: `test_sumcheck` and `test_sumcheck_failure` **ok**. Distinguishing failure path exists in-circuit.

## Pass 3 — L-EXIT / L-REMW re-tests

```
cargo test -p sp1-core-executor-runner test_guest_stderr_forwarding
cargo test -p sp1-jit test_remw_overflow_int_min_mod_minus_one
```

Outcomes: panic guest **exit_code()==1** (runner ok). Production `verify.rs:295` still requires zero exit unless `experimental` (OOS). JIT `i32::MIN % -1` **ok** on pin (v6.10.0 REMW fix). L-REMW is not a live bounty on this pin.

Full `test_verify_core` / Groth16 prove+verify was not run (needs long prove; timeout 300). `Prover::verify` unit path was exercised via wrap VK + verifier crate.

**Verified findings: 0.**
