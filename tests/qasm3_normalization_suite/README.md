# OpenQASM 3 normalization test suite

201 individually named `.qasm` files. All are OpenQASM 3.0 programs except that
20 intentionally contain syntax or semantic errors. The file extension is
`.qasm`; the language version is declared in the source.

Designed around your saved `Norm` class and its internal basis:

```python
{"h", "x", "rz", "cx"}
```

This is a diagnostic suite, not a claim that your compiler already supports
all these inputs. Each file contains its purpose and intended outcome in
comments. `TEST_INDEX.md` is the human-readable index; `manifest.json` is the
machine-readable version.

## What was and was not verified here

The files and runner were created, Python syntax-checked, and audited for
manifest/path consistency. The independent NumPy checks in `math_checks.py`
were actually executed; their results are in `checks/math_check_results.json`.
They reproduce the saved RY sequence and verify the phase/decomposition
identities discussed below.

**The QASM files and `run_suite.py` have NOT been executed through Qiskit here.**
Qiskit is not installed in the creation environment, and installation was
blocked by unavailable package-network access. Therefore, the expected results
are test specifications, not reported passes on your local code or importer.
`requirements.txt` is not a tested lockfile. Your Qiskit/importer versions can
change which language features import successfully.

No existing project files were changed. The source review refers to the saved
`norm.py` shared earlier, not to any newer local revision.

## Fastest way to use the files

You can feed any individual `.qasm` file into your current loader and normalizer.
For automated checking, extract this directory somewhere inside or alongside
your project. From the suite directory, run:

```bash
python run_suite.py --project-root .. --normalizer norm:Norm --only "01_single_qubit/*"
```

This assumes the parent directory is the import root and `norm.py` is directly
inside it. If your file is `compiler/norm.py`, use `compiler.norm:Norm` instead.
Point `--project-root` to the directory that also makes imports such as
`general.log_config` work. For example:

```bash
python run_suite.py --project-root "C:/path/to/quantum_compiler_draft" --normalizer compiler.norm:Norm
```

Use your existing environment first. In a separate test environment where the
dependencies are missing, install them with:

```bash
python -m pip install -r requirements.txt
```

Do not upgrade a working project environment merely to run these fixtures;
first record and test its current versions. The runner records package versions
in its output report.

Run the complete core coverage, without optional probes and negative inputs:

```bash
python run_suite.py --project-root .. --normalizer norm:Norm --kinds normalize
```

Run every file:

```bash
python run_suite.py --project-root .. --normalizer norm:Norm
```

Without `--normalizer` or `--pipeline`, the runner only checks imports and labels
successful inputs `IMPORT_OK_ONLY`. That does not mean normalization passed.
The default report is `results.json`; use `--report another_name.json` to change it.
Exit code 1 means a tested failure/error; exit code 2 means setup/argument errors.
Exit code 0 does not certify skipped, blocked, or unconnected checks.

## Expected behavior categories

| Kind | Count | Interpretation |
|---|---:|---|
| `normalize` | 140 | Desired supported unitary-body coverage. End in the internal basis and preserve the operation and wires. |
| `feature_probe` | 24 | Valid language features or advanced lowering probes. Import/lowering support may be missing; report it separately. |
| `policy_probe` | 8 | Deliberate design decisions, not unconditional accept/reject tests. |
| `reject_policy` | 9 | Reject under your current unitary computation + optional terminal-readout contract. These are not necessarily invalid QASM. |
| `invalid_qasm` | 20 | Reject syntax/semantic errors in the frontend, before normalization. |

For feature probes, explicit unsupported errors are useful outcomes. A successful
import and a returned circuit are not sufficient: any produced result must still
be correct. The runner does not turn arbitrary Python crashes into successful
rejections.

## Coverage map

