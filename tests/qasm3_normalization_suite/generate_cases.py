# Regenerates cases/, manifest.json and TEST_INDEX.md beside this script.
# WARNING: overwrites the generated cases and index; save manual edits first.
from pathlib import Path
import json, random, textwrap

ROOT = Path(__file__).resolve().parent
CASES = []
HEADER = 'OPENQASM 3.0;\ninclude "stdgates.inc";\n'

def add(group, name, body, purpose, *, kind='normalize', n=1, decl='', definitions='', raw=None, tags=(), note='', oracle=None):
    rel = f'cases/{group}/{name}.qasm'
    body = textwrap.dedent(body).strip()
    if raw is None:
        source = HEADER + '\n'
        if decl:
            source += textwrap.dedent(decl).strip() + '\n'
        if definitions:
            source += textwrap.dedent(definitions).strip() + '\n'
        if n is not None:
            source += f'qubit[{n}] q;\n'
        source += body + ('\n' if body else '')
    else:
        source = textwrap.dedent(raw).strip() + '\n'
    contract = {
        'normalize': 'Normalize the unitary body to h, x, rz, cx; preserve its operator and wires.',
        'feature_probe': 'Valid language feature / support probe. Importer or lowering support may be missing; never silently change semantics.',
        'reject_policy': 'Reject under the current unitary + optional terminal-measurement compiler policy; not necessarily invalid QASM.',
        'invalid_qasm': 'Intentionally invalid source: reject in parsing or semantic validation.',
        'policy_probe': 'Explicit design decision required; do not automatically count as a normalization failure.'
    }[kind]
    comments = '\n'.join('// ' + s for s in [f'TEST: {group}/{name}', f'KIND: {kind}', f'PURPOSE: {purpose}', f'EXPECTED: {contract}', *([f'NOTE: {note}'] if note else [])])
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(comments + '\n\n' + source, encoding='utf-8')
    item = dict(id=f'{group}/{name}', file=rel, kind=kind, purpose=purpose, tags=list(tags), note=note)
    if oracle is not None:
        item['oracle'] = oracle
    CASES.append(item)

# Minimal positive controls. None of these requires a decomposition rule.
G = '00_basics'
add(G,'empty_one_qubit','', 'An empty circuit is the identity; an empty DAG must not crash.', tags=['empty'], oracle='identity')
add(G,'empty_six_qubits','', 'Preserve all six declared idle qubits.', n=6, tags=['empty','width'], oracle='identity')
add(G,'h_only','h q[0];','An internal H must remain usable without a definition fallback.')
add(G,'x_only','x q[0];','An internal X must remain usable without a definition fallback.')
add(G,'rz_only','rz(pi/7) q[0];','A numerical internal RZ is already normalized.')
add(G,'cx_only','cx q[0], q[1];','Preserve control/target order for an internal CX.',n=2)
add(G,'already_normalized_mixed','h q[2];\nrz(-pi/7) q[2];\ncx q[2],q[0];\nx q[1];\ncx q[0],q[1];\nh q[0];','A complete pass should be a fixed point on an internal-basis circuit.',n=3,tags=['idempotence','order'])
add(G,'scalar_qubit','h a;\nrz(pi/7) a;\nx a;','Scalar qubits are not qubit arrays of a presumed name.',n=None,decl='qubit a;',tags=['width'])

G='01_single_qubit'
for gate in ['y','z','s','sdg','t','tdg','sx','id']:
    add(G,f'{gate}_only',f'{gate} q[0];',f'Isolate the {gate} lowering, including its global phase.',tags=['single','phase'])
for gate in ['rx','ry','p']:
    add(G,f'{gate}_generic',f'{gate}(0.731) q[0];',f'Isolate {gate} at a non-special angle; avoid accidental Clifford-only correctness.',tags=['single'])
add(G,'U_generic','U(0.731,-0.413,1.127) q[0];','Built-in U is a key fallback endpoint: implement a terminating lowering rather than assuming definition exists.',tags=['single','fallback','u'])
add(G,'U_zero','U(0,0,0) q[0];','Built-in U with zero angles is the identity.',tags=['u','zero'],oracle='identity')

