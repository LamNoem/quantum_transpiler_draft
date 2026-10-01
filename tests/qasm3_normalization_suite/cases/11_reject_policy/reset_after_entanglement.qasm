// TEST: 11_reject_policy/reset_after_entanglement
// KIND: reject_policy
// PURPOSE: Dropping reset changes the computation.
// EXPECTED: Reject under the current unitary + optional terminal-measurement compiler policy; not necessarily invalid QASM.

OPENQASM 3.0;
include "stdgates.inc";

bit[1] c;
qubit[2] q;
h q[0];
cx q[0],q[1];
reset q[1];
