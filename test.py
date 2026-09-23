from qiskit.circuit.library import get_standard_gate_name_mapping
from qiskit.converters import circuit_to_dag



gates = get_standard_gate_name_mapping()

for name, gate in gates.items():
    print(
        name,
        "definition:",
        gate.definition is not None,
        gate.definition if gate.definition is not None else False,
        "decompositions:",
        len(gate.decompositions),
        gate.decompositions
    )
    if gate.definition is not None:
        sub_dag = circuit_to_dag(gate.definition)
        print("sub_dag:", sub_dag)