G='02_angles'
angles = [('zero','0'),('pi','pi'),('minus_pi','-pi'),('half_pi','pi/2'),('minus_half_pi','-pi/2'),('two_pi','2*pi'),('four_pi','4*pi'),('generic_pi','pi/7'),('negative_large','-13*pi/9'),('tiny_nonzero','1e-6'),('generic_decimal','0.731'),('large_angle','23*pi/7')]
for gate in ['rx','ry','rz','p']:
    for label,theta in angles:
        add(G,f'{gate}_{label}',f'{gate}({theta}) q[0];',f'{gate}({theta}): isolate sign, angle, zero/periodicity and phase mistakes.',tags=['angle',gate],note='Use exact operator comparison as well as equivalence up to global phase. 2*pi is not an exact identity for spin rotations.' if label=='two_pi' and gate!='p' else '')
for gate in ['rx','ry','rz']:
    add(G,f'{gate}_near_two_pi',f'{gate}(2*pi + 1e-6) q[0];',f'Do not round a small nonzero residual in {gate} away.',tags=['angle','tolerance'])

G='03_symbolic'
for gate in ['rx','ry','rz','p']:
    add(G,f'{gate}_input',f'{gate}(theta) q[0];',f'Normalize {gate} before binding theta; no float(theta) conversion.',decl='input float[64] theta;',tags=['symbolic',gate])
add(G,'affine_expressions','rx(2*theta + pi/7) q[0];\nry(-theta/3 + phi) q[0];\nrz(theta-2*phi) q[0];', 'Preserve multiple parameter expressions and signs through substitutions.',decl='input float[64] theta;\ninput float[64] phi;',tags=['symbolic','expression'])
add(G,'nonalphabetical_parameters','ry(theta_10) q[0];\nrx(theta_2) q[1];\ncx q[1],q[0];\nrz(theta_1-theta_10) q[1];','Never bind by guessed lexical or declaration order; bind Parameter objects.',n=2,decl='input float[64] theta_2;\ninput float[64] theta_10;\ninput float[64] theta_1;',tags=['symbolic','binding'])
add(G,'U_three_parameters','U(theta,phi,lambda_) q[0];','An explicit U lowering must keep all three symbolic parameters in the correct order.',decl='input float[64] theta;\ninput float[64] phi;\ninput float[64] lambda_;',tags=['symbolic','u'])
add(G,'controlled_parameters','h q[0];\ncp(theta) q[0],q[1];\ncry(phi) q[1],q[0];\ncrz(theta-phi) q[0],q[1];','Parameter expressions must survive multi-qubit decompositions.',n=2,decl='input float[64] theta;\ninput float[64] phi;',tags=['symbolic','controlled'])
add(G,'repeated_custom_parameter','pair(theta) q[0],q[1];\npair(theta+pi/7) q[1],q[2];\npair(-theta) q[2],q[0];','Repeated instantiations must not mutate or reuse the first replacement with stale parameters.',n=3,decl='input float[64] theta;',definitions='gate pair(t) a,b { ry(t) a; cx a,b; rz(-t/2) b; }',tags=['symbolic','cache','mapping'])
add(G,'parameter_cancellation','rz(theta) q[0];\nrz(-theta) q[0];','A cancelled parameter may disappear; do not demand parameter-set equality after valid optimization.',decl='input float[64] theta;',tags=['symbolic','optimization'],oracle='identity')
add(G,'parameter_only_phase','gphase(theta);\nh q[0];','Parameter tracking includes circuit global_phase, not just gate parameters.',decl='input float[64] theta;',tags=['symbolic','phase'],kind='feature_probe')

G='04_two_three_qubit'
for gate in ['cy','cz','ch','swap']:
    add(G,f'{gate}_only',f'{gate} q[0],q[1];',f'Isolate {gate}; recursive replacement must terminate in the internal basis.',n=2,tags=['two_qubit','fallback'])
for gate in ['cp','crx','cry','crz']:
    add(G,f'{gate}_generic',f'{gate}(0.731) q[0],q[1];',f'Isolate {gate}; controlled phase and controlled rotation are different operations.',n=2,tags=['two_qubit','controlled'])
