"""
Flask web application for flight price tracker.
Displays flight data and allows users to configure alerts.
"""
import os
import json
import sys
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Try to import airport data utility, create fallback if not available
try:
    from flight_alert_bot.utils.airport_data import get_city_and_code, get_city_name
except ImportError:
    def get_city_name(airport_code):
        return airport_code
    def get_city_and_code(airport_code):
        return airport_code

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "flight-tracker-secret")

# MongoDB connection
mongodb_uri = os.environ.get("MONGODB_URI")
db_name = os.environ.get("DB_NAME", "flight_tracker")

# Flag to determine if we should use mock data
use_mock_data = os.environ.get("MOCK_DATA", "false").lower() == "true"

# MongoDB client and collections
mongo_client = None
db = None
flight_collection = None
alert_collection = None
combination_collection = None

# Try to establish MongoDB connection if not using mock data
if not use_mock_data and mongodb_uri:
    try:
        mongo_client = MongoClient(mongodb_uri)
        # Check if the connection is valid
        mongo_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        db = mongo_client[db_name]
        flight_collection = db.flight_prices  # Doğru koleksiyon adı
        alert_collection = db.alerts
        combination_collection = db.round_trip_combinations  # Doğru koleksiyon adı
        
        # Create indexes if they don't exist
        flight_collection.create_index([("origin", 1), ("destination", 1), ("departure_date", 1)])
        alert_collection.create_index([("flight_id", 1)])
        combination_collection.create_index([("outbound.origin", 1), ("outbound.destination", 1)])
        
        logger.info("MongoDB collections and indexes set up")
    except ConnectionFailure:
        logger.error("Failed to connect to MongoDB, falling back to mock data")
        use_mock_data = True
else:
    logger.warning("Using mock data (MongoDB connection not configured)")
    use_mock_data = True

# In-memory storage for mock data
mock_flights = []
mock_alerts = []

# Load mock data
def load_mock_data():
    """Load mock data for development."""
    global mock_flights, mock_alerts
    
    # Generate mock flight data with durations
    mock_flights = [
        {
            "id": f"flight-{i}",
            "origin": origins[i % len(origins)],
            "destination": destinations[i % len(destinations)],
            "departure_date": "2025-06-15",
            "return_date": "2025-06-25" if i % 3 != 0 else None,
            "price": 8500 + (i * 750),
            "currency": "TRY",
            "airline": airlines[i % len(airlines)],
            "duration_minutes": 180 + (i * 45),  # Varying durations
            "flightMaxDuration": 180 + (i * 45),  # Same as duration_minutes
            "stops": i % 3,
            "timestamp": datetime.now().isoformat(),
            "is_round_trip": i % 3 != 0
        }
        for i in range(10)
    ]
    
    # Generate mock alerts
    mock_alerts = [
        {
            "id": f"alert-{i}",
            "flight_id": f"flight-{i}",
            "price_drop_percentage": 15 + (i * 2),
            "previous_price": 10500 + (i * 1000),
            "current_price": 8500 + (i * 750),
            "currency": "TRY",
            "timestamp": datetime.now().isoformat(),
            "message": f"{origins[i % len(origins)]} - {destinations[i % len(destinations)]} uçuşunda fiyat düşüşü! Şimdi {8500 + (i * 750)} TL"
        }
        for i in range(3)
    ]

# Mock data sources
origins = ["IST", "JFK", "LHR", "CDG", "DXB"]
destinations = ["JFK", "LHR", "IST", "SFO", "SIN"]
airlines = ["Turkish Airlines", "Delta", "British Airways", "Air France", "Emirates"]

