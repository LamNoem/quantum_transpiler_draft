OPENQASM 3.0;
include "stdgates.inc";

// Four-qubit transverse-field Ising dynamics on the open chain 0--1--2--3.
// Units: hbar = 1. Hamiltonian: H = -(Z0 Z1 + Z1 Z2 + Z2 Z3)
//                                    - 0.7 (X0 + X1 + X2 + X3).
// Initial state: |++++>. Total time 0.8; 4 second-order Suzuki-Trotter
// steps of dt = 0.2. Each step is X-half / ZZ-full / X-half.
// RX half-step angle = -h*dt = -0.14.
// ZZ full-step angle = -2*J*dt = -0.4.
//
// This is an approximate simulation of exp(-i H*0.8), not exact evolution.
// Optimization must preserve THIS product-formula circuit, including its
// approximation, rather than change the physics model or time step.
//
// Normalizer exercise: RX and a user-defined two-qubit gate.
// No artificial identity-gate padding. Repeated half-layers at neighboring
// Trotter-step boundaries are deliberately left unfused.
// There are NO barriers at those boundaries: they must remain optimizable.
// Input count: 48 gate calls (4 H + 32 RX + 12 zz_rotation), plus 1 barrier.
// After expanding zz_rotation only: 72 gates, including 24 CX.
// No measurements, resets, classical control, or unbound program inputs.

gate zz_rotation(theta) a, b {
    // Exactly RZZ(theta) = exp(-i*theta*Za*Zb/2).
    cx a, b;
    rz(theta) b;
    cx a, b;
}

qubit[4] q;

// Prepare the product state |++++>.
h q[0];
h q[1];
h q[2];
h q[3];
barrier q;

// ---- Trotter step 1 of 4 ----
// First transverse-field half-step.
rx(-0.14) q[0];
rx(-0.14) q[1];
rx(-0.14) q[2];
rx(-0.14) q[3];
// Nearest-neighbor ZZ full-step; these three ZZ terms commute.
zz_rotation(-0.4) q[0], q[1];
zz_rotation(-0.4) q[1], q[2];
zz_rotation(-0.4) q[2], q[3];
// Last transverse-field half-step.
rx(-0.14) q[0];
rx(-0.14) q[1];
rx(-0.14) q[2];
rx(-0.14) q[3];

// ---- Trotter step 2 of 4 ----
// These RX gates can merge with the previous step's final RX layer.
// First transverse-field half-step.
rx(-0.14) q[0];
rx(-0.14) q[1];
rx(-0.14) q[2];
rx(-0.14) q[3];
// Nearest-neighbor ZZ full-step; these three ZZ terms commute.
zz_rotation(-0.4) q[0], q[1];
zz_rotation(-0.4) q[1], q[2];
zz_rotation(-0.4) q[2], q[3];
// Last transverse-field half-step.
rx(-0.14) q[0];
rx(-0.14) q[1];
rx(-0.14) q[2];
rx(-0.14) q[3];

// ---- Trotter step 3 of 4 ----
// These RX gates can merge with the previous step's final RX layer.
// First transverse-field half-step.
rx(-0.14) q[0];
rx(-0.14) q[1];
rx(-0.14) q[2];
rx(-0.14) q[3];
// Nearest-neighbor ZZ full-step; these three ZZ terms commute.
zz_rotation(-0.4) q[0], q[1];
zz_rotation(-0.4) q[1], q[2];
zz_rotation(-0.4) q[2], q[3];
// Last transverse-field half-step.
rx(-0.14) q[0];
rx(-0.14) q[1];
rx(-0.14) q[2];
rx(-0.14) q[3];

// ---- Trotter step 4 of 4 ----
// These RX gates can merge with the previous step's final RX layer.
// First transverse-field half-step.
rx(-0.14) q[0];
rx(-0.14) q[1];
rx(-0.14) q[2];
rx(-0.14) q[3];
// Nearest-neighbor ZZ full-step; these three ZZ terms commute.
zz_rotation(-0.4) q[0], q[1];
zz_rotation(-0.4) q[1], q[2];
zz_rotation(-0.4) q[2], q[3];
// Last transverse-field half-step.
rx(-0.14) q[0];
rx(-0.14) q[1];
rx(-0.14) q[2];
rx(-0.14) q[3];