add(G,'cu_four_angles','cu(0.731,-0.413,1.127,0.293) q[0],q[1];','The fourth cu angle is a control-relative phase; do not omit it.',n=2,tags=['controlled','phase','u'])
add(G,'ccx_only','ccx q[0],q[1],q[2];','Toffoli exposes multi-level decomposition and T/TDG handling.',n=3,tags=['three_qubit','fallback'])
add(G,'cswap_only','cswap q[0],q[1],q[2];','Fredkin exposes nested three-qubit gate decompositions.',n=3,tags=['three_qubit','fallback'])
add(G,'asymmetric_sequence','h q[0];\nry(0.321) q[1];\ncrx(-0.713) q[1],q[0];\ncy q[0],q[1];\nrz(0.913) q[1];','Use non-symmetric states and controls so reversed wires cannot accidentally pass.',n=2,tags=['mapping','order'])

G='05_custom_recursive'
add(G,'one_level','my_rx(pi/7) q[0];','Replace a custom node with a body containing a non-internal RX.',definitions='gate my_rx(a) t { rx(a) t; }',tags=['recursion'])
add(G,'three_levels','outer(pi/7) q[0],q[1];','A single sweep leaves middle/inner/custom or non-basis gates behind.',n=2,definitions='''
    gate inner(a) t { ry(a) t; s t; }
    gate middle(a) c,t { inner(a/2) t; cz c,t; inner(-a) c; }
    gate outer(a) c,t { middle(a) t,c; rx(a+pi/9) c; }
''',tags=['recursion','mapping'])
add(G,'empty_definition','identity_gate q[0];','An empty gate definition means identity, not unsupported; erase the node without erasing wires.',definitions='gate identity_gate a { }',tags=['empty','recursion'],oracle='identity')
add(G,'multiple_instances','g(pi/7) q[0];\ng(pi/3) q[1];\ng(-pi/5) q[0];','Cached replacement DAGs must not retain parameters from another invocation.',n=2,definitions='gate g(t) a { ry(t) a; rz(t/2) a; }',tags=['cache','symbolic'])
add(G,'unused_formal_wire','touch_second(pi/5) q[2],q[0];','The first formal wire is unused but must remain in the substitution interface.',n=3,definitions='gate touch_second(t) a,b { ry(t) b; }',tags=['width','mapping'])
add(G,'rzz_defined','rzz_test(pi/7) q[1],q[0];','RZZ is explicitly defined here; do not assume it is supplied by stdgates.inc.',n=2,definitions='gate rzz_test(t) a,b { cx a,b; rz(t) b; cx a,b; }',tags=['custom','mapping'])
add(G,'rxx_defined','rxx_test(pi/7) q[0],q[1];','Nested custom XX interaction with only a final internal-basis result.',n=2,definitions='''
    gate rzz_test(t) a,b { cx a,b; rz(t) b; cx a,b; }
    gate rxx_test(t) a,b { h a; h b; rzz_test(t) a,b; h a; h b; }
''',tags=['custom','recursion'])
add(G,'ryy_defined','ryy_test(pi/7) q[0],q[1];','YY interaction exercises S/SDG and nested custom definitions.',n=2,definitions='''
    gate rzz_test(t) a,b { cx a,b; rz(t) b; cx a,b; }
    gate ryy_test(t) a,b { sdg a; h a; sdg b; h b; rzz_test(t) a,b; h a; s a; h b; s b; }
''',tags=['custom','recursion','phase'])
defs=['gate layer0(t) a { ry(t) a; }']
for i in range(1,21):
    defs.append(f'gate layer{i}(t) a {{ layer{i-1}(t) a; rz(pi/101) a; }}')
add(G,'depth_twenty','layer20(pi/7) q[0];','A linear 20-level definition chain should terminate; detect depth limits without exponential expansion.',definitions='\n'.join(defs),tags=['recursion','depth'])
add(G,'two_custom_names','first(0.71) q[0];\nsecond(0.71) q[0];','Different definitions with identical arity/parameters must not share a wrong cache entry.',definitions='gate first(t) a { rx(t) a; }\ngate second(t) a { ry(t) a; }',tags=['cache'])

