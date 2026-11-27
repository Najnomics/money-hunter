# Base Everest — public Immunefi scope

Sources (public pages only; **never submit; never contact anyone**):

- https://immunefi.com/audit-competition/audit-comp-base-everest/information/
- https://immunefi.com/audit-competition/audit-comp-base-everest/scope/
- https://immunefi.com/audit-competition/audit-comp-base-everest/resources/

Captured 2026-11-27 UTC. The policy page is the authority. Mid-Contest Changelog had **no entries** at capture.

## Program

| Field | Value |
|---|---|
| Program | Audit Comp \| Base Everest |
| Status | Live (ends 01 Dec 2026 12:00 UTC) |
| nSLOC (page) | 135,275 |
| Pool | Primary $175,000 + All Stars $50,000 + Podium $25,000. Highest valid severity unlocks: Crit $250k / High $125k / Med $70k / Low $30k / none $20k |
| Policy | Primacy of Rules |
| PoC | Runnable PoC required for every severity. Insights not accepted |
| KYC | Required for payout |
| Harness | Money Hunter `strict` + all four gates (G1 divergence, G2 hypothesis, G3 distinguishing experiment on pinned code, G4 disprove/classify) |
| Operator | Do **not** submit, email, Discord-message, or disclose. Do **not** print or commit keys |

## Assets in scope (entire list)