| Directory | Files | Main target |
|---|---:|---|
| `00_basics` | 8 | Empty circuits, native gates, fixed points, idle qubits and scalar declarations. |
| `01_single_qubit` | 13 | Isolated Y/Z/S/SDG/T/TDG/SX/ID/RX/RY/P/U lowerings. |
| `02_angles` | 51 | Zero, signs, special and generic angles, tiny nonzero values, 2pi/4pi and larger rotations. |
| `03_symbolic` | 11 | Unbound parameters, expressions, parameter identity, controlled/custom gates and phase-only parameters. |
| `04_two_three_qubit` | 12 | CY/CZ/CH/SWAP/CP/CRX/CRY/CRZ/CU/CCX/CSWAP and asymmetric sequences. |
| `05_custom_recursive` | 10 | Nested and empty gate definitions, 20-level nesting, custom XX/YY/ZZ interactions and cache reuse. |
| `06_wire_mapping` | 8 | Reversed/nonadjacent operands, multiple registers, idle wires and reused substitutions. |
| `07_global_phase` | 11 | Exact phase preservation, accumulation, 2pi rotations, gphase and controlled-relative phases. |
| `08_terminal_measurements` | 8 | Partial/permuted/cross-register readout, measurement-only circuits and per-wire terminality. |
| `09_directive_policy` | 8 | Barriers, repeated readout, overwritten classical destinations, discarded measurements, timing and zero-qubit phase. |
| `10_language_features` | 19 | Inverse/control/power modifiers, open controls, broadcasts, aliases, constants, loops and name collisions. |
| `11_reject_policy` | 9 | Qubit reuse after measurement, reset and classical control. |
| `12_invalid_qasm` | 20 | Syntax, types, arity, indices, duplicate operands, undefined gates and invalid gate definitions. |
| `13_stress` | 6 | Seeded mixed circuits and repeated substitution/cache stress, at most six qubits. |
| `14_optimizer_traps` | 7 | Gate order, illegal commuting/merging, false cancellation and over-aggressive small-angle deletion. |

The suite does not require a topology or routing stage. A gate on q[4],q[1]
is a valid logical-normalization test, not a connectivity violation.

## What the runner checks

It loads QASM with `qiskit.qasm3.load`, constructs a DAG, and calls your function
or class. It does not invoke `transpile()`, basis-translation passes, or a
reference transpiler. `Operator` is used only as the semantic reference/checker.

For each ordinary normalization case it checks:

1. Actual final operations are canonical H, X, RZ and positive-control CX gates,
   not merely generic custom gates with matching names.
2. Logical quantum/classical wire identities, ordering and declared idle bits
   are preserved.
3. The original and normalized full operators agree, rather than comparing only
   the output of |00...0> or computational-basis probabilities.
4. Exact equality and equality up to global phase are reported separately.
5. Symbolic circuits are normalized while unbound, then checked at six fixed
   and eight independently sampled seeded bindings by default. Bindings use
   Parameter objects; parameters may disappear after genuine cancellation,
   but new unrelated Parameter identities must not appear.
6. In normalizer mode, normalizing the output again is a fixed point, and
   normalizing a fresh copy of the input is repeatable.

All matrix-checked test bodies have at most six qubits, so the largest matrix is
64 by 64. No large dense-matrix simulation is hidden in the stress tests.
Symbolic sampling is a regression test, not a mathematical proof for all values.

No exact output gate count is prescribed: many decompositions are valid.
Cancellation and minimum-depth optimization are not prerequisites for a correct
normalization pass. However, any extra optimization you perform must preserve
semantics. The `14_optimizer_traps` inputs help catch errors from combining the
stages too aggressively.

### Exact phase versus physical equivalence

The default `--phase exact` requires matrix equality, including global phase.
To examine whole-circuit physical equivalence separately:

```bash
python run_suite.py --project-root .. --normalizer norm:Norm --phase physical
```

An output that differs only by global phase is labeled
`PASS_UP_TO_GLOBAL_PHASE`, not plain `PASS`. This flag does NOT excuse a relative
phase error inside an already controlled operation.

The reference is the circuit produced by your installed Qiskit importer. This
suite can detect changes made by your normalizer; it is not an independent
certification that the importer implements every OpenQASM feature or phase
convention correctly. Keep its version in your regression reports.

## Keep frontend policy and normalization separate

In `--normalizer` mode, the supplied scaffold removes terminal measurements and
barriers before calling your DAG normalizer. It does not count that removal as
an operation performed by your own code, and it does not claim to test your
readout restoration. Reports explicitly label this limitation.

The scaffold retains classical registers so normalization can be checked for
wire preservation. It accepts unique final readouts with no classical control;
ambiguous cases such as repeated readout and classical overwrite remain policy
probes. A barrier is ignored for unitary comparison; preservation of its
scheduling/fence semantics is not tested by the matrix checker.

To test your input validator, expose an adapter receiving a QuantumCircuit:

```python
# In a module importable from --project-root:
def validate_for_suite(circuit):
    # Call YOUR actual validator here. Convert to DAG first if that is its API.
    # Return None/True on success, False or raise ValueError on policy rejection.
    # Translate only your known domain-rejection exception to ValueError.
    # Do not catch Exception broadly: programming bugs must remain failures.
    return your_actual_validator(circuit)
```

Then add `--validator your_module:validate_for_suite`. Without that hook, negative
policy tests are labeled `NOT_TESTED_POLICY`. Import failure on a valid dynamic
program is labeled `BLOCKED_IMPORT`, not credited as a successful validator test.