G='06_wire_mapping'
add(G,'highest_wire','ry(pi/7) q[5];','One-qubit replacement must act on the original q[5], not local sub-DAG wire 0.',n=6,tags=['mapping','width'])
add(G,'reversed_cx','x q[2];\ncx q[2],q[0];','The control is q[2] and target is q[0]; never sort the qargs.',n=3,tags=['mapping'])
add(G,'nonadjacent_controlled','h q[4];\ncry(pi/7) q[4],q[1];','Nonadjacent operands are valid at logical normalization; this is not a routing test.',n=6,tags=['mapping','topology'])
add(G,'permuted_custom','asymmetric(pi/7) q[3],q[0],q[2];','Preserve the ordered formal-to-actual mapping of a three-wire custom gate.',n=4,definitions='gate asymmetric(t) a,b,c { ry(t) a; cx a,c; rz(t/2) b; cx c,b; }',tags=['mapping','recursion'])
add(G,'multiple_registers','h data[1];\ncry(pi/5) anc[0],data[0];\ncz data[1],anc[0];','Different registers may both contain local index zero.',n=None,decl='qubit[2] data;\nqubit[1] anc;',tags=['mapping','registers'])
add(G,'scalar_and_array','rx(pi/7) anc;\ncy q[1],anc;\nrz(-pi/5) q[0];','Preserve a scalar ancilla and a separate array register.',n=2,decl='qubit anc;',tags=['mapping','registers'])
add(G,'different_invocation_order','pair(pi/7) q[2],q[0];\npair(-pi/5) q[1],q[2];','Reusing a custom rule must not reuse physical wire mappings.',n=3,definitions='gate pair(t) a,b { rx(t) a; cy a,b; rz(t) b; }',tags=['cache','mapping'])
add(G,'idle_classical_register','ry(pi/7) q[2];','Unused classical bits should not be mistaken for qubits or lost by a DAG-only pass.',n=3,decl='bit[5] unused;',tags=['width','classical'])

G='07_global_phase'
add(G,'z_vs_rz','z q[0];','Z = exp(i*pi/2) RZ(pi). A missing phase is invisible to Operator.equiv.',tags=['phase'])
add(G,'s_vs_rz','s q[0];','S = exp(i*pi/4) RZ(pi/2). Preserve or explicitly report the phase.',tags=['phase'])
add(G,'tdg_vs_rz','tdg q[0];','TDG requires a negative global-phase correction in an exact RZ lowering.',tags=['phase'])
add(G,'phase_accumulation','z q[0];\ns q[1];\nt q[0];\nsdg q[0];\ntdg q[1];','Accumulate all replacement phases rather than overwriting or dropping them.',n=2,tags=['phase','accumulation'])
add(G,'rotation_two_pi','rx(2*pi) q[0];','RX(2*pi) = -I, not exactly I; modulo-2*pi angle wrapping loses a phase.',tags=['phase','periodicity'])
add(G,'rotation_four_pi','ry(4*pi) q[0];','RY(4*pi) is exactly I within numerical precision.',tags=['phase','periodicity'],oracle='identity')
add(G,'explicit_gphase','gphase(pi/7);\nh q[0];','Preserve an incoming circuit global phase through DAG conversion and substitution.',tags=['phase'],kind='feature_probe')
add(G,'custom_internal_gphase','phased(pi/7) q[0];','Global phase stored inside a gate definition must be added during substitution.',definitions='gate phased(a) t { gphase(a/3); rx(a) t; }',tags=['phase','recursion'],kind='feature_probe')
add(G,'controlled_z_relative_phase','h q[0];\nh q[1];\nctrl @ z q[0],q[1];\nh q[0];','Under control, a formerly global phase becomes relative. Replacing controlled-Z by controlled-RZ(pi) is wrong.',n=2,tags=['phase','controlled'],kind='feature_probe')
add(G,'cp_not_crz','h q[0];\nh q[1];\ncp(pi/3) q[0],q[1];\nh q[0];','CP and CRZ must not share a naive lowering that discards the base-gate phase.',n=2,tags=['phase','controlled'])
add(G,'controlled_two_pi_rotation','h q[0];\ncrx(2*pi) q[0],q[1];\nh q[0];','A controlled 2*pi rotation is not the identity; the control acquires a relative minus sign.',n=2,tags=['phase','controlled','periodicity'])

