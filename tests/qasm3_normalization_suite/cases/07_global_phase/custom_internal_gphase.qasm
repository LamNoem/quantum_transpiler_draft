// TEST: 07_global_phase/custom_internal_gphase
// KIND: feature_probe
// PURPOSE: Global phase stored inside a gate definition must be added during substitution.
// EXPECTED: Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.

OPENQASM 3.0;
include "stdgates.inc";

gate phased(a) t { gphase(a/3); rx(a) t; }
qubit[1] q;
phased(pi/7) q[0];