To test normalization plus your own terminal-measurement restoration, provide
`--pipeline your_module:normalize_and_restore` instead of `--normalizer`.
That callable must receive and return a QuantumCircuit with the same logical
wire order, including readout. The runner then checks the output readout mapping
as well as the unitary body. This hook is NOT for a routed physical circuit;
placement/routing permutation checking is outside this suite.

### A subtle terminal-measurement decision

```qasm
h q[0];
c[0] = measure q[0];
ry(pi/7) q[1];
c[1] = measure q[1];
```

The first readout is final on q[0], even though unrelated work follows on q[1].
With no classical feed-forward and no later reuse of q[0], that readout can be
moved to the end without changing the circuit's measurement statistics.
A per-wire/DAG-terminal policy can accept it. A stricter textual-suffix policy
can reject it deliberately. This is a `policy_probe`, not a silently assumed
requirement. Gates using a measured wire as either control OR target are
unconditionally rejected under your current unitary-only computation contract.

## Start with these ten tests

Use `--only` with any of these IDs, or open the corresponding file under `cases/`.

| Order | Case ID | Why start here |
|---:|---|---|
| 1 | `01_single_qubit/rx_generic` | Positive control for an explicit rule you already have. |
| 2 | `02_angles/ry_zero` | Exposes the saved RY sequence at the simplest possible value. |
| 3 | `01_single_qubit/ry_generic` | Avoids special-angle coincidences; also tests whether RY is registered. |
| 4 | `07_global_phase/z_vs_rz` | Distinguishes a phase-only loss from a genuinely wrong unitary. |
| 5 | `05_custom_recursive/three_levels` | Detects the saved one-sweep replacement behavior. |
| 6 | `01_single_qubit/U_generic` | Forces you to handle a common fallback endpoint explicitly. |
| 7 | `06_wire_mapping/highest_wire` | Detects local-sub-DAG versus original-qubit indexing mistakes. |
| 8 | `03_symbolic/affine_expressions` | Tests normalization before parameter binding. |
| 9 | `07_global_phase/controlled_two_pi_rotation` | Makes discarded rotation phase observable under control. |
| 10 | `08_terminal_measurements/permuted_readout` | Tests restoration mapping when connected through your pipeline hook. |

## Likely improvements from the saved norm.py

These are observations about the previously shared source, not a claim that
all remain in your newest local version. The complete explanation is in
`KNOWN_ISSUES.md`.

The saved `recursive_normalize` performs one pass over the original operation
nodes and substitutes raw replacement DAGs. It does not recursively normalize
those replacements. `norm_ry` exists but is not in `KNOWN_NORM`, and its saved
sequence is not mathematically RY(theta). The explicit Z/S/SDG/T/TDG rules are
correct only up to a global phase unless their missing phases are tracked.

There is also a source-preservation concern: `orig_dag = dag` followed by
in-place substitution leaves `orig_dag` pointing to the changed graph.
The runner reports aliasing/in-place mutation but does not forbid an in-place
API. Never compare a result against an "original" that is the same mutated DAG.

Add clear errors for unsupported leaf gates, bounded recursion/no-progress
protection, safe operation dispatch, and a final basis postcondition. Keep
measurements/directives outside unitary gate decomposition. Do not require
optimization or routing as part of making normalization correct.

## Additional tests that QASM files alone cannot express well

Legal QASM gate definitions cannot recursively call themselves. Therefore,
a malformed cyclic Python `.definition` object must be tested with a separate
Python fixture; it is not a valid-QASM support case. The invalid recursive QASM
file checks frontend rejection, not an internal decomposition cycle detector.

Other useful Python-level fixtures are an opaque Gate with no definition,
malformed arity in a custom rule, a definition that expands back to itself,
mutable cached replacement DAGs, explicit non-finite gate parameters, failure
partway through an in-place pass, and parameter identity collisions. Also test
that a failure produces a useful error naming the original gate and the
recursive definition path. The repeatability/idempotence checks cover some,
but not all, cache/state errors.

## References

The files use the OpenQASM 3.0 standard library, built-in U and gphase, and
explicit custom definitions where a gate is not in that library. In particular,
RXX/RYY/RZZ examples define their own gates rather than assuming those names
exist in stdgates.inc.

- OpenQASM standard library: https://openqasm.com/language/standard_library.html
- Gate definitions, modifiers and broadcasting: https://openqasm.com/language/gates.html
- Qiskit OpenQASM 3 import: https://quantum.cloud.ibm.com/docs/en/api/qiskit/qasm3
- Qiskit DAG substitution: https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.dagcircuit.DAGCircuit
- Operator.equiv (up to global phase): https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.quantum_info.Operator
- Symbolic parameters: https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.Parameter
- Qiskit RY definition: https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.RYGate