G='08_terminal_measurements'
add(G,'bell_register_readout','h q[0];\ncx q[0],q[1];\nc = measure q;','Strip terminal measurements before Norm and restore the original q-to-c mapping afterward.',n=2,decl='bit[2] c;',tags=['measurement'])
add(G,'single_partial_readout','ry(pi/7) q[2];\ncx q[2],q[0];\nc[0] = measure q[2];','Not all qubits need to be measured, and the measured qubit is not necessarily q[0].',n=3,decl='bit[1] c;',tags=['measurement','mapping'])
add(G,'permuted_readout','x q[0];\nry(pi/7) q[2];\nc[2]=measure q[0];\nc[0]=measure q[2];\nc[1]=measure q[1];','Keep ordered qubit/classical-bit associations instead of rebuilding c[i]=measure q[i].',n=3,decl='bit[3] c;',tags=['measurement','mapping'])
add(G,'cross_register_readout','ry(pi/7) data[1];\ncx data[1],anc;\nout[0]=measure anc;\nflag=measure data[1];','Preserve scalar and array classical destinations across multiple quantum registers.',n=None,decl='qubit[2] data;\nqubit anc;\nbit[2] out;\nbit flag;',tags=['measurement','registers'])
add(G,'readout_only','c=measure q;','A measurement-only program has an empty unitary body, not an invalid circuit.',n=2,decl='bit[2] c;',tags=['measurement','empty'])
add(G,'measurement_terminal_per_wire','h q[0];\nc[0]=measure q[0];\nry(pi/7) q[1];\nc[1]=measure q[1];','The first measurement is terminal on its own qubit even though unrelated quantum work follows.',n=2,decl='bit[2] c;',tags=['measurement','terminal_policy'],kind='policy_probe',note='DAG/per-wire terminality can accept this safely when no classical result is read; a stricter textual-suffix policy may reject deliberately.')
add(G,'symbolic_then_readout','ry(theta) q[1];\ncx q[1],q[0];\nc=measure q;','Bind symbolic parameters only for equivalence checks, not before normalization.',n=2,decl='input float[64] theta;\nbit[2] c;',tags=['measurement','symbolic'])
add(G,'custom_then_readout','f(pi/7) q[2],q[0];\nc[0]=measure q[2];\nc[2]=measure q[0];','Nested normalization plus partial permuted terminal readout.',n=3,decl='bit[3] c;',definitions='gate f(t) a,b { ry(t) a; cz a,b; }',tags=['measurement','recursion'])

G='09_directive_policy'
add(G,'barrier_between_gates','ry(pi/7) q[0];\nbarrier q;\nrx(-pi/5) q[1];','A barrier is not a unitary gate to decompose. Decide whether to preserve or strip it before Norm.',n=2,kind='feature_probe',tags=['barrier'])
add(G,'barrier_before_measurements','ry(pi/7) q[1];\nbarrier q;\nc=measure q;','Keep barrier policy separate from terminal-measurement validation.',n=2,decl='bit[2] c;',kind='feature_probe',tags=['barrier','measurement'])
add(G,'barrier_after_measurements','h q[0];\nc[0]=measure q[0];\nbarrier q[0];','A trailing barrier is not quantum reuse; do not flag it as a gate after measurement.',n=1,decl='bit[1] c;',kind='policy_probe',tags=['barrier','measurement'])
add(G,'repeated_measurement','h q[0];\na=measure q[0];\nb=measure q[0];','Decide whether repeated final measurements of one qubit are supported or rejected.',n=1,decl='bit a;\nbit b;',kind='policy_probe',tags=['measurement'])
add(G,'classical_destination_overwrite','x q[0];\nc=measure q[0];\nc=measure q[1];','Two final measurements write the same bit; last-write order is significant.',n=2,decl='bit c;',kind='policy_probe',tags=['measurement','classical_order'])
add(G,'discarded_measurement','h q[0];\nmeasure q[0];','A measurement with no classical destination is valid QASM; decide whether the compiler accepts it.',kind='policy_probe',tags=['measurement'])
add(G,'delay','h q[0];\ndelay[10ns] q[0];\nx q[0];','Timing information is outside unitary gate normalization; preserve elsewhere or reject explicitly.',kind='policy_probe',tags=['timing'])
add(G,'phase_only_zero_qubits','gphase(pi/7);','Decide whether zero-qubit, pure-global-phase programs are inside the compiler input contract.',n=None,kind='policy_probe',tags=['phase','width'])

