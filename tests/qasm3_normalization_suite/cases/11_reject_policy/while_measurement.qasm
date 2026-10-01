// TEST: 11_reject_policy/while_measurement
// KIND: reject_policy
// PURPOSE: Dynamic loops are not a flat unitary circuit.
// EXPECTED: Reject under the current unitary + optional terminal-measurement compiler policy; not necessarily invalid QASM.

OPENQASM 3.0;
include "stdgates.inc";

bit[1] c;
qubit[1] q;
h q[0];
c[0]=measure q[0];
while (c[0]) { x q[0]; c[0]=measure q[0]; }
