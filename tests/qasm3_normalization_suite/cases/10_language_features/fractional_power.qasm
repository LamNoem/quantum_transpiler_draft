// TEST: 10_language_features/fractional_power
// KIND: feature_probe
// PURPOSE: A valid fractional-power feature may require synthesis not currently implemented.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
pow(0.5) @ x q[0];