G='10_language_features'
features=[
('inverse_s','inv @ s q[0];',1,'Inverse modifiers may import as sdg or a wrapped inverse operation.'),
('inverse_custom','inv @ custom_gate(pi/7) q[0];',1,'Inverse of a sequence requires reversing order and inverting every constituent.'),
('ctrl_x','ctrl @ x q[1],q[0];',2,'A control modifier prepends the control wire; it is not another parameter.'),
('ctrl_two_x','ctrl(2) @ x q[2],q[0],q[1];',3,'Multiple controls and permuted qargs.'),
('negative_control','negctrl @ x q[1],q[0];',2,'Open controls must not be treated as ordinary positive controls.'),
('mixed_controls','negctrl @ ctrl @ x q[2],q[0],q[1];',3,'Mixed-polarity controls expose name-only dispatch and ignored ctrl_state.'),
('controlled_inverse','ctrl @ inv @ s q[0],q[1];',2,'Combine controlled and inverse semantics without losing phases.'),
('integer_power','pow(3) @ rx(pi/7) q[0];',1,'Integer powers require complete lowering, not leaving a wrapper gate.'),
('fractional_power','pow(0.5) @ x q[0];',1,'A valid fractional-power feature may require synthesis not currently implemented.'),
('controlled_gphase','ctrl @ gphase(pi/7) q[0];',1,'Controlled global phase is a one-qubit phase operation, not ignorable metadata.'),
]
for name,body,n,purpose in features:
    add(G,name,body,purpose,n=n,kind='feature_probe',definitions='gate custom_gate(t) a { ry(t) a; rz(t/2) a; }' if name=='inverse_custom' else '',tags=['modifier'])
add(G,'broadcast_one_qubit','ry(pi/7) q;','Broadcast a one-qubit operation to every member of a register.',n=3,kind='feature_probe',tags=['broadcast'])
add(G,'broadcast_two_registers','h a;\ncx a,b;','Pairwise broadcasting over same-sized registers, not all-to-all connectivity.',n=None,decl='qubit[2] a;\nqubit[2] b;',kind='feature_probe',tags=['broadcast','mapping'])
add(G,'alias_slice','let pair = q[1:2];\nry(pi/7) pair;\ncx pair[1],pair[0];','Aliases must refer to existing qubits; do not allocate new wires.',n=4,kind='feature_probe',tags=['alias','mapping'])
add(G,'input_angle','ry(theta) q[0];','Probe input angle[64] support separately from input float[64].',decl='input angle[64] theta;',kind='feature_probe',tags=['symbolic','importer'])
add(G,'constant_expression','rx(theta) q[0];','A compile-time const declaration may be an importer limitation, not a Norm defect.',decl='const float[64] theta = pi/7;',kind='feature_probe',tags=['expression','importer'])
add(G,'symbolic_product','ry(theta*phi) q[0];','Probe non-affine symbolic expression support.',decl='input float[64] theta;\ninput float[64] phi;',kind='feature_probe',tags=['symbolic','expression'])
add(G,'static_for','for int i in [0:2] { ry(pi/7) q[i]; }','A static loop is valid, but should be unrolled in a frontend before a flat DAG normalizer.',n=3,kind='policy_probe',tags=['loop','frontend'])
# Legal user-defined names without the standard library: test semantic identity, not only op.name.
add(G,'custom_gate_named_h','','Do not mark a generic custom gate as normalized solely because its name is h.',raw='''
OPENQASM 3.0;
gate h a { U(pi,0,pi) a; }
qubit[1] q;
h q[0];
''',kind='feature_probe',tags=['name_collision','semantic_gate_identity'])
add(G,'custom_gate_named_rx','','A user-defined rx name need not mean Qiskit RXGate. Dispatch must inspect the operation type/definition.',raw='''
OPENQASM 3.0;
gate rx(t) a { U(0,0,t) a; }
qubit[1] q;
rx(pi/7) q[0];
''',kind='feature_probe',tags=['name_collision','semantic_gate_identity'])

