# Installed toolchains (G3 execution)

Never submit. Never print keys. Environment-only installs on 2026-11-27; not part of any Immunefi pin.

| Tool | How | Version / pin |
|---|---|---|
| Foundry installer | `timeout 300 bash -c 'curl -L https://foundry.paradigm.xyz \| bash'` | foundryup at `~/.foundry/bin` |
| Foundry | `timeout 300 foundryup` | forge 1.10.1 (`7c15a1dd0c`, 2026-11-26) |
| Rust | preinstalled | rustc 1.83.0 (`90b35a623`) |
| SP1 installer | `timeout 300 bash -c 'curl -L https://sp1up.succinct.xyz \| bash'` | `~/.sp1/bin/sp1up` |
| SP1 | `timeout 300 sp1up` | cargo-prove sp1 `d83ed91` 2026-10-23 (matches SP1 pin v6.10.0) |

PATH for later steps: `$PATH:/home/ubuntu/.foundry/bin:/home/ubuntu/.sp1/bin`

Next: install Everest `just deps` (not the Immunefi source pin; Foundry libs), then execute G3 / forge / cargo / fork tests.
