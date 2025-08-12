from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models here so they're available when models is imported
from .payment import Payment
from .exchange_rate import ExchangeRate
