// TEST: 11_reject_policy/measured_qubit_as_target
// KIND: reject_policy
// PURPOSE: Measurement followed by using that qubit as a CX target is not terminal.
// EXPECTED: Reject under the current unitary + optional terminal-measurement compiler policy; not necessarily invalid QASM.

OPENQASM 3.0;
include "stdgates.inc";

bit[1] c;
qubit[2] q;
c[0]=measure q[1];
cx q[0],q[1];
