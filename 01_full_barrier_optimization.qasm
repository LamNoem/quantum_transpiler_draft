OPENQASM 3.0;
include "stdgates.inc";

// Four-qubit optimizer exercise: full-register barriers.
// Basis: h, x, rz, cx. All angles are numerical and in radians.
// No measurements, resets, control flow, or extra gate definitions.
// Preserve every barrier. Comments describe local opportunities, not
// a mandatory final circuit for every beam width/search depth.
qubit[4] q;

// A. Nontrivial preparation plus adjacent simplifications.
// Keep the preparation; remove the HH, XX, and identical CX pairs.
// The three RZ gates on q[3] can merge to RZ(0.3125).
h q[0];
cx q[0], q[1];
rz(0.17) q[1];
cx q[1], q[2];
h q[3];
cx q[2], q[3];
h q[2];
h q[2];
x q[0];
x q[0];
rz(0.125) q[3];
rz(0.25) q[3];
rz(-0.0625) q[3];
cx q[0], q[2];
cx q[0], q[2];
barrier q;

// B. Two separate commutation-enabled cancellations.
// RZ on a CX control commutes with CX: the first CX pair can cancel.
// X on a CX target commutes with CX: the second CX pair can cancel.
cx q[0], q[1];
rz(0.375) q[0];
cx q[0], q[1];
cx q[2], q[3];
x q[3];
cx q[2], q[3];
barrier q;

// C. Same-control CX gates commute; the two CX(0,1) gates can cancel.
// On q[3], do NOT merge RZ gates through H using an RZ-commutation rule.
cx q[0], q[1];
cx q[0], q[2];
cx q[0], q[1];
rz(0.125) q[3];
h q[3];
rz(0.25) q[3];
barrier q;

// D. Deliberate fence: matching H and X gates must NOT cancel across it.
// The two RZ gates on q[2] must also remain on opposite sides.
h q[0];
x q[1];
rz(0.1875) q[2];
barrier q;
h q[0];
x q[1];
rz(0.3125) q[2];
barrier q;

// E. Another deliberate fence: the identical CX gates must NOT cancel.
cx q[1], q[3];
barrier q;
cx q[1], q[3];

// Nontrivial tail: the whole circuit is not just an identity exercise.
rz(0.11) q[0];
h q[0];
cx q[0], q[2];
