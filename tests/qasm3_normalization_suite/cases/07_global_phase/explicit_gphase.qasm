// TEST: 07_global_phase/explicit_gphase
// KIND: feature_probe
// PURPOSE: Preserve an incoming circuit global phase through DAG conversion and substitution.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

qubit[1] q;
gphase(pi/7);
h q[0];
