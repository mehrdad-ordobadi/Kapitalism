import time
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger
from base import Base


class Review(Base):
    """ Review """

    __tablename__ = "review"
    trace_id = Column(String(36), nullable=False)

    id = Column(Integer, primary_key=True)
    user_uuid = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey('product.id'), nullable=False)
    rating = Column(Integer, nullable=False)
    review_text = Column(String, nullable=False)
    title = Column(String, nullable=False)
    submission_date = Column(String, nullable=False)
    creation_date = Column(BigInteger, nullable=False)

    def __init__(self, user_uuid, product_id, submission_date, rating, review_text, trace_id, title):
        """ Initializes a review """
        self.user_uuid = user_uuid
        self.product_id = product_id
        self.rating = rating
        self.review_text = review_text
        self.title = title
        self.submission_date = submission_date
        self.creation_date = int(datetime.now(timezone.utc).timestamp() * 1000)
        self.trace_id = trace_id

    def to_dict(self):
        """ Dictionary Representation of a review """
        return {
            'id': self.id,
            'user_uuid': self.user_uuid,
            'product_id': self.product_id,
            'rating': self.rating,
            'review_text': self.review_text,
            'title': self.title,
            'creation_date': self.creation_date,
            'submission_date': self.submission_date,
            'trace_id': self.trace_id
        }