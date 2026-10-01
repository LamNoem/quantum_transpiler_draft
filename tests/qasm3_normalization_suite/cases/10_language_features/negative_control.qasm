// TEST: 10_language_features/negative_control
// KIND: feature_probe
// PURPOSE: Open controls must not be treated as ordinary positive controls.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
negctrl @ x q[1],q[0];
