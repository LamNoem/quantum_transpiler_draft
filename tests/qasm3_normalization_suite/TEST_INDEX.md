# Case-by-case test index

Each file also contains its purpose and expected behavior in comments.

| File | Kind | What it tests |
|---|---|---|
| `cases/00_basics/empty_one_qubit.qasm` | normalize | An empty circuit is the identity; an empty DAG must not crash. |
| `cases/00_basics/empty_six_qubits.qasm` | normalize | Preserve all six declared idle qubits. |
| `cases/00_basics/h_only.qasm` | normalize | An internal H must remain usable without a definition fallback. |
| `cases/00_basics/x_only.qasm` | normalize | An internal X must remain usable without a definition fallback. |
| `cases/00_basics/rz_only.qasm` | normalize | A numerical internal RZ is already normalized. |
| `cases/00_basics/cx_only.qasm` | normalize | Preserve control/target order for an internal CX. |
| `cases/00_basics/already_normalized_mixed.qasm` | normalize | A complete pass should be a fixed point on an internal-basis circuit. |
| `cases/00_basics/scalar_qubit.qasm` | normalize | Scalar qubits are not qubit arrays of a presumed name. |
| `cases/01_single_qubit/y_only.qasm` | normalize | Isolate the y lowering, including its global phase. |
| `cases/01_single_qubit/z_only.qasm` | normalize | Isolate the z lowering, including its global phase. |
| `cases/01_single_qubit/s_only.qasm` | normalize | Isolate the s lowering, including its global phase. |
| `cases/01_single_qubit/sdg_only.qasm` | normalize | Isolate the sdg lowering, including its global phase. |
| `cases/01_single_qubit/t_only.qasm` | normalize | Isolate the t lowering, including its global phase. |
| `cases/01_single_qubit/tdg_only.qasm` | normalize | Isolate the tdg lowering, including its global phase. |
| `cases/01_single_qubit/sx_only.qasm` | normalize | Isolate the sx lowering, including its global phase. |
| `cases/01_single_qubit/id_only.qasm` | normalize | Isolate the id lowering, including its global phase. |
| `cases/01_single_qubit/rx_generic.qasm` | normalize | Isolate rx at a non-special angle; avoid accidental Clifford-only correctness. |
| `cases/01_single_qubit/ry_generic.qasm` | normalize | Isolate ry at a non-special angle; avoid accidental Clifford-only correctness. |
| `cases/01_single_qubit/p_generic.qasm` | normalize | Isolate p at a non-special angle; avoid accidental Clifford-only correctness. |
| `cases/01_single_qubit/U_generic.qasm` | normalize | Built-in U is a key fallback endpoint: implement a terminating lowering rather than assuming definition exists. |
| `cases/01_single_qubit/U_zero.qasm` | normalize | Built-in U with zero angles is the identity. |
| `cases/02_angles/rx_zero.qasm` | normalize | rx(0): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_pi.qasm` | normalize | rx(pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_minus_pi.qasm` | normalize | rx(-pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_half_pi.qasm` | normalize | rx(pi/2): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_minus_half_pi.qasm` | normalize | rx(-pi/2): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_two_pi.qasm` | normalize | rx(2*pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_four_pi.qasm` | normalize | rx(4*pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_generic_pi.qasm` | normalize | rx(pi/7): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_negative_large.qasm` | normalize | rx(-13*pi/9): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_tiny_nonzero.qasm` | normalize | rx(1e-6): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_generic_decimal.qasm` | normalize | rx(0.731): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_large_angle.qasm` | normalize | rx(23*pi/7): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_zero.qasm` | normalize | ry(0): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_pi.qasm` | normalize | ry(pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_minus_pi.qasm` | normalize | ry(-pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_half_pi.qasm` | normalize | ry(pi/2): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_minus_half_pi.qasm` | normalize | ry(-pi/2): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_two_pi.qasm` | normalize | ry(2*pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_four_pi.qasm` | normalize | ry(4*pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_generic_pi.qasm` | normalize | ry(pi/7): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_negative_large.qasm` | normalize | ry(-13*pi/9): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_tiny_nonzero.qasm` | normalize | ry(1e-6): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_generic_decimal.qasm` | normalize | ry(0.731): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/ry_large_angle.qasm` | normalize | ry(23*pi/7): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_zero.qasm` | normalize | rz(0): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_pi.qasm` | normalize | rz(pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_minus_pi.qasm` | normalize | rz(-pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_half_pi.qasm` | normalize | rz(pi/2): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_minus_half_pi.qasm` | normalize | rz(-pi/2): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_two_pi.qasm` | normalize | rz(2*pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_four_pi.qasm` | normalize | rz(4*pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_generic_pi.qasm` | normalize | rz(pi/7): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_negative_large.qasm` | normalize | rz(-13*pi/9): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_tiny_nonzero.qasm` | normalize | rz(1e-6): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_generic_decimal.qasm` | normalize | rz(0.731): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rz_large_angle.qasm` | normalize | rz(23*pi/7): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_zero.qasm` | normalize | p(0): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_pi.qasm` | normalize | p(pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_minus_pi.qasm` | normalize | p(-pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_half_pi.qasm` | normalize | p(pi/2): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_minus_half_pi.qasm` | normalize | p(-pi/2): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_two_pi.qasm` | normalize | p(2*pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_four_pi.qasm` | normalize | p(4*pi): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_generic_pi.qasm` | normalize | p(pi/7): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_negative_large.qasm` | normalize | p(-13*pi/9): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_tiny_nonzero.qasm` | normalize | p(1e-6): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_generic_decimal.qasm` | normalize | p(0.731): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/p_large_angle.qasm` | normalize | p(23*pi/7): isolate sign, angle, zero/periodicity and phase mistakes. |
| `cases/02_angles/rx_near_two_pi.qasm` | normalize | Do not round a small nonzero residual in rx away. |
| `cases/02_angles/ry_near_two_pi.qasm` | normalize | Do not round a small nonzero residual in ry away. |
| `cases/02_angles/rz_near_two_pi.qasm` | normalize | Do not round a small nonzero residual in rz away. |
| `cases/03_symbolic/rx_input.qasm` | normalize | Normalize rx before binding theta; no float(theta) conversion. |
| `cases/03_symbolic/ry_input.qasm` | normalize | Normalize ry before binding theta; no float(theta) conversion. |
| `cases/03_symbolic/rz_input.qasm` | normalize | Normalize rz before binding theta; no float(theta) conversion. |
| `cases/03_symbolic/p_input.qasm` | normalize | Normalize p before binding theta; no float(theta) conversion. |
| `cases/03_symbolic/affine_expressions.qasm` | normalize | Preserve multiple parameter expressions and signs through substitutions. |
| `cases/03_symbolic/nonalphabetical_parameters.qasm` | normalize | Never bind by guessed lexical or declaration order; bind Parameter objects. |
| `cases/03_symbolic/U_three_parameters.qasm` | normalize | An explicit U lowering must keep all three symbolic parameters in the correct order. |
| `cases/03_symbolic/controlled_parameters.qasm` | normalize | Parameter expressions must survive multi-qubit decompositions. |
| `cases/03_symbolic/repeated_custom_parameter.qasm` | normalize | Repeated instantiations must not mutate or reuse the first replacement with stale parameters. |
| `cases/03_symbolic/parameter_cancellation.qasm` | normalize | A cancelled parameter may disappear; do not demand parameter-set equality after valid optimization. |
| `cases/03_symbolic/parameter_only_phase.qasm` | feature_probe | Parameter tracking includes circuit global_phase, not just gate parameters. |
| `cases/04_two_three_qubit/cy_only.qasm` | normalize | Isolate cy; recursive replacement must terminate in the internal basis. |
| `cases/04_two_three_qubit/cz_only.qasm` | normalize | Isolate cz; recursive replacement must terminate in the internal basis. |
| `cases/04_two_three_qubit/ch_only.qasm` | normalize | Isolate ch; recursive replacement must terminate in the internal basis. |
| `cases/04_two_three_qubit/swap_only.qasm` | normalize | Isolate swap; recursive replacement must terminate in the internal basis. |
| `cases/04_two_three_qubit/cp_generic.qasm` | normalize | Isolate cp; controlled phase and controlled rotation are different operations. |
| `cases/04_two_three_qubit/crx_generic.qasm` | normalize | Isolate crx; controlled phase and controlled rotation are different operations. |
| `cases/04_two_three_qubit/cry_generic.qasm` | normalize | Isolate cry; controlled phase and controlled rotation are different operations. |
| `cases/04_two_three_qubit/crz_generic.qasm` | normalize | Isolate crz; controlled phase and controlled rotation are different operations. |
| `cases/04_two_three_qubit/cu_four_angles.qasm` | normalize | The fourth cu angle is a control-relative phase; do not omit it. |
| `cases/04_two_three_qubit/ccx_only.qasm` | normalize | Toffoli exposes multi-level decomposition and T/TDG handling. |
| `cases/04_two_three_qubit/cswap_only.qasm` | normalize | Fredkin exposes nested three-qubit gate decompositions. |
| `cases/04_two_three_qubit/asymmetric_sequence.qasm` | normalize | Use non-symmetric states and controls so reversed wires cannot accidentally pass. |
| `cases/05_custom_recursive/one_level.qasm` | normalize | Replace a custom node with a body containing a non-internal RX. |
| `cases/05_custom_recursive/three_levels.qasm` | normalize | A single sweep leaves middle/inner/custom or non-basis gates behind. |
| `cases/05_custom_recursive/empty_definition.qasm` | normalize | An empty gate definition means identity, not unsupported; erase the node without erasing wires. |
| `cases/05_custom_recursive/multiple_instances.qasm` | normalize | Cached replacement DAGs must not retain parameters from another invocation. |
| `cases/05_custom_recursive/unused_formal_wire.qasm` | normalize | The first formal wire is unused but must remain in the substitution interface. |
| `cases/05_custom_recursive/rzz_defined.qasm` | normalize | RZZ is explicitly defined here; do not assume it is supplied by stdgates.inc. |
| `cases/05_custom_recursive/rxx_defined.qasm` | normalize | Nested custom XX interaction with only a final internal-basis result. |
| `cases/05_custom_recursive/ryy_defined.qasm` | normalize | YY interaction exercises S/SDG and nested custom definitions. |
| `cases/05_custom_recursive/depth_twenty.qasm` | normalize | A linear 20-level definition chain should terminate; detect depth limits without exponential expansion. |
| `cases/05_custom_recursive/two_custom_names.qasm` | normalize | Different definitions with identical arity/parameters must not share a wrong cache entry. |
| `cases/06_wire_mapping/highest_wire.qasm` | normalize | One-qubit replacement must act on the original q[5], not local sub-DAG wire 0. |
| `cases/06_wire_mapping/reversed_cx.qasm` | normalize | The control is q[2] and target is q[0]; never sort the qargs. |
| `cases/06_wire_mapping/nonadjacent_controlled.qasm` | normalize | Nonadjacent operands are valid at logical normalization; this is not a routing test. |
| `cases/06_wire_mapping/permuted_custom.qasm` | normalize | Preserve the ordered formal-to-actual mapping of a three-wire custom gate. |
| `cases/06_wire_mapping/multiple_registers.qasm` | normalize | Different registers may both contain local index zero. |
| `cases/06_wire_mapping/scalar_and_array.qasm` | normalize | Preserve a scalar ancilla and a separate array register. |
| `cases/06_wire_mapping/different_invocation_order.qasm` | normalize | Reusing a custom rule must not reuse physical wire mappings. |
| `cases/06_wire_mapping/idle_classical_register.qasm` | normalize | Unused classical bits should not be mistaken for qubits or lost by a DAG-only pass. |
| `cases/07_global_phase/z_vs_rz.qasm` | normalize | Z = exp(i*pi/2) RZ(pi). A missing phase is invisible to Operator.equiv. |
| `cases/07_global_phase/s_vs_rz.qasm` | normalize | S = exp(i*pi/4) RZ(pi/2). Preserve or explicitly report the phase. |
| `cases/07_global_phase/tdg_vs_rz.qasm` | normalize | TDG requires a negative global-phase correction in an exact RZ lowering. |
| `cases/07_global_phase/phase_accumulation.qasm` | normalize | Accumulate all replacement phases rather than overwriting or dropping them. |
| `cases/07_global_phase/rotation_two_pi.qasm` | normalize | RX(2*pi) = -I, not exactly I; modulo-2*pi angle wrapping loses a phase. |
| `cases/07_global_phase/rotation_four_pi.qasm` | normalize | RY(4*pi) is exactly I within numerical precision. |
| `cases/07_global_phase/explicit_gphase.qasm` | feature_probe | Preserve an incoming circuit global phase through DAG conversion and substitution. |
| `cases/07_global_phase/custom_internal_gphase.qasm` | feature_probe | Global phase stored inside a gate definition must be added during substitution. |
| `cases/07_global_phase/controlled_z_relative_phase.qasm` | feature_probe | Under control, a formerly global phase becomes relative. Replacing controlled-Z by controlled-RZ(pi) is wrong. |
| `cases/07_global_phase/cp_not_crz.qasm` | normalize | CP and CRZ must not share a naive lowering that discards the base-gate phase. |
| `cases/07_global_phase/controlled_two_pi_rotation.qasm` | normalize | A controlled 2*pi rotation is not the identity; the control acquires a relative minus sign. |
| `cases/08_terminal_measurements/bell_register_readout.qasm` | normalize | Strip terminal measurements before Norm and restore the original q-to-c mapping afterward. |
| `cases/08_terminal_measurements/single_partial_readout.qasm` | normalize | Not all qubits need to be measured, and the measured qubit is not necessarily q[0]. |
| `cases/08_terminal_measurements/permuted_readout.qasm` | normalize | Keep ordered qubit/classical-bit associations instead of rebuilding c[i]=measure q[i]. |
| `cases/08_terminal_measurements/cross_register_readout.qasm` | normalize | Preserve scalar and array classical destinations across multiple quantum registers. |
| `cases/08_terminal_measurements/readout_only.qasm` | normalize | A measurement-only program has an empty unitary body, not an invalid circuit. |
| `cases/08_terminal_measurements/measurement_terminal_per_wire.qasm` | policy_probe | The first measurement is terminal on its own qubit even though unrelated quantum work follows. |
| `cases/08_terminal_measurements/symbolic_then_readout.qasm` | normalize | Bind symbolic parameters only for equivalence checks, not before normalization. |
| `cases/08_terminal_measurements/custom_then_readout.qasm` | normalize | Nested normalization plus partial permuted terminal readout. |
| `cases/09_directive_policy/barrier_between_gates.qasm` | feature_probe | A barrier is not a unitary gate to decompose. Decide whether to preserve or strip it before Norm. |
| `cases/09_directive_policy/barrier_before_measurements.qasm` | feature_probe | Keep barrier policy separate from terminal-measurement validation. |
| `cases/09_directive_policy/barrier_after_measurements.qasm` | policy_probe | A trailing barrier is not quantum reuse; do not flag it as a gate after measurement. |
| `cases/09_directive_policy/repeated_measurement.qasm` | policy_probe | Decide whether repeated final measurements of one qubit are supported or rejected. |
| `cases/09_directive_policy/classical_destination_overwrite.qasm` | policy_probe | Two final measurements write the same bit; last-write order is significant. |
| `cases/09_directive_policy/discarded_measurement.qasm` | policy_probe | A measurement with no classical destination is valid QASM; decide whether the compiler accepts it. |
| `cases/09_directive_policy/delay.qasm` | policy_probe | Timing information is outside unitary gate normalization; preserve elsewhere or reject explicitly. |
| `cases/09_directive_policy/phase_only_zero_qubits.qasm` | policy_probe | Decide whether zero-qubit, pure-global-phase programs are inside the compiler input contract. |
| `cases/10_language_features/inverse_s.qasm` | feature_probe | Inverse modifiers may import as sdg or a wrapped inverse operation. |
| `cases/10_language_features/inverse_custom.qasm` | feature_probe | Inverse of a sequence requires reversing order and inverting every constituent. |
| `cases/10_language_features/ctrl_x.qasm` | feature_probe | A control modifier prepends the control wire; it is not another parameter. |
| `cases/10_language_features/ctrl_two_x.qasm` | feature_probe | Multiple controls and permuted qargs. |
| `cases/10_language_features/negative_control.qasm` | feature_probe | Open controls must not be treated as ordinary positive controls. |
| `cases/10_language_features/mixed_controls.qasm` | feature_probe | Mixed-polarity controls expose name-only dispatch and ignored ctrl_state. |
| `cases/10_language_features/controlled_inverse.qasm` | feature_probe | Combine controlled and inverse semantics without losing phases. |
| `cases/10_language_features/integer_power.qasm` | feature_probe | Integer powers require complete lowering, not leaving a wrapper gate. |
| `cases/10_language_features/fractional_power.qasm` | feature_probe | A valid fractional-power feature may require synthesis not currently implemented. |
| `cases/10_language_features/controlled_gphase.qasm` | feature_probe | Controlled global phase is a one-qubit phase operation, not ignorable metadata. |
| `cases/10_language_features/broadcast_one_qubit.qasm` | feature_probe | Broadcast a one-qubit operation to every member of a register. |
| `cases/10_language_features/broadcast_two_registers.qasm` | feature_probe | Pairwise broadcasting over same-sized registers, not all-to-all connectivity. |
| `cases/10_language_features/alias_slice.qasm` | feature_probe | Aliases must refer to existing qubits; do not allocate new wires. |
| `cases/10_language_features/input_angle.qasm` | feature_probe | Probe input angle[64] support separately from input float[64]. |
| `cases/10_language_features/constant_expression.qasm` | feature_probe | A compile-time const declaration may be an importer limitation, not a Norm defect. |
| `cases/10_language_features/symbolic_product.qasm` | feature_probe | Probe non-affine symbolic expression support. |
| `cases/10_language_features/static_for.qasm` | policy_probe | A static loop is valid, but should be unrolled in a frontend before a flat DAG normalizer. |
| `cases/10_language_features/custom_gate_named_h.qasm` | feature_probe | Do not mark a generic custom gate as normalized solely because its name is h. |
| `cases/10_language_features/custom_gate_named_rx.qasm` | feature_probe | A user-defined rx name need not mean Qiskit RXGate. Dispatch must inspect the operation type/definition. |
| `cases/11_reject_policy/measure_then_h.qasm` | reject_policy | A measured qubit is reused by a quantum gate. |
| `cases/11_reject_policy/measured_qubit_as_control.qasm` | reject_policy | Measurement followed by using that qubit as a CX control is not terminal. |
| `cases/11_reject_policy/measured_qubit_as_target.qasm` | reject_policy | Measurement followed by using that qubit as a CX target is not terminal. |
| `cases/11_reject_policy/measure_then_custom.qasm` | reject_policy | A gate hidden inside a custom definition still reuses a measured qubit. |
| `cases/11_reject_policy/reset_first.qasm` | reject_policy | Reset is outside the chosen unitary-only computation model, even at the beginning. |
| `cases/11_reject_policy/reset_after_entanglement.qasm` | reject_policy | Dropping reset changes the computation. |
| `cases/11_reject_policy/measurement_feedforward.qasm` | reject_policy | Classical feed-forward remains unsupported even if the measured qubit is never reused. |
| `cases/11_reject_policy/if_else.qasm` | reject_policy | Reject control-flow nodes rather than silently normalizing only one branch. |
| `cases/11_reject_policy/while_measurement.qasm` | reject_policy | Dynamic loops are not a flat unitary circuit. |
| `cases/12_invalid_qasm/missing_semicolon.qasm` | invalid_qasm | Syntax error: missing operation semicolon. |
| `cases/12_invalid_qasm/unknown_gate.qasm` | invalid_qasm | Semantic error: undefined gate. |
| `cases/12_invalid_qasm/undeclared_angle.qasm` | invalid_qasm | Semantic error: undeclared parameter theta. |
| `cases/12_invalid_qasm/unknown_qubit.qasm` | invalid_qasm | Semantic error: undeclared qubit. |
| `cases/12_invalid_qasm/qubit_out_of_range.qasm` | invalid_qasm | Semantic error: out-of-range array index. |
| `cases/12_invalid_qasm/classical_out_of_range.qasm` | invalid_qasm | Semantic error: classical destination out of range. |
| `cases/12_invalid_qasm/duplicate_cx_operand.qasm` | invalid_qasm | Semantic error: a controlled two-qubit gate cannot use the same qubit twice. |
| `cases/12_invalid_qasm/duplicate_ccx_operand.qasm` | invalid_qasm | Semantic error: repeated qubit in one three-qubit operation. |
| `cases/12_invalid_qasm/too_few_qubits.qasm` | invalid_qasm | Wrong gate arity: CX requires two qubit operands. |
| `cases/12_invalid_qasm/too_many_qubits.qasm` | invalid_qasm | Wrong gate arity: H has one operand; comma-separated operands are not broadcasting. |
| `cases/12_invalid_qasm/missing_angle.qasm` | invalid_qasm | Wrong parameter arity: RX needs an angle. |
| `cases/12_invalid_qasm/extra_angle.qasm` | invalid_qasm | Wrong parameter arity: RY has one angle. |
| `cases/12_invalid_qasm/classical_as_qubit.qasm` | invalid_qasm | Type error: a classical bit is not a gate operand. |
| `cases/12_invalid_qasm/mismatched_broadcast.qasm` | invalid_qasm | Broadcast arrays must have equal lengths. |
| `cases/12_invalid_qasm/mismatched_measurement.qasm` | invalid_qasm | Measurement source/destination lengths differ. |
| `cases/12_invalid_qasm/duplicate_declaration.qasm` | invalid_qasm | Duplicate declaration in one scope. |
| `cases/12_invalid_qasm/self_recursive_gate.qasm` | invalid_qasm | Recursive gate definitions are not legal OpenQASM; reject before Norm recursion. |
| `cases/12_invalid_qasm/measurement_in_gate.qasm` | invalid_qasm | A gate definition cannot contain measurement. |
| `cases/12_invalid_qasm/missing_std_include.qasm` | invalid_qasm | Without an include or definition, h is not a built-in; only U and gphase are built-in gates. |
| `cases/12_invalid_qasm/nonstandard_rzz_undefined.qasm` | invalid_qasm | RZZ is not automatically defined by the OpenQASM 3.0 standard library; provide a custom definition. |
| `cases/13_stress/seed_17_five_qubits.qasm` | normalize | Deterministic mixed circuit, seed 17, 160 source operations. No cancellation-only construction. |
| `cases/13_stress/seed_41_five_qubits.qasm` | normalize | Deterministic mixed circuit, seed 41, 160 source operations. No cancellation-only construction. |
| `cases/13_stress/seed_103_five_qubits.qasm` | normalize | Deterministic mixed circuit, seed 103, 160 source operations. No cancellation-only construction. |
| `cases/13_stress/seed_997_five_qubits.qasm` | normalize | Deterministic mixed circuit, seed 997, 160 source operations. No cancellation-only construction. |
| `cases/13_stress/many_replacements.qasm` | normalize | 240 source operations exercise mutation while iterating and repeated lowering on six wires. |
| `cases/13_stress/custom_reuse_120.qasm` | normalize | Repeated custom invocations expose shared replacement objects and stale cache state. |
| `cases/14_optimizer_traps/noncommuting_rotation_order.qasm` | normalize | Do not reverse operations while building a sub-DAG. |
| `cases/14_optimizer_traps/h_separates_rz.qasm` | normalize | Never merge RZ rotations through a noncommuting H. |
| `cases/14_optimizer_traps/cx_target_separates_rz.qasm` | normalize | RZ on the CX target cannot generally be moved through CX. |
| `cases/14_optimizer_traps/adjacent_inverse.qasm` | normalize | Correctness requires identity behavior, not a minimal output gate count. |
| `cases/14_optimizer_traps/two_x.qasm` | normalize | Two X gates may remain after normalization; cancellation is an optimization, not a normalization requirement. |
| `cases/14_optimizer_traps/cx_direction_changes.qasm` | normalize | Opposite-direction CX gates do not cancel. |
| `cases/14_optimizer_traps/tiny_angle_aggregate.qasm` | normalize | Repeated small rotations must not all be dropped as zero. |
