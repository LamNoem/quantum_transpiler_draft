import copy
from math import pi

from qiskit import QuantumCircuit
from qiskit.circuit import Barrier, Measure
from qiskit.circuit.library import HGate, CXGate, SwapGate, RZGate, SXGate, XGate, ECRGate, CZGate
from qiskit.converters import circuit_to_dag
from qiskit.dagcircuit import DAGCircuit

from general.log_config import logging
from parser_0.input_target import Target


logger = logging.getLogger(__name__)


class ToNativeTranslator:

    def __init__(self, routed_dag: DAGCircuit, target: Target):
        # Keep a reference to the input; modify only the working copy.
        self.orig_dag = routed_dag
        self.translated_dag = copy.deepcopy(routed_dag)

        self.native_gates = self.native_gates_as_gates(target.native_gates)
        self.native_arities = target.gate_arities
        self.native_set = target.native_set

        self.translate(self.translated_dag)

    def native_gates_as_gates(self,gate_names: list[str]):
        name_to_gate = {
            "h": HGate, 
            "x": XGate, 
            "rz": RZGate, 
            "cx": CXGate,
            "sx": SXGate,
            "cz": CZGate,
            "ecr": ECRGate
        }
        return [ name_to_gate[name] for name in gate_names]

    def is_native_gate(self, op) -> bool:
        """

        Assumption:
            Input operations are recognized standard gates from the
            earlier compiler stages.

        Barriers and measurements are handled separately.
        """

        if isinstance(op, CXGate) and op.ctrl_state != 1:
            return False
        if not isinstance(op,tuple(self.native_gates)):
            return False
        return self.native_arities.get(op.name) == op.num_qubits
        

    def append_native_h(self, qc: QuantumCircuit, qubit: int):
        """

        """
        if self.is_native_gate(HGate()):
            qc.append(HGate(), [qubit])
        else:
            qc.append(RZGate(pi / 2), [qubit])
            qc.append(SXGate(),[qubit])
            qc.append(RZGate(pi/2),[qubit])
            qc.global_phase += pi/4

    def append_native_cx(
        self,
        qc: QuantumCircuit,
        control: int,
        target_qubit: int,
    ):
        """
        The H helper accumulates its phase on this same qc.
        """
        if self.is_native_gate(CXGate()):
            qc.append(CXGate(), [control, target_qubit])
            
        elif self.native_set == "ibm_ecr":
            qc.append(XGate(),[control])
            qc.append(ECRGate(),[control, target_qubit])
            qc.append(RZGate(pi/2),[control])
            qc.append(SXGate(),[target_qubit])
        elif self.native_set == "ibm_cz":
            self.append_native_h(qc,target_qubit)
            qc.append(CZGate(),[control, target_qubit])
            self.append_native_h(qc, target_qubit)
        else:
            raise ValueError(f"no cx translation for native gate set {self.native_set} as yet.")


    def translate_node(self, node) -> DAGCircuit:
        # Build only the small replacement circuit.
        # Local wire i corresponds to node.qargs[i].
        qc = QuantumCircuit(len(node.qargs))

        if isinstance(node.op, HGate):
            self.append_native_h(qc, 0)

        elif isinstance(node.op, CXGate):
            if node.op.ctrl_state != 1:
                raise ValueError(
                    "Expected an ordinary CX with ctrl_state=1." #improv: what do we do here ? swap cx swap?
                )

            self.append_native_cx(qc, 0, 1)

        elif isinstance(node.op, SwapGate):
            # Needed only if routing leaves explicit SWAP nodes. -> it does not but no big harm in keeping
            self.append_native_cx(qc, 0, 1)
            self.append_native_cx(qc, 1, 0)
            self.append_native_cx(qc, 0, 1)

        else:
            raise ValueError(
                f"No translation rule for {node.op.name!r} "
                f"with native set {self.native_set!r}."
            )

        return circuit_to_dag(qc)

    def translate(self, dag: DAGCircuit) -> DAGCircuit:
        for node in dag.op_nodes():

            # Preserve the nongate operations supported by this pass.
            if isinstance(node.op, (Barrier, Measure)):
                continue

            # Native gates need no replacement.
            if self.is_native_gate(node.op):
                continue

            sub_dag = self.translate_node(node)

            # One traversal requires fully native replacements.
            if not all(
                self.is_native_gate(n.op)
                for n in sub_dag.op_nodes()
            ):
                raise ValueError(
                    f"Replacement for {node.op.name!r} "
                    "contains nonnative gates."
                )

            # Map the replacement's local wires to the original operands.
            wire_map = dict(zip(sub_dag.qubits, node.qargs))

            dag.substitute_node_with_dag(
                node,
                sub_dag,
                wires=wire_map,
            )

        self.validate_output(dag)

        logger.info(
            "Native gate translation complete for %s",
            self.native_set,
        )

        return dag

    def validate_output(self, dag: DAGCircuit):
        for node in dag.op_nodes():

            if isinstance(node.op, (Barrier, Measure)):
                continue

            if not self.is_native_gate(node.op):
                raise ValueError(
                    f"Output contains nonnative gate {node.op.name!r}."
                )