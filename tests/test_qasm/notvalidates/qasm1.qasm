OPENQASM 3.0;
include "stdgates.inc";

qubit[2] q;
bit[1] c;

h q[0];

c[0] = measure q[0];

x q[0];

cx q[0], q[1];