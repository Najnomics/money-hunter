# Lido Lend pin

**Never submit.** Immunefi accepts reports against **deployed bytecode**, not repository HEAD and not develop branches. This file records the pin used for this campaign.

Harness: Money Hunter (this repo) + Najnomics/boss-skill `audit-map-hunter`. Four gates: divergence, hypothesis, experiment, validate. Three SC passes, then web. PoCs, if any, are fork-of-deployed-contracts only.

## Source of truth

| Field | Value |
|---|---|
| Program | Immunefi Lido bug bounty (Lido Lend assets) |
| Bytecode scope page | https://docs.lido.fi/lend/deployed-contracts/ |
| Audits / deploy verification | https://docs.lido.fi/lend/audits/ |
| Web | https://lend.lido.fi |
| Chain | Ethereum mainnet (chain id 1) |
| Bytecode snapshot | `eth_getCode` `latest` via `https://rpc.mevblocker.io` |
| Block at snapshot | `26508283` (`0x1947bfb`) |
| Hash | keccak256 of runtime bytecode (empty code hashes to `0xc5d24601…`; none of the rows below are empty) |
| Date (UTC) | 2026-11-27 |

Bytecode is the in-scope artifact. Git SHAs below are for reading source that Cyfrin matched to that bytecode, not a license to audit a later main.

## Git pins (releases vs deploy vs HEAD)

Program rule: reports associated with **releases**, not develop. Cyfrin deployment verification used `lend-markets` `9c0ba34`. Lido research post (mainnet deployment) lists deploy commits separately from audit commits; Cyfrin matched the 53 audited files at the deploy commits by digest.

