// TEST: 10_language_features/controlled_gphase
// KIND: feature_probe
// PURPOSE: Controlled global phase is a one-qubit phase operation, not ignorable metadata.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
ctrl @ gphase(pi/7) q[0];
