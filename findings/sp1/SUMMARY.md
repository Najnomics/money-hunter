# SP1 — campaign summary

**Never submit.**

| Field | Result |
|---|---|
| Pin | `succinctlabs/sp1` tag `v6.10.0` = `d83ed91f96701209613720708f36ffce0e98ed33` |
| Harness | `bin/money-hunter` `strict` + four gates; G3 **executed** (`sp1up` cargo-prove `d83ed91`) |
| Passes run | **3 executed** — (1) prover wrap VK + verifier VK root; (2) recursion `test_sumcheck` / failure; (3) runner panic exit_code + JIT remw overflow |
| **Verified count** | **0** |
| Titles / severities | none |
| Strongest dropped lead | L-EXIT non-zero exit_code verify — G3: panic guest `exit_code()==1`; production `verify.rs:295` still requires experimental. JIT REMW overflow **ok** on pin. |
| FINDING files | none |
