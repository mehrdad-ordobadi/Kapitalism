import json
from datetime import datetime, timezone
import os
import logging
import logging.config
import connexion
import requests
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS


if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    APP_CONF_FILE = "/app/config/app_config.yml"
    LOG_CONF_FILE = "/app/config/log_config.yml"
else:
    print("In Dev Environment")
    APP_CONF_FILE = "app_config.yml"
    LOG_CONF_FILE = "log_config.yml"

with open(APP_CONF_FILE, "r") as f:
    app_config = yaml.safe_load(f.read())

EVENTSTORE_URL = app_config["eventstore"]["url"]
DATA_FILE = app_config["datastore"]["filename"]
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

with open(LOG_CONF_FILE, "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

logger.info("App Conf File: %s" % APP_CONF_FILE)
logger.info("Log Conf File: %s" % LOG_CONF_FILE)


def process_events():
    """  Process new events from the event store """
    logger.info("This is added for assignment3 - 2nd try - Enterprise course!")
    try:
        with open(DATA_FILE, "r") as f:
            stats = json.load(f)
    except FileNotFoundError:
        logger.warning("Stats file not found. Initializing new stats.")
        stats = {
            "num_products": 0,
            "num_reviews": 0,
            "max_product_price": 0,
            "top_avg_review_rating": 0,
            "last_entry_timestamp": 0,
            "last_updated": 0,
        }

    start_timestamp = stats["last_entry_timestamp"]
    end_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    logger.info(f"Processing events from {start_timestamp} to {end_timestamp}")

    # Fetch and process products
    products = get_events("products", start_timestamp, end_timestamp)
    new_product_count = len(products)
    if new_product_count > 0:
        stats["num_products"] += new_product_count
        stats["max_product_price"] = max(
            stats["max_product_price"], max(float(p["price"]) for p in products)
        )
        last_product_timestamp = max(p["creation_date"] for p in products)
        logger.info(
            f"Processed {new_product_count} new products. New total: {stats['num_products']}"
        )
    else:
        last_product_timestamp = start_timestamp
        logger.info("No new products to process")

    # Fetch and process reviews
    reviews = get_events("reviews", start_timestamp, end_timestamp)
    new_review_count = len(reviews)
    if new_review_count > 0:
        stats["num_reviews"] += new_review_count
        product_ratings = {}
        for review in reviews:
            product_id = review["product_id"]
            if product_id not in product_ratings:
                product_ratings[product_id] = {"total": 0, "count": 0}
            product_ratings[product_id]["total"] += review["rating"]
            product_ratings[product_id]["count"] += 1

        if product_ratings:
            top_avg_rating = round(
                max(r["total"] / r["count"] for r in product_ratings.values()), 2
            )
            stats["top_avg_review_rating"] = max(
                stats["top_avg_review_rating"], float(top_avg_rating)
            )

        last_review_timestamp = max(r["creation_date"] for r in reviews)
        logger.info(
            f"Processed {new_review_count} new reviews. New total: {stats['num_reviews']}"
        )
    else:
        last_review_timestamp = start_timestamp
        logger.info("No new reviews to process")

    # Update last_entry_timestamp only if new events were found
    if new_product_count > 0 or new_review_count > 0:
        stats["last_entry_timestamp"] = max(
            last_product_timestamp, last_review_timestamp
        )
        logger.info(f"Updated last_entry_timestamp to {stats['last_entry_timestamp']}")

    # Always update last_updated
    stats["last_updated"] = end_timestamp
    logger.info(f"Updated last_updated timestamp to {stats['last_updated']}")

    # Write updated stats to file
    with open(DATA_FILE, "w") as f:
        json.dump(stats, f, indent=2)

    return None


def get_events(event_type, start_timestamp, end_timestamp):
    """Fetch events from the data-storage service"""
    url = f"{EVENTSTORE_URL}/{event_type}"
    params = {
        "start_timestamp": int(start_timestamp),
        "end_timestamp": int(end_timestamp),
    }
    logger.info(f"Fetching {event_type} with params: {params}")
    response = requests.get(url, params=params)
    if response.status_code == 200:
        events = response.json()
        logger.info(f"Received {len(events)} {event_type}")
        return events
    else:
        logger.error(
            f"Failed to fetch {event_type} events. Status code: {response.status_code}"
        )
        return []


def get_stats():
    """Get the current stats"""
    logger.info("Received request for current stats")
    try:
        with open(DATA_FILE, "r") as f:
            stats = json.load(f)

        # Convert last_updated to human-readable format
        last_updated = datetime.fromtimestamp(
            stats["last_updated"] / 1000, tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S %Z")

        # Create a new dictionary with the required structure
        formatted_stats = {
            "num_products": stats["num_products"],
            "num_reviews": stats["num_reviews"],
            "max_product_price": stats["max_product_price"],
            "top_avg_review_rating": stats["top_avg_review_rating"],
            "last_updated": last_updated,
        }

        logger.debug(f"Formatted stats: {formatted_stats}")
        logger.info("Request for stats completed")
        return formatted_stats, 200
    except FileNotFoundError:
        logger.error("Statistics do not exist")
        return {"message": "Statistics do not exist"}, 404


def init_scheduler():
    """Initialize the background scheduler to process events"""
    sched = BackgroundScheduler(daemon=True, timezone=timezone.utc)
    sched.add_job(
        process_events, "interval", seconds=app_config["scheduler"]["period_sec"]
    )
    sched.start()


# Create the Connexion application instance
app = connexion.FlaskApp(__name__, specification_dir="./")

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config["CORS_HEADERS"] = "Content-Type"


# Read the openapi.yml file to configure the endpoints
app.add_api(
    "openapi.yml",
    base_path="/processing",
    strict_validation=True,
    validate_responses=True,
)

if __name__ == "__main__":
    logger.info("Starting the application")
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")
