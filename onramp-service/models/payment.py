from datetime import datetime
from . import db


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    reference = db.Column(db.String(100), nullable=False, index=True)
    
    # Payment method details
    payment_method = db.Column(db.String(20), nullable=False)
    card_last_four = db.Column(db.String(4), nullable=True)
    payment_reference = db.Column(db.String(50), nullable=True)
    
    # Amount details
    usd_amount = db.Column(db.Numeric(12, 2), nullable=False)
    usdc_amount = db.Column(db.Numeric(12, 6), nullable=False)
    exchange_rate = db.Column(db.Numeric(8, 6), nullable=False)
    
    # Wallet and status
    wallet_address = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    
    # Error handling
    error_code = db.Column(db.String(50), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.transaction_id}: {self.usd_amount} USD -> {self.usdc_amount} USDC>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'reference': self.reference,
            'payment_method': self.payment_method,
            'card_last_four': self.card_last_four,
            'payment_reference': self.payment_reference,
            'usd_amount': str(self.usd_amount),
            'usdc_amount': str(self.usdc_amount),
            'exchange_rate': str(self.exchange_rate),
            'wallet_address': self.wallet_address,
            'status': self.status,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'processed_at': self.processed_at.isoformat() + 'Z' if self.processed_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None
        }
