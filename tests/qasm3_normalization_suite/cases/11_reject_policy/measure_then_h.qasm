// TEST: 11_reject_policy/measure_then_h
// KIND: reject_policy
// PURPOSE: A measured qubit is reused by a quantum gate.
// EXPECTED: Reject under the current unitary + optional terminal-measurement compiler policy; not necessarily invalid QASM.

OPENQASM 3.0;
include "stdgates.inc";

bit[1] c;
qubit[1] q;
h q[0];
c[0]=measure q[0];
h q[0];
