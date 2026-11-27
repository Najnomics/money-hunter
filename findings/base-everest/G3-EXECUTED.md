# Base Everest — executed G3 (pinned code)

Never submit. All commands `timeout 300`. Pin `b9b76d97` contracts / `0ea0d123` nitro / `689054ee` client.

## Pass 1 — TEE signer registration (L-TEE-001)

```
FOUNDRY_PROFILE=lite forge test --match-contract TEEProverRegistry_RegisterSigner_Test \
  --match-test 'test_registerSigner_unauthorized_reverts|test_registerSigner_debugModePCR0_reverts|test_registerSigner_owner_succeeds' -vv
```

Outcome: **3 passed**. Unprivileged `registerSigner` reverts `OwnableManaged`. Owner path with all-zero PCR0 reverts `InvalidPCR0`. Distinguishing attack does **not** register a production signer.

## Pass 2 — pause, portal finalize, challenge/nullify, TEE verify (L-SYS-001, L-PORTAL-001, L-AGG-*, L-AGG-002)

```
FOUNDRY_PROFILE=lite forge test --match-test 'testFuzz_pause_notGuardianOrIncidentResponder_reverts|testFuzz_unpause_notGuardian_reverts' -vv
FOUNDRY_PROFILE=lite forge test --match-test 'test_finalizeWithdrawalTransaction_targetFails_fails|test_finalizeWithdrawalTransaction_delegatedTargetFails_reverts|test_finalizeWithdrawalTransaction_ifWithdrawalNotProven_reverts' -vv
FOUNDRY_PROFILE=lite forge test --match-path 'test/L1/proofs/{Challenge,Nullify,TEEVerifier}.t.sol' --summary
```

Outcomes: pause/unpause fuzz **2 passed**; portal finalize **3 passed** (after `go build` of `scripts/go-ffi/go-ffi`); Challenge 10 / Nullify 9 / TEEVerifier 7 **all passed**. Unprivileged pause killed. Delegated-EOA failed target **reverts**. `testVerifyFailsWithUnregisteredSigner` / `InvalidProposer` / `ImageIdMismatch` kill forged TEE proofs. Challenge/nullify suites encode intended `gameOver` sequencing, not a missing-auth bug.

## Pass 3 — Nitro library + B20 cap (L-NITRO-001, L-B20-001)

```
forge test --match-test 'test_AttestationReplayHasNoOnChainProtection|test_ParseCert|test_CorruptedSignatureNeverAccepts' -vv
cargo test -p base-common-precompiles --features test-utils --test b20_stablecoin_v1_golden golden_mint_reverts_over_supply_cap
```

Outcomes: nitro **3 passed**. `test_AttestationReplayHasNoOnChainProtection` **passes** — library has no freshness (KI-32 / in-code integrator duty). Corrupted signature never accepts. B20 `golden_mint_reverts_over_supply_cap` **ok**. txpool `mined_replay_id_twin` did **not** compile: librocksdb-sys missing C++ stdlib headers (`<map>`). Not a distinguishing pass for L-POOL-001; remains KI-10 residual, not a finding.

**Verified findings from G3: 0.** No FINDING files.
