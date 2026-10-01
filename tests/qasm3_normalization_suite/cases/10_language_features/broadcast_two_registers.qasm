// TEST: 10_language_features/broadcast_two_registers
// KIND: feature_probe
// PURPOSE: Pairwise broadcasting over same-sized registers, not all-to-all connectivity.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[2] a;
qubit[2] b;
h a;
cx a,b;
