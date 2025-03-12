import logging
import logging.config
import json
import os
import time
from threading import Thread
from flask_cors import CORS

import yaml
import connexion
from connexion import NoContent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pykafka import KafkaClient
from pykafka.common import OffsetType

from base import Base
from product import Product
from review import Review

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

# External Logging Configuration
with open(LOG_CONF_FILE, "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

logger.info("App Conf File: %s", APP_CONF_FILE)
logger.info("Log Conf File: %s", LOG_CONF_FILE)

# Get database credentials from environment variables
user = os.environ["MYSQL_USER"]
password = os.environ["MYSQL_PASSWORD"]
hostname = app_config["datastore"]["hostname"]
port = app_config["datastore"]["port"]
db = os.environ["MYSQL_DATABASE"]

logger.info(f"Connecting to database {db} - Host: {hostname} - Port:{port}")

# Create database engine with improved connection pool settings
DB_ENGINE = create_engine(
    f"mysql+pymysql://{user}:{password}@{hostname}:{port}/{db}",
    pool_size=5,
    pool_recycle=3600,
    pool_pre_ping=True,
)

Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def process_add_product(payload):
    """Store product event in the database"""
    session = DB_SESSION()

    try:
        product = Product(
            name=payload["product"]["name"],
            model=payload["product"]["model"],
            build_year=payload["product"]["build_year"],
            price=payload["product"]["price"],
            stock_quantity=payload["product"]["stock_quantity"],
            category=payload["product"].get("category"),
            trace_id=payload["trace_id"],
        )

        session.add(product)
        session.commit()
        logger.debug(
            f"Stored event add_product request with a trace id of {payload['trace_id']}"
        )
    except Exception as e:
        logger.error(f"Error storing product event: {e}")
        session.rollback()
        raise e
    finally:
        session.close()


def process_add_review(payload):
    """Store review event in the database"""
    session = DB_SESSION()

    try:
        review = Review(
            user_uuid=payload["user_uuid"],
            product_id=payload["product_id"],
            rating=payload["rating"],
            review_text=payload["review_text"],
            submission_date=payload["submission_date"],
            title=payload["title"],
            trace_id=payload["trace_id"],
        )

        session.add(review)
        session.commit()
        logger.debug(
            f"Stored event add_review request with a trace id of {payload['trace_id']}"
        )
    except Exception as e:
        logger.error("Error storing review event: %s", e)
        session.rollback()
        raise e
    finally:
        session.close()


def get_products(start_timestamp, end_timestamp):
    """Get products within a date range"""
    session = DB_SESSION()

    try:
        products = (
            session.query(Product)
            .filter(
                Product.creation_date > int(start_timestamp),
                Product.creation_date <= int(end_timestamp),
            )
            .all()
        )

        results = [product.to_dict() for product in products]
        logger.info(
            f"Query for products between {start_timestamp} and {end_timestamp} returns {len(results)} results"
        )

        return results, 200
    except Exception as e:
        logger.error("Error querying products: %s", e)
        return {"message": "Error querying products"}, 500
    finally:
        session.close()


def get_reviews(start_timestamp, end_timestamp):
    """Get reviews within a date range"""
    session = DB_SESSION()

    try:
        reviews = (
            session.query(Review)
            .filter(
                Review.creation_date > int(start_timestamp),
                Review.creation_date <= int(end_timestamp),
            )
            .all()
        )

        results = [review.to_dict() for review in reviews]
        logger.info(
            f"Query for reviews between {start_timestamp} and {end_timestamp} returns {len(results)} results"
        )

        return results, 200
    except Exception as e:
        logger.error("Error querying reviews: %s", e)
        return {"message": "Error querying reviews"}, 500
    finally:
        session.close()


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
    """Process event messages with reconnection logic"""
    while True:
        client, topic, consumer = connect_to_kafka()
        if consumer is None:
            time.sleep(5)
            continue

        try:
            logger.info("Started processing messages")
            for msg in consumer:
                try:
                    msg_str = msg.value.decode("utf-8")
                    msg = json.loads(msg_str)
                    logger.info(f"Message: {msg}")
                    payload = msg["payload"]

                    if msg["type"] == "add-product":
                        logger.info(f"Processing add-product event. Payload: {payload}")
                        process_add_product(payload)
                        logger.info("add-product event processed successfully")
                    elif msg["type"] == "add-review":
                        logger.info(f"Processing add-review event. Payload: {payload}")
                        process_add_review(payload)
                        logger.info("add-review event processed successfully")
                    else:
                        logger.warning(f"Unknown event type received: {msg['type']}")

                except json.JSONDecodeError as e:
                    logger.error(f"JSON decoding error: {e}")
                except KeyError as e:
                    logger.error(f"Missing key in message: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error processing message: {e}")

        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
            try:
                consumer.stop()
                client.close()
            except:
                pass
            time.sleep(5)


app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api(
    "openapi.yml", base_path="/storage", strict_validation=True, validate_responses=True
)
CORS(app.app, resources={r"/*": {"origins": "*"}})

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8090, host="0.0.0.0")
