// TEST: 11_reject_policy/if_else
// KIND: reject_policy
// PURPOSE: Reject control-flow nodes rather than silently normalizing only one branch.
// EXPECTED: Reject under the current unitary + optional terminal-measurement compiler policy; not necessarily invalid QASM.

OPENQASM 3.0;
include "stdgates.inc";

bit[1] c;
qubit[2] q;
c[0]=measure q[0];
if (c[0]) { x q[1]; } else { h q[1]; }
