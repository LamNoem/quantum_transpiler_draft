// TEST: 10_language_features/inverse_s
// KIND: feature_probe
// PURPOSE: Inverse modifiers may import as sdg or a wrapped inverse operation.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
inv @ s q[0];
