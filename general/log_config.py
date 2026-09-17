import logging

# Configure root logger to write to a file instead of print/console
logging.basicConfig(
    filename='C:\Users\noemi\OneDrive - University of Waterloo\quantum_compiler_draft\log',
    filemode='a',  # 'a' appends, 'w' overwrites each run
    level=logging.INFO,  # Set threshold level (DEBUG, INFO, WARNING, ERROR)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)