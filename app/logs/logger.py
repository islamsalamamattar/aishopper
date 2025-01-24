import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the base level to DEBUG to capture all messages
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Logs all levels to stdout
    ]
)

# Separate handlers for different log levels
info_handler = logging.FileHandler('/home/admin/arobah/arobah_api/app/logs/info.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))

debug_handler = logging.FileHandler('/home/admin/arobah/arobah_api/app/logs/debug.log')
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))

warning_handler = logging.FileHandler('/home/admin/arobah/arobah_api/app/logs/warning.log')
warning_handler.setLevel(logging.WARNING)
warning_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))

error_handler = logging.FileHandler('/home/admin/arobah/arobah_api/app/logs/error.log')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))

# Get the logger and attach handlers
logger = logging.getLogger(__name__)
logger.addHandler(info_handler)
logger.addHandler(debug_handler)
logger.addHandler(warning_handler)
logger.addHandler(error_handler)
