// TEST: 11_reject_policy/measurement_feedforward
// KIND: reject_policy
// PURPOSE: Classical feed-forward remains unsupported even if the measured qubit is never reused.
// EXPECTED: Reject under the current unitary + optional terminal-measurement compiler policy; not necessarily invalid QASM.

OPENQASM 3.0;
include "stdgates.inc";

bit[1] c;
qubit[2] q;
h q[0];
c[0]=measure q[0];
if (c[0]) { x q[1]; }
