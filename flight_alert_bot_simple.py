#!/usr/bin/env python
"""
Simplified entry point for the flight alert bot.
This script directly implements the functionality needed for the workflow.
"""
import os
import sys
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("flight_alert_bot")

def run_bot():
    """Run the flight alert bot once."""
    try:
        # Import the main module
        from flight_alert_bot.main import run_once
        
        # Run the bot once
        logger.info("Starting flight alert bot")
        result = run_once()
        
        if result:
            logger.info("Flight alert bot completed successfully")
        else:
            logger.error("Flight alert bot failed")
            
        return result
    except Exception as e:
        logger.error(f"Error running flight alert bot: {e}")
        logger.exception("Stack trace:")
        return False

if __name__ == "__main__":
    # Run the bot
    run_bot()