# Routes
@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/flights')
def get_flights():
    """API endpoint to get flight data."""
    # Get query parameters
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    departure_date = request.args.get('departure_date')
    
    if use_mock_data:
        # Use mock data
        if not mock_flights:
            load_mock_data()
        
        # Filter flights based on query parameters
        filtered_flights = mock_flights
        
        if origin:
            filtered_flights = [f for f in filtered_flights if f['origin'] == origin]
        
        if destination:
            filtered_flights = [f for f in filtered_flights if f['destination'] == destination]
        
        if departure_date:
            filtered_flights = [f for f in filtered_flights if f['departure_date'] == departure_date]
    else:
        # Use MongoDB
        try:
            query = {}
            if origin:
                query['origin'] = origin
            if destination:
                query['destination'] = destination
            if departure_date:
                query['departure_date'] = departure_date
                
            # If no date filter is specified, only show flights for future dates
            if not departure_date:
                today = datetime.now().strftime('%Y-%m-%d')
                # Get flights for the next 90-120 days
                future_date = (datetime.now() + timedelta(days=120)).strftime('%Y-%m-%d')
                query['departure_date'] = {'$gte': today, '$lte': future_date}
            
            # Get flights from MongoDB without filtering invalid prices at query level
            filtered_flights = list(flight_collection.find(query, {'_id': 0}))
            
            # Filter out flights with invalid prices in Python code
            filtered_flights = [f for f in filtered_flights if f.get('price', 0) != 9999 and f.get('price', 0) != -1 and f.get('price', 0) > 0]
            
            # Convert ObjectId to string if present
            for flight in filtered_flights:
                if '_id' in flight and hasattr(flight['_id'], '__str__'):
                    flight['_id'] = str(flight['_id'])
        except Exception as e:
            logger.error(f"Error retrieving flights from MongoDB: {e}")
            if not mock_flights:
                load_mock_data()
            filtered_flights = mock_flights
    
    # Add city names to the flights and handle no_flights_found cases
    for flight in filtered_flights:
        flight['origin_city'] = get_city_name(flight['origin'])
        flight['destination_city'] = get_city_name(flight['destination'])
        flight['origin_display'] = get_city_and_code(flight['origin'])
        flight['destination_display'] = get_city_and_code(flight['destination'])
        
        # Check for duration directly first (string format like "3h 35m")
        duration_str = flight.get('duration')
        if duration_str and isinstance(duration_str, str):
            # Already in display format, just use it directly
            flight['duration_display'] = duration_str
            
            # Also parse it to get duration_minutes for calculations
            try:
                # Parse the duration string (e.g. "3h 35m" to minutes)
                hours = 0
                mins = 0
                if 'h' in duration_str:
                    hours_part = duration_str.split('h')[0].strip()
                    hours = int(hours_part) if hours_part.isdigit() else 0
                if 'm' in duration_str:
                    if 'h' in duration_str:
                        mins_part = duration_str.split('h')[1].split('m')[0].strip()
                    else:
                        mins_part = duration_str.split('m')[0].strip()
                    mins = int(mins_part) if mins_part.isdigit() else 0
                
                # Calculate total minutes
                flight['duration_minutes'] = (hours * 60) + mins
                flight['flightMaxDuration'] = flight['duration_minutes']
            except Exception as e:
                logger.error(f"Error parsing duration string: {duration_str}, error: {e}")
                flight['duration_minutes'] = 0
                flight['flightMaxDuration'] = 0
        else:
            # Format duration for display (convert minutes to hours and minutes)
            # Check for duration_minutes first, then flightMaxDuration as fallback
            duration_mins = flight.get('duration_minutes', flight.get('flightMaxDuration', 0))
            if duration_mins > 0:
                hours = duration_mins // 60
                mins = duration_mins % 60
                flight['duration_display'] = f"{hours}h {mins}m"
            else:
                flight['duration_display'] = 'Unknown'
    
    return jsonify(filtered_flights)

