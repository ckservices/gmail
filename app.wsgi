import sys
import logging
sys.path.insert(0, '/app')
from app import app as application
logging.basicConfig(stream=sys.stderr)
