// TEST: 10_language_features/alias_slice
// KIND: feature_probe
// PURPOSE: Aliases must refer to existing qubits; do not allocate new wires.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[4] q;
let pair = q[1:2];
ry(pi/7) pair;
cx pair[1],pair[0];
