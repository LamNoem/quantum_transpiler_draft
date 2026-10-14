from qiskit import QuantumCircuit
from qiskit.dagcircuit import DAGCircuit
from qiskit.converters import circuit_to_dag

# Build a sample circuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)

# Convert to DAGCircuit
dag = circuit_to_dag(qc)

# Iterate over all edges in the DAG
for source, dest, wire in dag.edges():
    print(f"From {source.name} to {dest.name} along wire {wire}")