OPENQASM 3.0;
include "stdgates.inc";

// Grover amplitude amplification: 1 marked item among 8 possibilities.
// Three data qubits, no ancilla, two Grover iterations.
// Marked bitstring in Qiskit order |q[2] q[1] q[0]>: |101>.
// The oracle is hard-coded to that string for a checkable demonstration;
// this toy instance does not claim a useful speedup over knowing the answer.
//
// Expected ideal probability from |000>: P(101) = 121/128 = 0.9453125.
// Every other 3-bit string has probability 1/128 = 0.0078125.
// Test equivalence of the entire unitary as well, not just these probabilities.
//
// Normalizer exercise: standard Toffoli (ccx), a three-qubit gate.
// Its decomposition typically introduces H, CX, T and Tdg, which must then
// be lowered recursively to your internal H/X/RZ/CX basis.
// Global-phase bookkeeping is needed for exact T/Tdg -> RZ substitutions.
//
// No artificial identity-gate padding. The explicit oracle and diffuser
// have basis changes that can cancel after decomposition/composition.
// Do not insert barriers between the oracle and diffusion blocks if you
// want the optimizer to exploit cancellations across their boundary.
// Input count: 43 gate calls (23 H + 16 X + 4 CCX), plus 1 barrier.
// No measurements, resets, classical control, or unbound program inputs.

qubit[3] q;

// Uniform superposition over 000, ..., 111.
h q[0];
h q[1];
h q[2];
barrier q;

// ---- Grover iteration 1: oracle for 101 ----
// Change the zero bit q[1] to 1; CCZ then marks the original 101.
x q[1];
h q[2];
ccx q[0], q[1], q[2];
h q[2];
x q[1];

// ---- Grover iteration 1: diffusion ----
// This H-X-CCZ-X-H block is I - 2|s><s| = -D, with |s> = |+++>.
// Each iteration differs by -1 from the +D convention. Two iterations
// give (-1)^2 = +1, so the complete circuit matches that convention exactly.
h q[0];
h q[1];
h q[2];
x q[0];
x q[1];
x q[2];
h q[2];
ccx q[0], q[1], q[2];
h q[2];
x q[0];
x q[1];
x q[2];
h q[0];
h q[1];
h q[2];

// ---- Grover iteration 2: oracle for 101 ----
x q[1];
h q[2];
ccx q[0], q[1], q[2];
h q[2];
x q[1];

// ---- Grover iteration 2: diffusion ----
h q[0];
h q[1];
h q[2];
x q[0];
x q[1];
x q[2];
h q[2];
ccx q[0], q[1], q[2];
h q[2];
x q[0];
x q[1];
x q[2];
h q[0];
h q[1];
h q[2];