@app.route('/api/alerts')
def get_alerts():
    """API endpoint to get alert data."""
    if use_mock_data:
        # Use mock data
        if not mock_alerts:
            load_mock_data()
        alerts = mock_alerts
    else:
        # Use MongoDB
        try:
            # Get alerts from MongoDB, newest first
            alerts = list(alert_collection.find({}, {'_id': 0}).sort('timestamp', -1))
            
            # Convert ObjectId to string if present
            for alert in alerts:
                if '_id' in alert and hasattr(alert['_id'], '__str__'):
                    alert['_id'] = str(alert['_id'])
                    
                # Add origin and destination display if not present
                if 'origin' in alert and 'destination' in alert:
                    alert['origin_display'] = get_city_and_code(alert['origin'])
                    alert['destination_display'] = get_city_and_code(alert['destination'])
        except Exception as e:
            logger.error(f"Error retrieving alerts from MongoDB: {e}")
            if not mock_alerts:
                load_mock_data()
            alerts = mock_alerts
    
    return jsonify(alerts)

@app.route('/api/city-pairs')
def get_city_pairs():
    """API endpoint to get available city pairs."""
    if use_mock_data:
        # Use mock data
        city_pairs = [
            {"origin": "IST", "destination": "JFK"},
            {"origin": "IST", "destination": "LHR"},
            {"origin": "JFK", "destination": "LHR"},
            {"origin": "JFK", "destination": "SFO"},
            {"origin": "LHR", "destination": "CDG"}
        ]
    else:
        # Use MongoDB
        try:
            # Get distinct origin-destination pairs from the database
            origins = list(flight_collection.distinct('origin'))
            destinations = list(flight_collection.distinct('destination'))
            
            # Create all possible combinations
            city_pairs = []
            for origin in origins:
                for destination in destinations:
                    # Don't include same origin and destination
                    if origin != destination:
                        # Check if this pair has any flights
                        count = flight_collection.count_documents({
                            'origin': origin,
                            'destination': destination
                        })
                        if count > 0:
                            city_pairs.append({
                                'origin': origin,
                                'destination': destination
                            })
        except Exception as e:
            logger.error(f"Error retrieving city pairs from MongoDB: {e}")
            city_pairs = [
                {"origin": "IST", "destination": "JFK"},
                {"origin": "IST", "destination": "LHR"},
                {"origin": "JFK", "destination": "LHR"},
                {"origin": "JFK", "destination": "SFO"},
                {"origin": "LHR", "destination": "CDG"}
            ]
    
    # Add city names
    for pair in city_pairs:
        pair['origin_display'] = get_city_and_code(pair['origin'])
        pair['destination_display'] = get_city_and_code(pair['destination'])
    
    return jsonify(city_pairs)

@app.route('/api/statistics')
def get_statistics():
    """API endpoint to get statistical data about flights and alerts."""
    try:
        if use_mock_data:
            # Use mock data
            if not mock_flights:
                load_mock_data()
            
            flights = mock_flights
            alerts = mock_alerts
        else:
            # Use MongoDB
            flights = list(flight_collection.find({}, {'_id': 0}))
            alerts = list(alert_collection.find({}, {'_id': 0}))
            
        # Calculate statistics specific to routes instead of global averages
        if flights:
            # Filter out "no flights found" entries for price calculations
            valid_flights = [f for f in flights if f.get('price', 0) > 0 and f.get('price', 0) != 9999]
            
            # We won't calculate global average/min/max as they're not meaningful across different routes
            avg_price = 0  # We're not showing this anymore
            min_price = 0  # We're not showing this anymore
            max_price = 0  # We're not showing this anymore
                
            # Count round trips and one-way trips
            round_trips = sum(1 for f in flights if f.get('is_round_trip', False))
            one_way_trips = sum(1 for f in flights if not f.get('is_round_trip', False))
            
            # Find most common origin and destination
            origins = [f['origin'] for f in flights]
            destinations = [f['destination'] for f in flights]
            
            most_common_origin = max(set(origins), key=origins.count) if origins else None
            most_common_destination = max(set(destinations), key=destinations.count) if destinations else None
            
            # Get city display names
            most_common_origin_display = get_city_and_code(most_common_origin) if most_common_origin else None
            most_common_destination_display = get_city_and_code(most_common_destination) if most_common_destination else None
        else:
            avg_price = 0
            min_price = 0
            max_price = 0
            round_trips = 0
            one_way_trips = 0
            most_common_origin = None
            most_common_destination = None
            most_common_origin_display = None
            most_common_destination_display = None
            
        stats = {
            "total_flights": len(flights),
            "total_alerts": len(alerts),
            "round_trips": round_trips,
            "one_way_trips": one_way_trips,
            "most_common_origin": most_common_origin,
            "most_common_origin_display": most_common_origin_display,
            "most_common_destination": most_common_destination,
            "most_common_destination_display": most_common_destination_display,
            "data_source": "MongoDB" if not use_mock_data else "Mock Data"
        }
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        # Return default values if there's an error
        stats = {
            "total_flights": 0,
            "total_alerts": 0,
            "round_trips": 0,
            "one_way_trips": 0,
            "most_common_origin": None,
            "most_common_destination": None,
            "data_source": "Error",
            "error": str(e)
        }
    
    return jsonify(stats)