G='11_reject_policy'
rejects=[
('measure_then_h','h q[0];\nc[0]=measure q[0];\nh q[0];',1,'A measured qubit is reused by a quantum gate.'),
('measured_qubit_as_control','h q[0];\nc[0]=measure q[0];\ncx q[0],q[1];',2,'Measurement followed by using that qubit as a CX control is not terminal.'),
('measured_qubit_as_target','c[0]=measure q[1];\ncx q[0],q[1];',2,'Measurement followed by using that qubit as a CX target is not terminal.'),
('measure_then_custom','c[0]=measure q[0];\nf(pi/7) q[0];',1,'A gate hidden inside a custom definition still reuses a measured qubit.'),
('reset_first','reset q[0];\nh q[0];',1,'Reset is outside the chosen unitary-only computation model, even at the beginning.'),
('reset_after_entanglement','h q[0];\ncx q[0],q[1];\nreset q[1];',2,'Dropping reset changes the computation.'),
('measurement_feedforward','h q[0];\nc[0]=measure q[0];\nif (c[0]) { x q[1]; }',2,'Classical feed-forward remains unsupported even if the measured qubit is never reused.'),
('if_else','c[0]=measure q[0];\nif (c[0]) { x q[1]; } else { h q[1]; }',2,'Reject control-flow nodes rather than silently normalizing only one branch.'),
('while_measurement','h q[0];\nc[0]=measure q[0];\nwhile (c[0]) { x q[0]; c[0]=measure q[0]; }',1,'Dynamic loops are not a flat unitary circuit.'),
]
for name,body,n,purpose in rejects:
    add(G,name,body,purpose,n=n,decl='bit[1] c;',definitions='gate f(t) a { ry(t) a; }' if name=='measure_then_custom' else '',kind='reject_policy',tags=['validation'])

G='12_invalid_qasm'
invalid=[
('missing_semicolon',HEADER+'qubit[1] q;\nh q[0]\n','Syntax error: missing operation semicolon.'),
('unknown_gate',HEADER+'qubit[1] q;\nnot_a_gate q[0];','Semantic error: undefined gate.'),
('undeclared_angle',HEADER+'qubit[1] q;\nry(theta) q[0];','Semantic error: undeclared parameter theta.'),
('unknown_qubit',HEADER+'qubit[1] q;\nh missing[0];','Semantic error: undeclared qubit.'),
('qubit_out_of_range',HEADER+'qubit[2] q;\nx q[2];','Semantic error: out-of-range array index.'),
('classical_out_of_range',HEADER+'qubit[1] q;\nbit[1] c;\nc[1]=measure q[0];','Semantic error: classical destination out of range.'),
('duplicate_cx_operand',HEADER+'qubit[1] q;\ncx q[0],q[0];','Semantic error: a controlled two-qubit gate cannot use the same qubit twice.'),
('duplicate_ccx_operand',HEADER+'qubit[2] q;\nccx q[0],q[1],q[1];','Semantic error: repeated qubit in one three-qubit operation.'),
('too_few_qubits',HEADER+'qubit[2] q;\ncx q[0];','Wrong gate arity: CX requires two qubit operands.'),
('too_many_qubits',HEADER+'qubit[2] q;\nh q[0],q[1];','Wrong gate arity: H has one operand; comma-separated operands are not broadcasting.'),
('missing_angle',HEADER+'qubit[1] q;\nrx q[0];','Wrong parameter arity: RX needs an angle.'),
('extra_angle',HEADER+'qubit[1] q;\nry(pi/7,pi/5) q[0];','Wrong parameter arity: RY has one angle.'),
('classical_as_qubit',HEADER+'bit[1] c;\nh c[0];','Type error: a classical bit is not a gate operand.'),
('mismatched_broadcast',HEADER+'qubit[2] a;\nqubit[3] b;\ncx a,b;','Broadcast arrays must have equal lengths.'),
('mismatched_measurement',HEADER+'qubit[2] q;\nbit[1] c;\nc=measure q;','Measurement source/destination lengths differ.'),
('duplicate_declaration',HEADER+'qubit[1] q;\nqubit[1] q;','Duplicate declaration in one scope.'),
('self_recursive_gate',HEADER+'gate bad a { bad a; }\nqubit[1] q;\nbad q[0];','Recursive gate definitions are not legal OpenQASM; reject before Norm recursion.'),
('measurement_in_gate',HEADER+'gate bad a { measure a; }\nqubit[1] q;\nbad q[0];','A gate definition cannot contain measurement.'),
('missing_std_include','OPENQASM 3.0;\nqubit[1] q;\nh q[0];','Without an include or definition, h is not a built-in; only U and gphase are built-in gates.'),
('nonstandard_rzz_undefined',HEADER+'qubit[2] q;\nrzz(pi/7) q[0],q[1];','RZZ is not automatically defined by the OpenQASM 3.0 standard library; provide a custom definition.'),
]
for name,raw,purpose in invalid:
    add(G,name,'',purpose,raw=raw,kind='invalid_qasm',tags=['negative','frontend'])

