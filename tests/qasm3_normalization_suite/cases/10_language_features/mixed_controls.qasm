// TEST: 10_language_features/mixed_controls
// KIND: feature_probe
// PURPOSE: Mixed-polarity controls expose name-only dispatch and ignored ctrl_state.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
negctrl @ ctrl @ x q[2],q[0],q[1];
