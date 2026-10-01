// TEST: 10_language_features/integer_power
// KIND: feature_probe
// PURPOSE: Integer powers require complete lowering, not leaving a wrapper gate.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
pow(3) @ rx(pi/7) q[0];