@app.route('/config')
def config_page():
    """Configuration page."""
    return render_template("config.html")

def update_env_file(data):
    """Update the .env file with new configuration values."""
    try:
        # Read existing .env file
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Create a dictionary of existing values
        env_vars = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
        
        # Update values with new data
        if 'scrape_interval_minutes' in data:
            env_vars['SCRAPE_INTERVAL_MINUTES'] = str(data['scrape_interval_minutes'])
        
        if 'data_retention_days' in data:
            env_vars['DATA_RETENTION_DAYS'] = str(data['data_retention_days'])
        
        if 'debug_mode' in data:
            env_vars['DEBUG'] = str(data['debug_mode']).lower()
        
        if 'routes' in data:
            # Rotaları virgülle ayırarak ve boşluk bırakmadan kaydet
            env_vars['ROUTES'] = ','.join(data['routes'])
        
        if 'departure_date_start' in data:
            env_vars['DEPARTURE_DATE_START'] = str(data['departure_date_start'])
        
        if 'departure_date_end' in data:
            env_vars['DEPARTURE_DATE_END'] = str(data['departure_date_end'])
        
        # Add new flight-specific stay settings
        if 'short_flight_min_stay' in data:
            env_vars['SHORT_FLIGHT_MIN_STAY'] = str(data['short_flight_min_stay'])
        
        if 'short_flight_max_stay' in data:
            env_vars['SHORT_FLIGHT_MAX_STAY'] = str(data['short_flight_max_stay'])
        
        if 'long_flight_min_stay' in data:
            env_vars['LONG_FLIGHT_MIN_STAY'] = str(data['long_flight_min_stay'])
        
        if 'long_flight_max_stay' in data:
            env_vars['LONG_FLIGHT_MAX_STAY'] = str(data['long_flight_max_stay'])
        
        # Legacy settings
        if 'return_date_min_stay' in data:
            env_vars['RETURN_DATE_MIN_STAY'] = str(data['return_date_min_stay'])
        
        if 'return_date_max_stay' in data:
            env_vars['RETURN_DATE_MAX_STAY'] = str(data['return_date_max_stay'])
        
        if 'price_drop_percentage' in data:
            env_vars['PRICE_DROP_PERCENTAGE'] = str(data['price_drop_percentage'])
        
        if 'price_drop_z_score' in data:
            env_vars['PRICE_DROP_Z_SCORE'] = str(data['price_drop_z_score'])
        
        if 'max_price_try' in data:
            env_vars['MAX_PRICE_TRY'] = str(data['max_price_try'])
        
        if 'use_real_time_currency_rates' in data:
            env_vars['USE_REAL_TIME_CURRENCY_RATES'] = str(data['use_real_time_currency_rates']).lower()
        
        # Currency rates
        if 'currency_rates' in data:
            for currency, rate in data['currency_rates'].items():
                env_key = f"CURRENCY_RATE_{currency.upper()}"
                env_vars[env_key] = str(rate)
        
        # Telegram settings
        if 'telegram_enabled' in data:
            env_vars['TELEGRAM_ENABLED'] = str(data['telegram_enabled']).lower()
        
        if 'telegram_bot_token' in data:
            env_vars['TELEGRAM_BOT_TOKEN'] = data['telegram_bot_token']
        
        if 'telegram_chat_id' in data:
            env_vars['TELEGRAM_CHAT_ID'] = data['telegram_chat_id']
        
        # Write updated .env file
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Log successful update
        logger.info(f"Updated .env file with new configuration values")
        return True
    
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")
        return False


