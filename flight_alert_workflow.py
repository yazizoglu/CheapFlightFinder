#!/usr/bin/env python
"""
Continuous runner for the flight alert bot.
This is designed to be used as a workflow script.
"""
import os
import sys
import time
import logging
from datetime import datetime

# Add the parent directory to sys.path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("flight_alert_workflow")

def run_bot_once():
    """Run the flight alert bot once."""
    try:
        # Import the necessary modules
        from flight_alert_bot.config import DEBUG, SCRAPE_INTERVAL_MINUTES
        from flight_alert_bot.fetch_data import fetch_one_way_flights
        from flight_alert_bot.fetch_return_flights import fetch_return_flights
        from flight_alert_bot.create_combined_flights import create_flight_combinations
        from flight_alert_bot.generate_alerts import generate_and_send_alerts
        
        start_time = time.time()
        
        # Step 1: Fetch one-way flights
        logger.info("Step 1: Fetching one-way flights")
        one_way_flights = fetch_one_way_flights()
        logger.info(f"Fetched {one_way_flights} one-way flights")
        
        # Step 2: Fetch return flights
        logger.info("Step 2: Fetching return flights")
        return_flights = fetch_return_flights()
        logger.info(f"Fetched {return_flights} return flights")
        
        # Step 3: Create flight combinations
        logger.info("Step 3: Creating flight combinations")
        combinations = create_flight_combinations()
        logger.info(f"Created {combinations} flight combinations")
        
        # Step 4: Generate and send alerts
        logger.info("Step 4: Generating and sending alerts")
        alerts = generate_and_send_alerts()
        logger.info(f"Generated and sent {alerts} alerts")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        logger.info(f"Total execution time: {execution_time:.2f} seconds")
        
        return SCRAPE_INTERVAL_MINUTES  # Return the interval for the next run
    except Exception as e:
        logger.error(f"Error running flight alert bot: {e}")
        logger.exception("Stack trace:")
        return 15  # Return a default interval (15 minutes) if there was an error

def main():
    """Main entry point for the flight alert workflow."""
    logger.info("Starting flight alert workflow - continuous mode")
    
    try:
        while True:
            # Run the bot once
            logger.info("Starting new iteration")
            interval_minutes = run_bot_once()
            
            # Sleep until the next run
            logger.info(f"Sleeping for {interval_minutes} minutes until next run...")
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down...")
    except Exception as e:
        logger.error(f"Unhandled exception in main loop: {e}")
        logger.exception("Stack trace:")
        # Sleep briefly to allow logs to be written before potentially restarting
        time.sleep(5)
        sys.exit(1)

if __name__ == "__main__":
    main()