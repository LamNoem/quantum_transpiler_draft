// TEST: 09_directive_policy/classical_destination_overwrite
// KIND: policy_probe
// PURPOSE: Two final measurements write the same bit; last-write order is significant.
// EXPECTED: Explicit design decision required; do not automatically count as a normalization failure.

OPENQASM 3.0;
include "stdgates.inc";

bit c;
qubit[2] q;
x q[0];
c=measure q[0];
c=measure q[1];
