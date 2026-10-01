// TEST: 11_reject_policy/measure_then_custom
// KIND: reject_policy
// PURPOSE: A gate hidden inside a custom definition still reuses a measured qubit.
// EXPECTED: Reject under the current unitary + optional terminal-measurement compiler policy; not necessarily invalid QASM.

OPENQASM 3.0;
include "stdgates.inc";

bit[1] c;
gate f(t) a { ry(t) a; }
qubit[1] q;
c[0]=measure q[0];
f(pi/7) q[0];
