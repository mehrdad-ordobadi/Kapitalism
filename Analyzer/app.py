import json
import logging
import logging.config
import os
import yaml
import connexion
from pykafka import KafkaClient
from pykafka.exceptions import KafkaException
from flask_cors import CORS


if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    APP_CONF_FILE = "/app/config/app_config.yml"
    LOG_CONF_FILE = "/app/config/log_config.yml"
else:
    print("In Dev Environment")
    APP_CONF_FILE = "app_config.yml"
    LOG_CONF_FILE = "log_config.yml"

with open(APP_CONF_FILE, "r", encoding="utf-8") as f:
    app_config = yaml.safe_load(f.read())

# External Logging Configuration
with open(LOG_CONF_FILE, "r", encoding="utf-8") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

logger.info("App Conf File: %s" % APP_CONF_FILE)
logger.info("Log Conf File: %s" % LOG_CONF_FILE)


def get_product(index):
    """Get Product Event from History"""
    return get_event_by_index("add-product", index)


def get_review(index):
    """Get Review Event from History"""
    return get_event_by_index("add-review", index)


def get_event_by_index(event_type, index):
    """Generic function to get an event by index"""
    hostname = "%s:%d" % (
        app_config["events"]["hostname"],
        app_config["events"]["port"],
    )
    try:
        client = KafkaClient(hosts=hostname)
        topic = client.topics[str.encode(app_config["events"]["topic"])]
        consumer = topic.get_simple_consumer(
            reset_offset_on_start=True, consumer_timeout_ms=1000
        )
        logger.info(f"Retrieving {event_type} at index {index}")

        event_count = 0
        for msg in consumer:
            msg_str = msg.value.decode("utf-8")
            msg = json.loads(msg_str)
            if msg["type"] == event_type:
                if event_count == index:
                    logger.info(f"Found {event_type} at index {index}")
                    return msg["payload"], 200
                event_count += 1

        logger.error(f"Could not find {event_type} at index {index}")
        return {"message": "Not Found"}, 404

    except KafkaException as ke:
        logger.error(f"Kafka Error: {str(ke)}")
        return {"message": "Kafka Error"}, 500
    except json.JSONDecodeError as je:
        logger.error(f"JSON Decode Error: {str(je)}")
        return {"message": "JSON Decode Error"}, 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"message": "Internal Server Error"}, 500


def get_stats():
    """Get Event Stats"""
    hostname = "%s:%d" % (
        app_config["events"]["hostname"],
        app_config["events"]["port"],
    )
    try:
        client = KafkaClient(hosts=hostname)
        topic = client.topics[str.encode(app_config["events"]["topic"])]
        consumer = topic.get_simple_consumer(
            reset_offset_on_start=True, consumer_timeout_ms=1000
        )
        logger.info("Retrieving stats")

        num_products = 0
        num_reviews = 0
        for msg in consumer:
            msg_str = msg.value.decode("utf-8")
            msg = json.loads(msg_str)
            if msg["type"] == "add-product":
                num_products += 1
            elif msg["type"] == "add-review":
                num_reviews += 1
        logger.info("Stats retrieved")
        return {"num_products": num_products, "num_reviews": num_reviews}, 200

    except KafkaException as ke:
        logger.error(f"Kafka Error: {str(ke)}")
        return {"message": "Kafka Error"}, 500
    except json.JSONDecodeError as je:
        logger.error(f"JSON Decode Error: {str(je)}")
        return {"message": "JSON Decode Error"}, 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {"message": "Internal Server Error"}, 500


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api(
    "openapi.yml",
    base_path="/analyzer",
    strict_validation=True,
    validate_responses=True,
)

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config["CORS_HEADERS"] = "Content-Type"

if __name__ == "__main__":
    app.run(port=8110, host="0.0.0.0")
