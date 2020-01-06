import sys
from mailparser import main
import logging
logging.basicConfig(level=logging.WARN)
sys.exit(main())
