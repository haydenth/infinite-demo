from datetime import datetime
from . import db


class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)
    rate = db.Column(db.Numeric(10, 6), nullable=False)
    
    # Rate metadata
    source = db.Column(db.String(50), nullable=False, default='mock')
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on currency pairs
    __table_args__ = (
        db.UniqueConstraint('from_currency', 'to_currency', name='unique_currency_pair'),
    )
    
    def __repr__(self):
        return f'<ExchangeRate {self.from_currency}-{self.to_currency}: {self.rate}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'from_currency': self.from_currency,
            'to_currency': self.to_currency,
            'rate': str(self.rate),
            'source': self.source,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None
        }
