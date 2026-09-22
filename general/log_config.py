import logging
from pathlib import Path

# Configure root logger to write to a file instead of print/console
logging.basicConfig(
    filename=Path(__file__).resolve().parent.parent / 'log',
    filemode='a',  # 'a' appends, 'w' overwrites each run
    level=logging.INFO,  # Set threshold level (DEBUG, INFO, WARNING, ERROR)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
