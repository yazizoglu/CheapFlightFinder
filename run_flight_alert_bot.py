#!/usr/bin/env python
"""
Entry point script to run the flight alert bot.
"""
import sys
import os
import logging

# Add the parent directory to sys.path to make the flight_alert_bot package importable
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import required modules
from flight_alert_bot.config import DEBUG
from flight_alert_bot.main import run_once, run_continuously

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("flight_alert_bot_runner")

def main():
    """Main entry point for the script."""
    logger.info("Starting flight alert bot")
    
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        logger.info("Running in one-time mode")
        run_once()
    else:
        logger.info("Running in continuous mode")
        run_continuously()

if __name__ == "__main__":
    main()