G='13_stress'
for seed in [17,41,103,997]:
    rng=random.Random(seed)
    ops=[]
    for i in range(160):
        k=rng.choice(['h','x','y','z','s','sdg','t','tdg','rx','ry','rz','p','cx','cy','cz','swap','cp'])
        a,b=rng.sample(range(5),2)
        angle=f'{rng.uniform(-7,7):.12f}'
        if k in ['rx','ry','rz','p']: ops.append(f'{k}({angle}) q[{a}];')
        elif k=='cp': ops.append(f'cp({angle}) q[{a}],q[{b}];')
        elif k in ['cx','cy','cz','swap']: ops.append(f'{k} q[{a}],q[{b}];')
        else: ops.append(f'{k} q[{a}];')
    add(G,f'seed_{seed}_five_qubits','\n'.join(ops),f'Deterministic mixed circuit, seed {seed}, 160 source operations. No cancellation-only construction.',n=5,tags=['stress','random'],note='Full operator comparison is affordable at five qubits; these inputs are reproducible.')
ops=[f'ry({(i%17-8)}/19) q[{i%6}];\ncx q[{i%6}],q[{(i+3)%6}];' for i in range(120)]
add(G,'many_replacements','\n'.join(ops),'240 source operations exercise mutation while iterating and repeated lowering on six wires.',n=6,tags=['stress','iteration'])
add(G,'custom_reuse_120','\n'.join(f'block({(i%13-6)}/17) q[{i%4}],q[{(i+1)%4}];' for i in range(120)),'Repeated custom invocations expose shared replacement objects and stale cache state.',n=4,definitions='gate block(t) a,b { ry(t) a; cz a,b; rx(-t/3) b; }',tags=['stress','cache'])

G='14_optimizer_traps'
traps=[
('noncommuting_rotation_order','rx(pi/7) q[0];\nry(pi/5) q[0];\nrz(pi/3) q[0];',1,'Do not reverse operations while building a sub-DAG.'),
('h_separates_rz','rz(pi/7) q[0];\nh q[0];\nrz(pi/5) q[0];',1,'Never merge RZ rotations through a noncommuting H.'),
('cx_target_separates_rz','rz(pi/7) q[1];\ncx q[0],q[1];\nrz(pi/5) q[1];',2,'RZ on the CX target cannot generally be moved through CX.'),
('adjacent_inverse','rx(pi/7) q[0];\nrx(-pi/7) q[0];',1,'Correctness requires identity behavior, not a minimal output gate count.'),
('two_x','x q[0];\nx q[0];',1,'Two X gates may remain after normalization; cancellation is an optimization, not a normalization requirement.'),
('cx_direction_changes','cx q[0],q[1];\ncx q[1],q[0];',2,'Opposite-direction CX gates do not cancel.'),
('tiny_angle_aggregate','\n'.join('ry(1e-6) q[0];' for _ in range(100)),1,'Repeated small rotations must not all be dropped as zero.'),
]
for name,body,n,purpose in traps:
    add(G,name,body,purpose,n=n,tags=['optimization','order'],oracle='identity' if name in ['adjacent_inverse','two_x'] else None)

# Stable IDs and a machine-readable table of expected behavior.
assert len({c['id'] for c in CASES})==len(CASES)
manifest={'schema_version':1,'language':'OpenQASM 3.0','basis':['h','x','rz','cx'],'matrix_atol':1e-9,'matrix_rtol':1e-9,'max_matrix_qubits':6,'cases':CASES}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
lines=['# Case-by-case test index','','Each file also contains its purpose and expected behavior in comments.','', '| File | Kind | What it tests |','|---|---|---|']
for c in CASES:
    lines.append(f"| `{c['file']}` | {c['kind']} | {c['purpose']} |")
(ROOT/'TEST_INDEX.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
from collections import Counter
print('TOTAL',len(CASES))
print('BY KIND',dict(Counter(c['kind'] for c in CASES)))
print('BY GROUP',dict(Counter(c['id'].split('/')[0] for c in CASES)))
