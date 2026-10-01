// TEST: 11_reject_policy/reset_first
// KIND: reject_policy
// PURPOSE: Reset is outside the chosen unitary-only computation model, even at the beginning.
// EXPECTED: Reject under the current unitary + optional terminal-measurement compiler policy; not necessarily invalid QASM.

OPENQASM 3.0;
include "stdgates.inc";

bit[1] c;
qubit[1] q;
reset q[0];
h q[0];
