import logging
import logging.config
import uuid
import json
import os
import datetime
import time

import connexion
from connexion import NoContent
from pykafka import KafkaClient
import yaml
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

# External Logging Configuration
with open(log_conf_file, "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

# Global variables for Kafka client and producer
KAFKA_CLIENT = None
KAFKA_PRODUCER = None
KAFKA_TOPIC = None


def connect_to_kafka():
    """Establish connection to Kafka with retry logic"""
    global KAFKA_CLIENT, KAFKA_PRODUCER, KAFKA_TOPIC

    max_retries = app_config["kafka"]["max_retries"]
    retry_count = 0

    while retry_count < max_retries:
        try:
            logger.info(
                f"Attempting to connect to Kafka - Attempt {retry_count + 1}/{max_retries}"
            )
            hostname = (
                f"{app_config['events']['hostname']}:{app_config['events']['port']}"
            )
            KAFKA_CLIENT = KafkaClient(hosts=hostname)
            KAFKA_TOPIC = KAFKA_CLIENT.topics[str.encode(
                app_config["events"]["topic"])]
            KAFKA_PRODUCER = KAFKA_TOPIC.get_sync_producer()
            logger.info("Successfully connected to Kafka")
            logger.info("This is added for assignment3 - Enterprise course!")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                sleep_time = app_config["kafka"]["retry_delay"]
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

    logger.error("Failed to connect to Kafka after all retries")
    return False


def check_kafka_connection():
    """Check if Kafka connection is still alive"""
    try:
        # Try to list topics as a connection test
        KAFKA_CLIENT.topics
        return True
    except Exception:
        logger.error("Kafka connection check failed")
        return False


def ensure_kafka_connection():
    """Ensure Kafka connection is active, reconnect if needed"""
    if not check_kafka_connection():
        logger.info("Kafka connection lost, attempting to reconnect...")
        return connect_to_kafka()
    return True


def produce_message(msg_str):
    """Produce message with circuit breaker pattern"""
    max_retries = app_config["kafka"]["max_retries"]

    for attempt in range(max_retries):
        try:
            KAFKA_PRODUCER.produce(msg_str.encode("utf-8"))
            return True
        except Exception as error:
            logger.error(f"Failed to produce message: {str(error)}")
            if not ensure_kafka_connection():
                continue
            if attempt == max_retries - 1:
                raise error
            time.sleep(app_config["kafka"]["retry_delay"])
    return False


def add_product(body):
    """Add a product to the data storage"""
    trace_id = str(uuid.uuid4())
    body["trace_id"] = trace_id
    logger.info(
        f"Received event add_product request with a trace id of {trace_id}")

    msg = {
        "type": "add-product",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body,
    }
    msg_str = json.dumps(msg)

    if produce_message(msg_str):
        logger.info(
            f"Returned event add_product response (Id: {trace_id}) with status {201}"
        )
        return NoContent, 201
    else:
        logger.error(
            f"Failed to produce message for add_product (Id: {trace_id})")
        return NoContent, 500


def add_review(body):
    """ Add a review of a product to the data storage """
    trace_id = str(uuid.uuid4())
    body["trace_id"] = trace_id
    logger.info(
        f"Received event add_review request with a trace id of {trace_id}")

    msg = {
        "type": "add-review",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body,
    }
    msg_str = json.dumps(msg)

    if produce_message(msg_str):
        logger.info(
            f"Returned event add_review response (Id: {trace_id}) with status {201}"
        )
        return NoContent, 201
    else:
        logger.error(
            f"Failed to produce message for add_review (Id: {trace_id})")
        return NoContent, 500


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)
CORS(app.app, resources={r"/*": {"origins": "*"}})

if __name__ == "__main__":
    # Connect to Kafka before starting the Flask app
    if connect_to_kafka():
        app.run(port=8080, host="0.0.0.0")
    else:
        logger.error(
            "Failed to start application due to Kafka connection failure")
