#!/usr/bin/env python
"""
Entry point for the flight alert bot.
This is used by the workflow to run the bot.
"""
import os
import sys
import logging
import time
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("flight_alert_bot_workflow")

def main():
    """Main entry point for the script."""
    logger.info("Starting flight alert bot workflow")
    
    try:
        # Run the bot using the start_flight_bot.py script
        bot_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "start_flight_bot.py")
        logger.info(f"Running bot script: {bot_script_path}")
        
        # Run the script
        while True:
            logger.info("Starting flight alert bot iteration")
            result = subprocess.run(
                [sys.executable, bot_script_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Log the result
            if result.returncode == 0:
                logger.info("Flight alert bot completed successfully")
                logger.info(f"Output: {result.stdout}")
            else:
                logger.error(f"Flight alert bot failed with exit code {result.returncode}")
                logger.error(f"Error: {result.stderr}")
                logger.error(f"Output: {result.stdout}")
            
            # Wait for a while before the next run (e.g., 15 minutes)
            logger.info("Sleeping for 15 minutes until next run...")
            time.sleep(15 * 60)
    
    except Exception as e:
        logger.error(f"Error running flight alert bot: {e}")
        logger.exception("Stack trace:")
        # Sleep briefly to allow logs to be written
        time.sleep(5)
        sys.exit(1)

if __name__ == "__main__":
    main()