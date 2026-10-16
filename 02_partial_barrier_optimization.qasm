OPENQASM 3.0;
include "stdgates.inc";

// Five-qubit optimizer exercise: partial barriers and deeper search.
// Basis: h, x, rz, cx. All angles are numerical and in radians.
// A barrier fences only its listed qubits; it is NOT a global stop.
// Preserve every barrier, including the two adjacent barriers near the end.
// No measurements, resets, control flow, or extra gate definitions.
qubit[5] q;

// A. Retained preparation: creates superpositions and interactions.
h q[0];
h q[3];
cx q[0], q[1];
cx q[1], q[2];
rz(0.17) q[2];
cx q[3], q[4];
rz(0.29) q[4];
barrier q;

// B. Partial fence on q[0] and q[1].
// H(q[0]) and RZ(q[1]) must NOT combine across the partial barrier.
// H(q[3]) and X(q[4]) pairs CAN cancel: their wires are not fenced.
h q[0];
rz(0.125) q[1];
h q[3];
x q[4];
barrier q[0], q[1];
h q[0];
rz(0.375) q[1];
h q[3];
x q[4];
barrier q;

// C. Fencing only the CX target still blocks cancellation of the CX pair.
// Meanwhile the two RZ gates on unfenced q[4] can merge to RZ(0.5).
cx q[0], q[1];
rz(0.125) q[4];
barrier q[1];
cx q[0], q[1];
rz(0.375) q[4];
barrier q;

// D. Fencing only the CX control also blocks cancellation of the CX pair.
// RZ gates on unfenced q[0] can merge to RZ(0.3125).
cx q[2], q[3];
rz(0.125) q[0];
barrier q[2];
cx q[2], q[3];
rz(0.1875) q[0];
barrier q;

// E. Two intervening gates commute with CX on different operands.
// Exposing the CX(0,1) cancellation takes two adjacent commutations.
cx q[0], q[1];
rz(0.1875) q[0];
x q[1];
cx q[0], q[1];

// Same-target CX gates commute; CX(2,4) can cancel, leaving CX(3,4).
cx q[2], q[4];
cx q[3], q[4];
cx q[2], q[4];
barrier q;

// F. RZ merging through a CX on its control: 0.125 + 0.375 = 0.5.
// Also includes straightforward HH and XX pairs.
rz(0.125) q[1];
cx q[1], q[2];
rz(0.375) q[1];
h q[3];
h q[3];
x q[4];
x q[4];
barrier q;

// G. Negative controls: these are NOT the valid patterns above.
// RZ on the CX target does not generally commute with that CX.
cx q[0], q[1];
rz(0.33) q[1];
cx q[0], q[1];
// X on the CX control does not commute with that CX.
cx q[2], q[3];
x q[2];
cx q[2], q[3];
// Reversing control and target does not produce an identical CX pair.
cx q[1], q[4];
cx q[4], q[1];
barrier q;

// H. Adjacent barriers are not an inverse-gate pair: keep BOTH.
// They prevent this H pair from cancelling on q[4].
h q[4];
barrier q[4];
barrier q[4];
h q[4];

// Independent cleanup and retained tail.
x q[0];
x q[0];
rz(0.07) q[2];
h q[2];