| Target | Immunefi name | Competition fork |
|---|---|---|
| Offchain components — v1.6.0-rc.9 | base-consensus, base-reth-node, proofs, Everest | https://github.com/immunefi-team/audit-comp-base-everest-base |
| Deployment and upgrade scripts for Base Sepolia | `base/contract-deployments` | https://github.com/immunefi-team/audit-comp-base-everest-contract-deployments |
| Implementation contracts — v8.5.0-rc.1 | pause logic moved from SuperchainConfig into SystemConfig (PR #432) | https://github.com/immunefi-team/audit-comp-base-everest-contracts |
| TEE attestation contracts | NitroValidator, CertManager, P384Verifier + libraries those contracts use | https://github.com/immunefi-team/audit-comp-base-everest-nitro-validator |

Client source baseline: `base/base` **v1.6.0-rc.9**, commit `689054ee14933cb2ee5bd54eadcd8dacbe1cc517`. Declared `base/reth` dependency: `2b20e42de9c42b51ea0fb56599fda3c2f22640ef`. Full SHAs for all forks: `PIN.md`.

All programming languages in the listed assets are covered, subject to exclusions.

### Networks and code in scope

- Everest is **not** live on Sepolia during the competition. Test on the designated local Everest devnet from the pinned commit (`just devnet up everest`).
- Base-native deployed contracts in scope: AggregateVerifier, TEEVerifier, DisputeGameFactory, AnchorStateRegistry, TEEProverRegistry, ProtocolVersions, NitroValidator, CertManager, P384Verifier.
- ZK host + circuits (the zkVM **program**, including Base changes to OP-Succinct) **in**. Soundness bugs **in the zkVM itself** are **out**.
- Everest: Base Transactions (EIP-8430, type `0x79`) and gas-limit billing at the immutable `base/base` commit: encoding, authorization, replay protection, execution, settlement, native nonce/context precompiles, payer RPC when enabled, admission, block building, receipts, batch encoding/derivation, proof-boot Everest gate. Historical EIP-8130 names do not exclude retained functionality.
- Gas-limit billing in scope for standard user txs and Base Transactions when enabled in the Everest environment (execution and proving consistency, settlement, builder reservations, receipt and header accounting).
- OP-derived contracts Base **did** deploy: OptimismPortal2, SystemConfig, DisputeGameFactory, L2ToL1MessagePasser, L1Block, fee vaults, bridge/messenger + factories, listed L2 predeploys.
- In-scope deployment pipeline is `base/contract-deployments`. Deployment scripts **inside** `base/contracts` (e.g. MockVerifier wiring) are test tooling and **out**.
- Also in: Beryl, Cobalt, Denim and Everest code across base-consensus, base-reth-node, B20 precompiles.

### Deployed contracts (Sepolia snapshot 16 Nov 2026)

Ethereum Sepolia block 12,149,624 / Base Sepolia block 59,691,356. These run **earlier** revisions than the pinned commit and do **not** include Everest. They matter only for findings that depend on deployed pre-Everest state, tested on a **local fork**. Source revisions: `base/contracts` v8.4.0 (`8c21f6d0`) for Denim / 20 Oct / 4 Nov deployments; v8.3.0 (`385f21a4`) for Cobalt; `base/nitro-validator` `0ea0d123`; deployments `e6797dfd`. Exceptions: AnchorStateRegistry is v8.0.0 (`ddd5a09e`) plus the 20 Apr 2026 ASR reset patch; DelayedWETH (Multiproof) is v8.0.0 (`ddd5a09e`) unpatched; SystemConfig is v8.3.0 plus `max-gas-limit.patch` (version `3.14.0+max-gas-limit-2000M`). Everest native precompiles come from the local Everest devnet at the competition commit. Devnet L1 contracts at that commit come from bundled setup artifacts, **not** `v8.5.0-rc.1`, unless `base/base#6682` then `#6680` are applied (devnet setup only, not in-scope code). Everest devnet still runs no proposer/prover/challenger; proof components use the proof-component PoC exception.

**Ethereum Sepolia (L1)**

| Contract | Address (may be proxy) | Implementation | Version |
|---|---|---|---|
| AddressManager | `0x709c2B8ef4A9feFc629A8a2C1AF424Dc5BD6ad1B` | n/a | n/a |
| AggregateVerifier (Multiproof) | `0x4234216f1648A8119c6E41e6C0C73956Ecc850Af` | n/a | 0.3.0 |
| AnchorStateRegistry | `0x2fF5cC82dBf333Ea30D8ee462178ab1707315355` | `0xb1cc9f8422042eda9eb36a408002517d7c772ac7` | 3.7.0 |
| CertManager | `0x50521128e3eB8708F05129D7B7283737D55a1936` | n/a | n/a |
| DelayedWETH (Multiproof) | `0xD6e2d9D4f1f8865AC983eE848983fb1979429914` | `0xbbfdb04121b74d8ae7f53fd5238ddef133ab977a` | 1.5.0 |
| DisputeGameFactory | `0xd6E6dBf4F7EA0ac412fD8b65ED297e64BB7a06E1` | `0x9cacf701ef24b8339cd1fdecadde7c080373fb29` | 1.5.0 |
| L1CrossDomainMessenger | `0xC34855F4De64F1840e5686e64278da901e261f20` | `0xb686f13aff1e427a1f993f29ab0f2e7383729fe0` | 2.11.0 |
| L1ERC721Bridge | `0x21eFD066e581FA55Ef105170Cc04d74386a09190` | `0x74f1ac50eb0be98853805d381c884f5f9abdecf9` | 2.9.0 |
| L1StandardBridge | `0xfd0Bf71F60660E2f608ed56e1659C450eB113120` | `0x61525eaacddb97d9184afc205827e6a4fd0bf62a` | 2.8.0 |
| NitroValidator | `0x16970101Ea32243cC80a2e0C91427e8bDA70F689` | n/a | n/a |
| OptimismMintableERC20Factory | `0xb1efB9650aD6d0CC1ed3Ac4a0B7f1D5732696D37` | `0x8ee6fb13c6c9a7e401531168e196fbf8b05ceabb` | 1.10.2 |
| OptimismPortal2 | `0x49f53e41452C74589E85cA1677426Ba426459e85` | `0xa53f56711a2f65c19c1542c98116b98fc07a9bb1` | 6.0.0 |
| P384Verifier | `0xa8320712fF181D74e719Ff7E6E1012bbe4687b26` | n/a | n/a |
| ProtocolVersions | `0x15B721B12CF3b0C4400c8a2935A0Ae391c2eF65b` | `0x1a4c38c954bf25e0aa6831baa0de1497280e09fd` | 1.0.0 |
| ProxyAdmin | `0x0389E59Aa0a41E4A413Ae70f0008e76CAA34b1F3` | n/a | n/a |
| SystemConfig | `0xf272670eb55e895584501d564AfEB048bEd26194` | `0xaeb75e200b9bcf9343ff1a2d2b1b3976e7339ca4` | 3.14.0+max-gas-limit-2000M |
| TEEProverRegistry | `0xf0d7E15673fBA052e83d7f2b26BB6071E86b972e` | `0xf07584cdade9b2a739c682d88987881335c5f12f` | 0.6.1 |
| TEEVerifier | `0x92F6dD3501E51B8b20C77b959becaaebeB210e17` | n/a | 0.2.0 |
| ZkVerifier | `0xa738E13d97A3f10b307C2CD190edd3E227A72D68` | n/a | 0.1.0 (on-chain + ZK host + circuits) |

**Base Sepolia (L2)**

| Contract | Address | Implementation | Version |
|---|---|---|---|
| WETH9 | `0x4200000000000000000000000000000000000006` | n/a | n/a |
| L2CrossDomainMessenger | `0x4200000000000000000000000000000000000007` | `0x4414e1030595860a268b7f14181cf2f88f74c823` | 2.2.0 |
| L2StandardBridge | `0x4200000000000000000000000000000000000010` | `0xb704544947b208f3cf0cf1ce9d9515b6b88d9444` | 1.13.0 |
| SequencerFeeVault | `0x4200000000000000000000000000000000000011` | `0x68f75ea462ad397918b09267cb7ee53e21a2c31d` | 1.6.0 |
| OptimismMintableERC20Factory | `0x4200000000000000000000000000000000000012` | `0x65c5b76e6af6906f29554b8795dfb86976be4f0f` | 1.10.2 |
| GasPriceOracle | `0x420000000000000000000000000000000000000F` | `0x4f1db3c6abd250ba86e0928471a8f7db3afd88f1` | 1.6.0 |
| L1Block | `0x4200000000000000000000000000000000000015` | `0xace2255fb2abb3dd64d5f7ca9b7d8ed812640782` | 1.8.0 |
| L2ToL1MessagePasser | `0x4200000000000000000000000000000000000016` | `0x48823ac5a979c1ab154bf0a4e8ee9d2a5c4d4f29` | 1.2.0 |
| L2ERC721Bridge | `0x4200000000000000000000000000000000000014` | `0x09bbb02383a35fc5aa860d113d9e6a5bf7f80b0c` | 1.10.0 |
| OptimismMintableERC721Factory | `0x4200000000000000000000000000000000000017` | `0x2963d48b49dd3f6bffa9459afe76d8474e1b000c` | 1.4.2 |
| ProxyAdmin | `0x4200000000000000000000000000000000000018` | `0xc0d3c0d3c0d3c0d3c0d3c0d3c0d3c0d3c0d30018` | n/a |
| BaseFeeVault | `0x4200000000000000000000000000000000000019` | `0x8fc73aa5ba43ead89356e1bbc9c249a4e9c32299` | 1.6.0 |
| L1FeeVault | `0x420000000000000000000000000000000000001a` | `0xd9b1b2e960317408dc42903ca59a4832bd173b84` | 1.6.0 |
| OperatorFeeVault | `0x420000000000000000000000000000000000001b` | `0x10A1F82fbff4be64699C411aBf35500F6d7be622` | 1.1.0 |
| EAS | `0x4200000000000000000000000000000000000021` | `0xc919d2c8d3a7b617fea7604b68d862027bd02e64` | 1.4.1-beta.3 |
| EASSchemaRegistry | `0x4200000000000000000000000000000000000020` | `0xbbac3f3b485099f33ea9450299fdd5fc0a2a0a5a` | 1.3.1-beta.2 |
| BaseTime | `0x4200000000000000000000000000000000000030` | `0xc0d3c0d3c0d3c0d3c0d3c0d3c0d3c0d3c0d30030` | 1.0.0 |

**Native contracts (`base/base` at competition commit)**

| Contract | Address |
|---|---|
| B20Factory | `0xB20f000000000000000000000000000000000000` |
| ActivationRegistry | `0x8453000000000000000000000000000000000001` |
| PolicyRegistry | `0x8453000000000000000000000000000000000002` |
| B20 tokens | created by B20Factory |
| Nonce Manager | `0x813000000000000000000000000000000000aa01` |
| Transaction Context | `0x813000000000000000000000000000000000aa02` |

## Severity table (in-scope impacts)

Only these impacts are accepted. An impact that is claimed but not demonstrated does not raise severity. Highest demonstrated impact governs.

**Blockchain/DLT — Critical**

- Direct loss to Base or users ≥ 2.5% of funds held within the Bridge
- Unintended permanent chain split requiring hard fork
- Network not being able to confirm new transactions (total network shutdown: unprivileged exploit prevents the sequencer from including otherwise-valid, adequately funded, fee-paying user txs for ≥ 30 seconds; L1-info + BaseTime-only blocks count as not confirming user txs)
- Permanent freezing of funds held in Base’s canonical bridge, or of users’ native ETH balances on Base (fix requires hardfork). Third-party protocol funds not covered
- Attacker causes a node in supported metrics-only mode to change fork activation from contract data, resulting in total network shutdown, a permanent chain split requiring a hard fork, or acceptance/finalization of an invalid root
- Bypassing required sender or payer authorization, or replay protection, resulting in unauthorized execution of a Base Transaction, delegation or charging
- Draining or stealing funds from the L1 bridge portal

**B20 / Smart Contract — Critical** (severity as if the token held mainnet value)

- Unauthorized minting of a B20 token, or total supply above its supply cap
- Unauthorized transfer or spending of B20 balances, including unauthorized allowance enabling theft
- Attacker-induced permanent freezing of B20 balances, excluding restrictions legitimately imposed through the issuer’s authorized roles, policies or pause
- Unauthorized acquisition or restoration of a B20 role that enables unauthorized minting, seizure, destruction of balances or an equivalent Critical outcome
- Bypassing a required B20 policy restriction or pause, causing unauthorized transfer, unauthorized minting or permanent freezing of B20 balances
- A standalone policy or pause bypass **without** a demonstrated Critical impact is **High**

**Proof soundness / invalid output roots**

- “Invalid TEE or ZK proof” means a proof accepted only through key compromise, forged attestation or a cryptographic break of the prover — OOS unless the report shows how to obtain it. A bug in NitroValidator / CertManager / P384Verifier that accepts an attestation AWS did not sign is a way to obtain one and **stays in**.
- Valid proof of a state transition different from canonical Base execution: **Critical** if the invalid root can also finalize despite Security Council / Guardian emergency actions; **High** when the PoC reaches AggregateVerifier acceptance or stops at the verifier library; **Medium** when it stops at proof generation. Assumption (b) does not apply to this ladder.
- AggregateVerifier accepting an invalid output root, or a game resolving / withdrawal finalizing against one: **Critical**, whatever the path. Assumption (b) may lower it by one level, once. Exception: proof-soundness or execution divergence — acceptance alone is **High**, Critical only if it can also finalize despite emergency actions.

**PoC rules (harness G3 must match)**

- Execute the in-scope code path with Production configuration, including signature checks and gossip validation.
- **No mocks** of a trusted component (preimage oracle, L1 provider, state database, verifier) that break that component’s contract. Executor / tx-pool mocks are invalid. Enclave: local server harness OK if it runs the same request-handling code.
- Default: local Everest devnet (`just devnet up everest`), real binaries, default flags, resource metering **disabled**. Denim 200 ms from L2 block 25; Everest from block 100.
- Local forks of ETH/Base Sepolia or mainnet only when the exploit needs state that exists only there. Forks only, never live. A fork does not bring that network’s deployments into scope.
- Contracts at `v8.5.0-rc.1`: Foundry test in `base/contracts` at competition commit `b9b76d97` with Production config values, **or** local devnet with `#6682` then `#6680`.
- Proof-component exception: component-level PoCs accepted; fixtures may supply surrounding deps if they do not fabricate the vulnerability.
- Validity txs: local devnet only. Public sequencer endpoint testing is prohibited.

## Out of scope

**Base-specific**

- Findings demonstrated only on Base mainnet, public Base Sepolia, Zeronet or other devnets (exceptions: designated local Everest devnet, local forks, component-level PoCs)
- Contracts inherited from Optimism that Base does **not** deploy, even if they appear in `base/contracts`: SuperFaultDisputeGame / super-root game types, OPSuccinctFaultDisputeGame + AccessManager, OPContractsManager. Deployment scripts inside `base/contracts`
- Legacy fault-proof contracts still on Ethereum Sepolia: FaultDisputeGame, PermissionedDisputeGame, MIPS, PreimageOracle and their DelayedWETH proxies
- Findings that only appear under a configuration different from Production, unless an unprivileged way to reach it is shown
- Impacts that require a proposal with an invalid root to resolve without being challenged, blacklisted or retired during its full dispute window (assumption (a))
- Theoretical impacts without proof
- EIP-8130 Keystore code (Zenith account configuration, non-secp256k1 authenticators, account-change types `0x02`/`0x03`), removed from rc.9, and any other code gated to Zenith unless reachable with only Everest active
- `crates/common/evm2` (not the Everest executor)
- Base-operated token-gas payer service (deferred). Core payer authorization/settlement, third-party ERC-8168 payers, and the node’s payer-rpc proxy when enabled **are in**
- Flashblocks components (builder mode, RPC methods, websocket-proxy, `flashblock_index` predicates) when unused in the approved competition configuration. Shared code remains in when reachable
- Legacy NitroEnclaveVerifier, and the RISC Zero and Boundless attestation path
- zkVM **soundness** bugs (the ZK **host/circuits program** remains in)
- Optimism components Base does not deploy (`op-node`, `op-geth`, `op-batcher` as OP Stack clients)
- Legacy endpoints no longer provisioned (authenticated websocket-proxy)
- Experimental/testing modes: `--enable-shadow-indexer`; `--sequencer.shadow-blocks-per-cycle` / `--sequencer.shadow-funding-*`; `--rpc.dev-enabled`; dangerous L1 overrides of DA batch inbox or batcher sender; `--validity-signature-mode`; `--snap.v2` / `--net-if.experimental`; `--pooled-tx-response-soft-limit` / `--pooled-tx-pack-soft-limit`; `--dev*` / `--testing.*` / `testing_buildBlockV1`; `--debug.` CLI (distinct from debug builds / `debug_` RPCs); experimental engine-tuning flags listed on the resources page; payer relay `--rollup.payer-enabled` / `--rollup.payer` (off by default). **Base batcher** `BASE_BATCHER_SHADOW_ENABLED` remains **in** (distinct from excluded shadow-indexer/sequencer)

**Trust boundaries (OOS even if they exceed attributed privileges)**

- Trusted roles: sequencer, batcher, proposer, TEE signers and registrar, Security Council, Guardian
- L1 Ethereum validators/stakers
- Third-party bridge validators (Relay, Across, Axelar, …)
- Base corporate infrastructure not part of the protocol (KMS, deployment pipelines, …)
- Trusted inputs: unsafe-block gossip signed by the unsafe-block signer, Engine API, operator-configured L1/L2 RPC — unless the attacker can inject without controlling the source
- Non-public endpoints: admin/debug/engine/miner/txpool namespaces, `base_insertValidatedTransaction`, prover service, websocket-proxy origin. Public allowlist is listed on the scope page. Local availability of an RPC method does not establish attacker reachability
- RPC resource consumption matching upstream Reth at `base/reth` `2b20e42d` (e.g. `eth_getLogs`, `debug_*`). Base-specific RPC (BaseTime fields) stays in
- Heavy volumetric flooding of public RPC ingress, unless lasting effect needing manual recovery. Temporary DoS unavailability OOS
- Only `eth_sendRawTransaction`, `base_sendRawTransactionValidity`, `eth_sendRawTransactionSync`, `base_transactionStatus` reach block-building nodes. Read-only RPC issues cannot be rated Critical for sequencer/block building

**Default Immunefi OOS:** third-party oracle incorrect data (oracle manipulation/flashloans remain valid); 51%/governance; lack of liquidity; Sybil; centralization; already-exploited damage; leaked keys; privileged addresses without extra privilege grant; external stablecoin depeg not caused by a code bug; secrets in GitHub without proof of production use; best practices; feature requests; test/config files unless stated; phishing/social engineering.

**Intended behavior (not vulnerabilities)** — see program page. Highlights: L1 head only attests blob data from a real L1 block; nullify is a global kill-switch; challenges only counter incorrect TEE proofs; `challenge()`/`nullify()` have no `gameOver()` check; child games of invalid parent are invalid; additional proofs only shorten resolution; TEE proofs centralized (Coinbase); sequencer/op-conductor favours consistency (stall by design); OP Stack-matching behaviour; gas-limit billing receipts use billed gas (limit + payer auth for sponsored Base tx); deposits keep metered gas and pay no L2 execution fee; tx hash is keccak of full EIP-2718 encoding; delegation must use protocol nonce (key 0); validity predicates forbidden on EIP-7702 / delegated senders / Base txs with delegation.

## Known issues (public; not eligible)

Unfixed findings in listed audits (including accepted-risk), limitations in code comments/NatSpec at the in-scope tag, issues publicly disclosed in in-scope repos before launch, and the KI table. Each entry covers **only** the described behavior.

**Issues in public repositories:** KI-02 proof-store init omits storage (#6586); KI-03 validator startup waits indefinitely (#6566); KI-04 pruned heads SyncStart crash (#6505); KI-05 derivation resets stall finalization (#6228); KI-06 lost validity txs not resent (#6450, not planned); KI-07 mixed nonce runs incomplete (#6451, not planned); KI-08 resting validity add build work (#6439); KI-09 deposit receipts incorrect DA (#6602); KI-10 residual nonce-free admission race (#6596); KI-11 stale TEE-signer cohorts serial (#5755); KI-12 background tasks survive shutdown (#6537); KI-13 batcher draining/startup-sync (#6534); KI-41 malformed batch arithmetic panic in debug (#6538); KI-42 preimage length truncates on 32-bit (#6538); KI-47 simulation accepts delegation off protocol nonce (#6652); KI-52 simulation ignores sub-second block time; KI-53 estimates ignore lowered gas-limit override; KI-54 `eth_simulateV1` skips per-tx gas cap; KI-55 `base_transactionStatus` omits included txs; KI-56 channel heads bypass sender slot limit; KI-57 invalid batch recovery differs from proofs; KI-58 eviction by fee cap (**fixed** at competition commit, #6598/#6605/#6646 — only the old ranking is known); KI-59 forwarder batches can exceed client request size (**fix public** #6724 on 24 Nov 2026 — OOS if after changelog); KI-60 validity txs stay pending after sender cannot pay (**fix public** #6726); KI-61 destroyed-account wakes scan every parked storage blocker (**fix public** #6728); P-01 RPC/metrics hang on v1.5.1 (#6230).

**Audit / spec limitations:** KI-14 policy arrays decoded before size checks; KI-15 storage-layout hashing unmetered; KI-16 static-write failures revert vs halt; KI-17 permits accept high-s; KI-18 upgrade identity/coordination; KI-19 incomplete initial upgrade schedule; KI-20 BaseTime proxy hash not validated; KI-21 millisecond timestamp overflow differs; KI-22 zero Denim activation meanings; KI-23 verifier intervals vs prover sampling; KI-24 verifier assumes schedule slot 13 is Denim; KI-25 extra BaseTime setter vs metadata; KI-26 BaseTime setter before activation; KI-27 redirected first deposit stale BaseTime; KI-28 upgrade signal trusts configured L1; KI-29 runtime activation can lack Beryl admin; KI-30 activation-admin fallback config-dependent; KI-31 activation marker survives deactivation; KI-32 Nitro library leaves debug-PCR to callers; KI-33 Nitro cert owner/revoker trusted; KI-40 EIP-8037 state-gas gaps; KI-48 signing domains differ from public EIP-8430 draft; KI-49 pool holds Base txs below current base fee; KI-50 call phases capped at 1,024; KI-51 validity window at millisecond precision.

**Cantina EIP-8430 acknowledged:** KI-34 extra Transaction Context views; KI-36 sidecar replacement discards sender balance; KI-37 declared coinbase tip can boost priority without being paid; KI-43 `eth_estimateGas` ignores DA-footprint limit; KI-44 estimate too low or too high; KI-45 delegated-sender in-flight limit not applied to sidecar; KI-46 pooled Base tx memory size undercounted.

Fixed at competition commit (reference only): KI-01 expiry precision (#6617/#6646); KI-35 pool removal racing readmission (#6253).

Private known issues remain valid until listed in the Mid-Contest Changelog.

## Previous audits (unfixed items OOS)

- Multiproof contracts 1/2 (Cantina)
- TEE contracts 1/2 (Cantina)
- Denim 200 ms blocks; Dynamic Upgrades; Cobalt Dynamic Upgrades; Beryl B20; Beryl precompile storage; Cobalt B20; Nitro validator 2026-08-03 (Cantina PDFs)
- Optimism security reviews including Kona
- Base Azul Audit Competition results

## Assumptions about Base’s response (one-level downgrade each, never a close)

- (a) OOS: invalid-root proposal resolving unchallenged for the full dispute window (5 days with one accepted proof; 1 day after a second proof of the other type; re-extended by `challenge()`/`nullify()`), unless the bug itself is what gets the root past verification/window
- (b) Pre-Impact Bug Monitoring: Base-challenger + Guardian blacklist/retire may lower invalid-root-past-verification by one level if 100% detection+prevention is objectively shown
- (c) Restart lowers by one only when documented config restart clears it
- (d) Compromising Base-operated infrastructure is OOS (exclusion, not a downgrade)

## Production configuration (PoC must use)

Operator fee scalar/constant = 0. Resource metering off (remove `--builder.enable-resource-metering` on local docker). Bundles not live. Cancun+ active. AggregateVerifier 0.3.0 intervals 600/30 slow, 6000/300 fast (Denim active → use fast). ZK verifier = ZkVerifier. TEE fleet typical 4×39.06 GiB. Fork PoCs use **mainnet** delays (1 day), not Sepolia’s 0. Everest env: gas-limit billing on; keystore removed; payer RPC off; mempool by declared coinbase tip / gas_limit; 16 per payer, 64 per allowlisted payer; Base cost 12,000 gas; payer auth 5,100; MAX_CALL_PHASES 1024; MAX_ACCOUNT_CHANGES 1; nonce-free window 30,000 ms inclusion / 20,000 ms mempool; replay ring 340,000; domains `0x7900`/`0x7901`/`0x7902`.

## Campaign constraints

- Cover the **entire** in-scope list across three independent passes.
- A candidate is a **finding** only if it passes G1–G4 **and** an honest regression: reproduces on the pinned real code or a fork of real deployed state, and stops reproducing after a minimal fix. **No mocks.**
- Confirmed items only: `FINDING-*.md` and `FINDING-*.txt`.
- Every lead, including drops: `LOG.md` and `SUMMARY.md`.
