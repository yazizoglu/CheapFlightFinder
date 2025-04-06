#!/usr/bin/env python
"""
Entry point for the flight alert bot.
This script is used to run the bot directly.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("run_bot")

def main():
    """Main entry point for the script."""
    logger.info("Starting flight alert bot")
    
    try:
        # Add the current directory to sys.path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        
        # Import local modules directly without package structure
        import time
        from datetime import datetime
        
        # Load configuration
        sys.path.append(os.path.join(current_dir, "flight_alert_bot"))
        
        # Import the required modules from local paths
        from flight_alert_bot.fetch_data import fetch_one_way_flights
        from flight_alert_bot.fetch_return_flights import fetch_return_flights
        from flight_alert_bot.create_combined_flights import create_flight_combinations
        from flight_alert_bot.generate_alerts import generate_and_send_alerts
        
        # Execute steps
        logger.info("Starting one-time execution")
        
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
        
        logger.info("Bot execution completed successfully")
        
    except Exception as e:
        logger.error(f"Error running flight alert bot: {e}")
        logger.exception("Stack trace:")
        sys.exit(1)

if __name__ == "__main__":
    main()