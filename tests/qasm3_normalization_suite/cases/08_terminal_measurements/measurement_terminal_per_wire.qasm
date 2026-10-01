// TEST: 08_terminal_measurements/measurement_terminal_per_wire
// KIND: policy_probe
// PURPOSE: The first measurement is terminal on its own qubit even though unrelated quantum work follows.
// EXPECTED: Explicit design decision required; do not automatically count as a normalization failure.
// NOTE: DAG/per-wire terminality can accept this safely when no classical result is read; a stricter textual-suffix policy may reject deliberately.

OPENQASM 3.0;
include "stdgates.inc";

bit[2] c;
qubit[2] q;
h q[0];
c[0]=measure q[0];
ry(pi/7) q[1];
c[1]=measure q[1];
