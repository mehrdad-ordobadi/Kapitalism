import connexion
from connexion import NoContent
import logging
import logging.config
import yaml
import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import os
import time
import datetime
from flask_cors import CORS


if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/app/config/app_config.yml"
    log_conf_file = "/app/config/log_config.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_config.yml"
    log_conf_file = "log_config.yml"

with open(app_conf_file, "r") as f:
    app_config = yaml.safe_load(f.read())

os.makedirs(os.path.dirname(app_config["datastore"]["filename"]), exist_ok=True)
if not os.path.exists(app_config["datastore"]["filename"]):
    with open(app_config["datastore"]["filename"], "w") as f:
        json.dump([], f)

# External Logging Configuration
with open(log_conf_file, "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

logger.info(
    "Starting service with anomaly thresholds: Price Max=$%s, Stock Min=%s",
    app_config["anomaly"]["thresholds"]["price_max"],
    app_config["anomaly"]["thresholds"]["stock_min"],
)


def connect_to_kafka():
    """Establish connection to Kafka with retry logic"""
    max_retries = app_config.get("kafka", {}).get("max_retries", 3)
    retry_count = 0

    while retry_count < max_retries:
        try:
            logger.info(
                f"Attempting to connect to Kafka - Attempt {retry_count + 1}/{max_retries}"
            )
            hostname = "%s:%d" % (
                app_config["events"]["hostname"],
                app_config["events"]["port"],
            )
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config["events"]["topic"])]
            consumer = topic.get_simple_consumer(
                consumer_group=b"event_group",
                reset_offset_on_start=False,
                auto_offset_reset=OffsetType.LATEST,
                auto_commit_enable=True,
                auto_commit_interval_ms=1000,
            )
            logger.info("Successfully connected to Kafka")
            return client, topic, consumer
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                sleep_time = app_config.get("kafka", {}).get("retry_delay", 5)
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

    logger.error("Failed to connect to Kafka after all retries")
    return None, None, None


def process_messages():
    """Background thread function to continuously process messages from Kafka"""

    client, topic, consumer = connect_to_kafka()

    if consumer is None:
        logger.error(
            "Failed to establish Kafka connection. Anomaly detection service cannot start."
        )
        return

    logger.info("Kafka consumer has started. Waiting for messages...")
    try:
        for msg in consumer:
            msg_str = msg.value.decode("utf-8")
            # Log raw payload
            logger.info(f"Received event payload: {msg_str}")

            try:
                event = json.loads(msg_str)
                check_anomalies(event)

            except json.JSONDecodeError as e:
                logger.error(f"Error decoding message: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    except Exception as e:
        logger.error(f"Kafka consumer loop error: {e}")
    finally:
        if consumer:
            consumer.commit_offsets()
            consumer.stop()
        if client:
            client.stop()


def check_anomalies(event):
    """Check for price and stock anomalies in the event"""

    price_threshold = app_config["anomaly"]["thresholds"]["price_max"]
    stock_threshold = app_config["anomaly"]["thresholds"]["stock_min"]

    try:
        # Only process product events
        if event["type"] != "add-product":
            return

        # Product data is in event['payload']['product']
        product = event["payload"]["product"]
        user_uuid = event["payload"]["user_uuid"]
        trace_id = event["payload"].get("trace_id", "")

        price = product["price"]
        stock = product["stock_quantity"]

        if price > price_threshold:
            anomaly = {
                "event_id": user_uuid,
                "trace_id": trace_id,
                "event_type": "Product",
                "anomaly_type": "PriceTooHigh",
                "description": f"The value is too high (Price of ${price} is greater than threshold of ${price_threshold})",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_anomaly(anomaly)

        if stock < stock_threshold:
            anomaly = {
                "event_id": user_uuid,
                "trace_id": trace_id,
                "event_type": "Product",
                "anomaly_type": "StockTooLow",
                "description": f"The value is too low (Stock quantity of {stock} is less than threshold of {stock_threshold})",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_anomaly(anomaly)

    except KeyError as e:
        logger.error(f"Missing required field in event: {e}")
    except Exception as e:
        logger.error(f"Error checking anomalies: {e}")


def save_anomaly(anomaly):
    """Save anomaly to JSON file"""
    try:
        try:
            with open(app_config["datastore"]["filename"], "r") as f:
                anomalies = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            anomalies = []

        anomalies.append(anomaly)

        with open(app_config["datastore"]["filename"], "w") as f:
            json.dump(anomalies, f, indent=2)
        logger.info(f"Added anomaly to database: {json.dumps(anomaly)}")
    except Exception as e:
        logger.error(f"Error saving anomaly to file: {e}")


def get_anomalies(anomaly_type=None):
    """Get anomalies endpoint implementation"""
    logger.info(f"Received GET request for anomalies with type: {anomaly_type}")

    valid_types = ["PriceTooHigh", "StockTooLow"]
    if anomaly_type and anomaly_type not in valid_types:
        logger.info(f"Invalid anomaly type requested: {anomaly_type}")
        return {"message": f"Invalid anomaly type. Must be one of {valid_types}"}, 400
    try:
        with open(app_config["datastore"]["filename"], "r") as f:
            anomalies = json.load(f)
    except FileNotFoundError:
        logger.info("No anomalies found - file does not exist")
        return {"message": "No anomalies found"}, 404

    if anomaly_type:
        anomalies = [a for a in anomalies if a["anomaly_type"] == anomaly_type]

    if not anomalies:
        logger.info(f"No anomalies found for type: {anomaly_type}")
        return {"message": f"No anomalies found for type {anomaly_type}"}, 404

    # Sort by timestamp descending (newest first)
    anomalies.sort(key=lambda x: x["timestamp"], reverse=True)

    logger.info(f"Returning {len(anomalies)} anomalies of type {anomaly_type}")
    return anomalies, 200


# Create and start the Flask application
app = connexion.FlaskApp(__name__, specification_dir=".")
app.add_api(
    "openapi.yaml",
    base_path="/anomaly",
    strict_validation=True,
    validate_responses=True,
)

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config["CORS_HEADERS"] = "Content-Type"

if __name__ == "__main__":
    # Start Kafka consumer in a background thread
    kafka_thread = Thread(target=process_messages, daemon=True)
    kafka_thread.start()

    app.run(port=8120, host="0.0.0.0")
