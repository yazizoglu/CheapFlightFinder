#!/usr/bin/env python
"""
Entry point for the flight alert bot.
This script is used by the workflow to run the bot.
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
logger = logging.getLogger("flight_bot_runner")

def fetch_one_way_flights():
    """Fetch one-way flight data."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fetch_data", 
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "flight_alert_bot/fetch_data.py")
    )
    fetch_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fetch_module)
    return fetch_module.fetch_one_way_flights()

def fetch_return_flights():
    """Fetch return flight data."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fetch_return", 
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "flight_alert_bot/fetch_return_flights.py")
    )
    fetch_return_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fetch_return_module)
    return fetch_return_module.fetch_return_flights()

def create_flight_combinations():
    """Create flight combinations."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "create_combined", 
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "flight_alert_bot/create_combined_flights.py")
    )
    combined_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(combined_module)
    return combined_module.create_flight_combinations()

def generate_and_send_alerts():
    """Generate and send alerts."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "generate_alerts", 
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "flight_alert_bot/generate_alerts.py")
    )
    alerts_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(alerts_module)
    return alerts_module.generate_and_send_alerts()

def run_scheduled_task():
    """Run the scheduled flight data fetch and alert generation."""
    start_time = time.time()
    
    try:
        logger.info("Starting scheduled task execution")
        
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
        
        return True
    
    except Exception as e:
        logger.error(f"Error in scheduled task: {e}")
        logger.exception("Stack trace:")
        return False

def run_once():
    """Run the flight data fetch and alert generation once."""
    run_scheduled_task()

def main():
    """Main entry point for the flight alert bot."""
    logger.info("Starting flight alert bot")
    
    # Run the scheduled task once
    run_once()

if __name__ == "__main__":
    main()