import time
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, BigInteger
from base import Base


class Product(Base):
    """ Product """

    __tablename__ = "product"
    trace_id = Column(String(36), nullable=False)
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250), nullable=False)
    model = Column(String(250), nullable=False)
    build_year = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String(250))
    stock_quantity = Column(Integer, nullable=False)
    creation_date = Column(BigInteger, nullable=False)

    def __init__(self, name, model, build_year, price, stock_quantity, trace_id, category=None):
        """ Initializes a product """
        self.name = name
        self.model = model
        self.build_year = build_year
        self.price = price
        self.stock_quantity = stock_quantity
        self.category = category
        self.trace_id = trace_id
        self.creation_date = int(datetime.now(timezone.utc).timestamp() * 1000)

    def to_dict(self):
        """ Dictionary Representation of a product """
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'build_year': self.build_year,
            'price': float(self.price),
            'category': self.category,
            'stock_quantity': self.stock_quantity,
            'trace_id': self.trace_id,
            'creation_date': self.creation_date
        }