| Repo | Release tag | Tag SHA | Audit commit | Deploy commit (bytecode pin) | Default branch HEAD (do not hunt) |
|---|---|---|---|---|---|
| [lidofinance/lend](https://github.com/lidofinance/lend) | `v1.0.0` | `4d55f1dd98a0f7712543965c66e03c963a004263` | `4d55f1dd98a0f7712543965c66e03c963a004263` | `422d589f9d098124249b54b55306884165833207` | same as `v1.0.0` |
| [lidofinance/lend-irm](https://github.com/lidofinance/lend-irm) | `v1.0.1` | `97af4c39c51f1e023d8025319f34a1658036066c` | `97af4c39c51f1e023d8025319f34a1658036066c` | `566d31f7dfdf83d07a6593f641f7474c263a7f89` | same as `v1.0.1` |
| [lidofinance/lend-markets](https://github.com/lidofinance/lend-markets) | **no tags** | — | `23416c43c4038ea3c00a13d6203949c8f88905cc` | `9c0ba34580ab5cff4354be8cb701419fb02b65d5` | `cfc464c641e7670794b3cac1aa486c2ec7df03a9` (develop merge; **not** the pin) |
| [lidofinance/lend-guardian-daemon](https://github.com/lidofinance/lend-guardian-daemon) | `v0.1.0` | `846f197cd33c7bb3a05facf44db50a45eb27cca4` | MixBytes `b566e019684568e1d505ff25f77b3da4e61fe095` | n/a (off-chain; Immunefi `src/` only) | same as `v0.1.0` |

Related pins named on the audits page (bytecode of the named instances is still in the address table):

| Component | Repo | Tag / commit used at deploy |
|---|---|---|
| Easy Track factories + `LidoLendPreseeder` | lidofinance/easy-track | `4caa9117435631ef352d263c901fa9e26cfccfb4` |
| Circuit Breaker instance | lidofinance/circuit-breaker | tag `1.0.0` `6829a5a962ece56564bd9d72d01c29cabf157579` |
| Bundler3 | morpho-org/bundler3 | commit `9afc2f4` (docs); Lido instance is not shared |

`lend` and `lend-irm`: deploy commits are **ancestors** of the release tags. Cyfrin reported file-digest match for the audited set. This campaign still treats **runtime bytecode** as the object under test.

`lend-markets` HEAD `cfc464c` is a later develop→main merge. Do not score against it.

## Runtime bytecode keccak256

All addresses from the docs page (protocol, bundler/adapters, circuit breaker, exit books, Easy Track factories, proposed WETH/wstETH market). Size is runtime byte length from `eth_getCode`.

Shared ERC-1967 proxy runtime (2018 bytes, keccak `0x489816a1b58525daf440b9ea0e39235cbee14f6647a47285dad65bda0c0fe056`) appears on every listed proxy. Implementation hashes differ.

### Protocol

| Name | Address | Bytes | keccak256 |
|---|---|---:|---|
| LidoLend proxy | `0x026a770badc7126c7252Ef8d407E5b9C56147491` | 2018 | `0x489816a1b58525daf440b9ea0e39235cbee14f6647a47285dad65bda0c0fe056` |
| LidoLend impl | `0xa40Bd2281F54A2D3845F9535b74D2abD946E1911` | 20548 | `0xf882bc080060c8f2a619c2cd6a18798243fdc8cec893f757fdf33be6ee253123` |
| LidoLendOwner | `0x85378a1073E8f338e11A97E090E47e2F0FdD3D5a` | 6055 | `0xe878a8ccd518374a253b27602c049c1594a0179ac87d6ddb92cb4caa768130b7` |
| IrmRouter proxy | `0x81B7cC9523B30429110282d90db2fa90ff443d91` | 2018 | `0x489816a1b58525daf440b9ea0e39235cbee14f6647a47285dad65bda0c0fe056` |
| IrmRouter impl | `0x683eA34c29658fb6cDeCc92Eb4B4e7f766979868` | 3764 | `0x234c06178f1949759a33dd95b351860a2db9ce81509e02ca7444a07ed3e8a97a` |
| AdaptiveCurveIrm | `0xf6f1565F4fD3d29E6bDAb86764A50BCde381422f` | 3627 | `0x883a7881d3ca49825fdbfd0c85fed8649517b7445705e6417e99f2b2a90ca3d0` |
| IrmConfigFactory | `0xE7ce129Eb67970C4d71e1456ad50f84B43C35496` | 5138 | `0x4b9b843759fb083de73c96f187b136d27c3cdb564c18ff27ce965bb7361db38f` |
| LidoLendMarketFactory | `0xBe1C1eaBda3eD8a93D3CE3246cf4EeF8111c76C7` | 15697 | `0xf00672169018c0773fa3b278b311442950c6a3ecaab1b652c5b9df45d46d5d29` |
| RiskStewardDashboard | `0xC3C241bC213EF3ba16234A7c689999209cE515D7` | 5306 | `0x056f70ff33c41e7c8a86818b5f7b8a06e7c92e6c5ecb4d7e7ecf9fed30921914` |
| GuardianSignals impl | `0x66aFC8Bb3aB2f01127fDdEb05425bAD77923091f` | 12526 | `0x759b65fd142cd8ed2bb819ff9ab76f81a60a30f18bce79e1bb057fe2b68a24b4` |
| LidoLendMarketController impl | `0x69136Ab2be05194C0b2773f6E2Cb944bCeb1D6b8` | 24482 | `0x3dd65bcface2718985297052fc6c1a8699f65afdff60b90a03045e2d44179a06` |
| LidoLendERC4626 impl | `0x8549736900BF3e643D7660E6DfDd09B0FBa2E286` | 13311 | `0xa62d4eb77ce4b31fcd493c129347ceb31adcb8d7cdc14ffe3c0783cd5bc25d17` |

### Bundler, adapters, circuit breaker, exit books

| Name | Address | Bytes | keccak256 |
|---|---|---:|---|
| Bundler3 | `0x0056b888E90a1b783311351B54B782dE5de61e87` | 1365 | `0x94f57c1dd1fd8a4d8b095693f49bc71c4c926cba9f5ae01d8e6f3d5cdeac7d66` |
| EthereumGeneralAdapter1 | `0x0C6151F0205A6Edf143b42C4f7B4E97a8f099260` | 13148 | `0xd55e084bd2b7768c448709be0e6c6291d94f9cc53b189033a9d5a2c6bd049786` |
| LidoLendVaultAdapter | `0xb1A64663B5390Ecf1a582df7e19d0a6753d1B84A` | 2179 | `0xb0306c273145c8fa059e3c7bcdb4afe5a8bd68718fc6aa6d7f39b51e70667701` |
| CircuitBreaker | `0xd0A81A130a303237d338A0b5835edcB011Ab3afd` | 3413 | `0x8d4f4df9319d212c0dc3b1a843a5fcab3225e0f75df5e8c656cad49810b0b02c` |
| MorphoExitBook | `0xAd28EFa8f2ef56a68b0Eb6836f4aE1d2D6459Ecd` | 14272 | `0xc06774590c76dc5f94f4d0abf1b6c176d63a5d524dcb6826392cec44dcc66f23` |
| Erc4626ExitBook | `0x0d2580e4c9b20507eDFAeFC7777d760F12Ad55D4` | 11805 | `0xcc74151f3af88ef22034b38f9c225cf54c39e29a1069c8a8b09a402374f0aec5` |

Docs: exit books and `LidoLendExitBookActions` are deployed and **not used by a live market yet**.

### Easy Track factories

| Name | Address | Bytes | keccak256 |
|---|---|---:|---|
| LidoLendPreseeder | `0x3F107d1fbCA49F425321Cb27f6Ef5CbB94a72c41` | 6675 | `0x2277b23c311cd97744a25d0dcdced72a3bc2302d533ffc205f41b1a37144cddd` |
| LidoLendActivateMarket | `0x17bb2A2B5983D29392A5d31D627D4C8B13383fe6` | 6628 | `0xae52b94b846315a71035ccc5f547ca6137b120fcc7a42d52a576d1b0050f38b7` |
| LidoLendCircuitBreakerActions | `0x4e89cc970F0DBAE2f8C38C083D5D345B4F9e76b8` | 3605 | `0xd93df2d21c9539a3364e9111c8945853b1dafdcf8f9fbaffa575f147c1c4ac0b` |
| LidoLendGuardianActions | `0x9fE41afb2114bF9430D7f9B1Fb65f0a4B9DeF779` | 8823 | `0x0ca1af6d3ba0606827044a46c9648d37875d0ce160e9f8f6fa26e846d1a672a8` |
| LidoLendMarketManagerActions | `0x9D75EaE321976e85e472847AFD21246F1f87dC43` | 8268 | `0xa4c9549a8300bb701f3e1b6e4941f96cb32711760e8221ca4e21ec70080e37df` |
| LidoLendRiskStewardActions | `0x7276CE5f92911216d41C7b0A9C3575DE873763E9` | 2510 | `0xfef371cfff398ccecb8a1adff8fec968f5b757ca24565ea14864e20c4f75c0ba` |
| LidoLendApplyIrmConfig | `0x5795E73C0c2007ceD7D65cE4FC21c0C09F14C668` | 3816 | `0x2d4b69b7525bcfe5ff32c4160468371fae6296c935311c542d6077d370f3a134` |
| LidoLendExitBookActions | `0xA30b212c3657fa745feaE4b48B7Eb0A8F429C604` | 4318 | `0x00073a5de18f6650a7767be28f9007ab07c7b9ca1effc5b45a80c0a4ce691eea` |

### WETH / wstETH market (docs: deployed, not activated)

Market id (proposed): `0xe4af8961b4e5a779b85d8c461be1007e4b78a7933976e0a5f23121682020de29`

| Name | Address | Bytes | keccak256 |
|---|---|---:|---|
| LidoLendMarketController proxy | `0xCF1B266d320CA9c0d4e13eF2C46465962F040e88` | 2018 | `0x489816a1b58525daf440b9ea0e39235cbee14f6647a47285dad65bda0c0fe056` |
| LidoLendERC4626 proxy | `0xd8765FA896be3D30A49B9a7d95453E34E2c7A056` | 2018 | `0x489816a1b58525daf440b9ea0e39235cbee14f6647a47285dad65bda0c0fe056` |
| GuardianSignals proxy | `0xc8a8CBBF4c55980F85332fD8470DF0fC52d690aC` | 2018 | `0x489816a1b58525daf440b9ea0e39235cbee14f6647a47285dad65bda0c0fe056` |
| WstEthRateOracle proxy | `0x20a078F9940dC05C46De4153D1bCbd54D2b5b151` | 2018 | `0x489816a1b58525daf440b9ea0e39235cbee14f6647a47285dad65bda0c0fe056` |
| WstEthRateOracle impl | `0xEA67847D37069bF385983c6f58e59dD6011A59a0` | 338 | `0xffd4001480794d11926736ae241463cd4ecf161e3c4fd6c4a8384c80a211df5a` |
| AdaptiveCurveConfig | `0x6076f89f5Cd68c526C73eA1F730d9ce8f05301a6` | 872 | `0x5e8c6c84cb7cf7618db53e82a48be79079f5fc10f2032501ece81e7464930f76` |

Controller / ERC4626 / GuardianSignals implementations for this market are the protocol implementation rows above.

## Out of this pin

- Repo HEAD after the deploy commits (`lend-markets` `cfc464c` in particular).
- Develop / feature branches.
- Morpho Blue / Morpho IRM / Morpho Bundler3 upstream except the Lido-deployed instances listed.
- Guardian daemon files outside `src/`.
- WETH token `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2` (external token on the docs page).
- Committee Safes (role holders, not bytecode under test).

Re-hash before any PoC if a later `eth_getCode` keccak differs from this table.
