// TEST: 10_language_features/ctrl_x
// KIND: feature_probe
// PURPOSE: A control modifier prepends the control wire; it is not another parameter.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
ctrl @ x q[1],q[0];
