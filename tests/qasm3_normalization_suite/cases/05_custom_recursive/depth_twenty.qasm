// TEST: 05_custom_recursive/depth_twenty
// KIND: normalize
// PURPOSE: A linear 20-level definition chain should terminate; detect depth limits without exponential expansion.
// EXPECTED: Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.

OPENQASM 3.0;
include "stdgates.inc";

gate layer0(t) a { ry(t) a; }
gate layer1(t) a { layer0(t) a; rz(pi/101) a; }
gate layer2(t) a { layer1(t) a; rz(pi/101) a; }
gate layer3(t) a { layer2(t) a; rz(pi/101) a; }
gate layer4(t) a { layer3(t) a; rz(pi/101) a; }
gate layer5(t) a { layer4(t) a; rz(pi/101) a; }
gate layer6(t) a { layer5(t) a; rz(pi/101) a; }
gate layer7(t) a { layer6(t) a; rz(pi/101) a; }
gate layer8(t) a { layer7(t) a; rz(pi/101) a; }
gate layer9(t) a { layer8(t) a; rz(pi/101) a; }
gate layer10(t) a { layer9(t) a; rz(pi/101) a; }
gate layer11(t) a { layer10(t) a; rz(pi/101) a; }
gate layer12(t) a { layer11(t) a; rz(pi/101) a; }
gate layer13(t) a { layer12(t) a; rz(pi/101) a; }
gate layer14(t) a { layer13(t) a; rz(pi/101) a; }
gate layer15(t) a { layer14(t) a; rz(pi/101) a; }
gate layer16(t) a { layer15(t) a; rz(pi/101) a; }
gate layer17(t) a { layer16(t) a; rz(pi/101) a; }
gate layer18(t) a { layer17(t) a; rz(pi/101) a; }
gate layer19(t) a { layer18(t) a; rz(pi/101) a; }
gate layer20(t) a { layer19(t) a; rz(pi/101) a; }
qubit[1] q;
layer20(pi/7) q[0];