@app.route('/api/config', methods=['GET', 'POST'])
def config_api():
    """API endpoint to get and update configuration."""
    from flight_alert_bot import config as bot_config
    
    if request.method == 'POST':
        try:
            # Get the JSON data from the request
            data = request.json
            
            # Basic validation
            if data.get('scrape_interval_minutes') < 5:
                return jsonify({"success": False, "message": "Scrape interval must be at least 5 minutes"})
            
            # Update the .env file with the new configuration
            success = update_env_file(data)
            
            if success:
                # Notify the user that a restart is required for changes to take effect
                return jsonify({
                    "success": True, 
                    "message": "Configuration updated. Changes will take effect on next workflow restart."
                })
            else:
                return jsonify({
                    "success": False, 
                    "message": "Error updating configuration file. Please check server logs."
                })
                
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return jsonify({"success": False, "message": str(e)})
    
    # Return current configuration
    config_data = {
        "scrape_interval_minutes": bot_config.SCRAPE_INTERVAL_MINUTES,
        "data_retention_days": bot_config.DATA_RETENTION_DAYS,
        "debug_mode": bot_config.DEBUG,
        
        "routes": bot_config.ROUTES,
        
        "departure_date_start": bot_config.DEPARTURE_DATE_START,
        "departure_date_end": bot_config.DEPARTURE_DATE_END,
        
        # New flight-specific stay settings
        "short_flight_min_stay": bot_config.SHORT_FLIGHT_MIN_STAY,
        "short_flight_max_stay": bot_config.SHORT_FLIGHT_MAX_STAY,
        "long_flight_min_stay": bot_config.LONG_FLIGHT_MIN_STAY,
        "long_flight_max_stay": bot_config.LONG_FLIGHT_MAX_STAY,
        
        # Legacy settings
        "return_date_min_stay": bot_config.RETURN_DATE_MIN_STAY,
        "return_date_max_stay": bot_config.RETURN_DATE_MAX_STAY,
        
        "price_drop_percentage": bot_config.PRICE_DROP_PERCENTAGE,
        "price_drop_z_score": bot_config.PRICE_DROP_Z_SCORE,
        "max_price_try": bot_config.MAX_PRICE_TRY,
        
        "use_real_time_currency_rates": bot_config.USE_REAL_TIME_CURRENCY_RATES,
        "currency_rates": bot_config.CURRENCY_RATES,
        
        "telegram_enabled": bool(bot_config.TELEGRAM_BOT_TOKEN),
        "telegram_bot_token": bot_config.TELEGRAM_BOT_TOKEN,
        "telegram_chat_id": bot_config.TELEGRAM_CHAT_ID,
        
        # Additional system status data
        "mongodb_enabled": bool(os.environ.get("MONGODB_URI")),
        "city_pairs": [
            {"origin": "IST", "destination": "JFK"},
            {"origin": "IST", "destination": "LHR"},
            {"origin": "JFK", "destination": "LHR"}
        ],
        "departure_dates": ["2025-06-12", "2025-06-15", "2025-07-01"],
        "return_dates": ["2025-06-20", "2025-06-25", "2025-07-10"],
        
        # These would be provided by a real system
        "last_check_time": datetime.now().isoformat(),
        "next_check_time": (datetime.now() + timedelta(minutes=bot_config.SCRAPE_INTERVAL_MINUTES)).isoformat()
    }
    
    return jsonify(config_data)

if __name__ == "__main__":
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)