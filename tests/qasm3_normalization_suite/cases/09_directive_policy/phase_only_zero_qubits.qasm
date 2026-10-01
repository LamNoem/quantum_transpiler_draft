// TEST: 09_directive_policy/phase_only_zero_qubits
// KIND: policy_probe
// PURPOSE: Decide whether zero-qubit, pure-global-phase programs are inside the compiler input contract.
// EXPECTED: Explicit design decision required; do not automatically count as a normalization failure.

OPENQASM 3.0;
include "stdgates.inc";

gphase(pi/7);
