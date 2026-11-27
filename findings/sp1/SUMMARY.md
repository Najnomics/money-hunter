# SP1 — campaign summary

**Never submit.**

| Field | Result |
|---|---|
| Pin | `succinctlabs/sp1` tag `v6.10.0` = `d83ed91f96701209613720708f36ffce0e98ed33` |
| Harness | `bin/money-hunter` `strict` + four gates |
| Passes | 3 (pipeline on verifier/executor; syscalls; recursion/hypercube/slop) |
| In-scope list | All 8 crates named on Immunefi were in the clone. Deep review: prover `verify.rs`, zkvm lib verify, executor syscalls. Recursion/hypercube/slop sampled, not fully constrained. |
| **Verified count** | **0** |
| Titles / severities | none |
| Strongest dropped lead | Non-zero `exit_code` verification — G1 OOS + production reject at `verify.rs:295` |
| FINDING files | none |
| Apex | 2 DIV, 1 H-* disproved, 0 verified. G3 SNARK not executed (`cargo prove` missing). |
