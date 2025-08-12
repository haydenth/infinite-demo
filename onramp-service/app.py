#!/usr/bin/env python3
"""
Mock Onramp Service - USD Collection & USDC Conversion
Simulates a service that collects USD and converts to USDC
"""

from flask import Flask, request, jsonify, send_from_directory
import uuid
import time
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Mock exchange rates (in production this would come from real rate feeds)
EXCHANGE_RATES = {
    'USD_USDC': 0.99500,  # 1 USD = 0.995 USDC (includes spread and provider fees)
    'EUR_USDC': 1.16000,
    'GBP_USDC': 1.30000,
    'CAD_USDC': 0.80000,
}

@app.route('/', methods=['GET'])
def serve_index():
    """Serve the index.html file"""
    return send_from_directory('.', 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'onramp-service',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

@app.route('/exchange-rates', methods=['GET'])
def get_exchange_rates():
    """Get current exchange rates"""
    return jsonify({
        'rates': EXCHANGE_RATES,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'base_currency': 'USDC'
    }), 200

@app.route('/collect', methods=['POST'])
def process_collection():
    """
    Process USD collection and conversion to USDC
    
    Expected payload:
    {
        "payment_method": "credit_card",
        "card_number": "4111111111111111",
        "card_expiry": "12/25",
        "card_cvv": "123",
        "usd_amount": "1000.00",
        "wallet_address": "0x742d35cc543b6c70800d36d6c24b3c7e1e8c9c5e",
        "reference": "collection_1234567890"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['payment_method', 'usd_amount', 'wallet_address']
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'missing_required_fields',
                'missing_fields': missing_fields
            }), 400
        
        # Extract and validate inputs
        payment_method = data['payment_method']
        usd_amount = float(data['usd_amount'])
        wallet_address = data['wallet_address']
        reference = data.get('reference', f'collection_{int(time.time())}')
        
        # Validate payment method support
        supported_methods = ['credit_card', 'bank_transfer', 'debit_card', 'ach']
        if payment_method not in supported_methods:
            return jsonify({
                'error': 'unsupported_payment_method',
                'supported_methods': supported_methods,
                'requested_method': payment_method
            }), 400
        
        # Mock payment validation (in real system would validate card details)
        if payment_method in ['credit_card', 'debit_card']:
            card_number = data.get('card_number', '')
            if not card_number or len(card_number) < 15:
                return jsonify({
                    'error': 'invalid_card_details',
                    'message': 'Valid card number is required'
                }), 400
        
        # Simulate processing delay
        time.sleep(0.5)  # Mock network/processing time
        
        # Calculate conversion
        exchange_rate = EXCHANGE_RATES['USD_USDC']
        usdc_amount = round(usd_amount * exchange_rate, 2)
        
        # Generate mock transaction IDs
        transaction_id = f'tx_{uuid.uuid4().hex[:12]}'
        payment_reference = f'pay_ref_{uuid.uuid4().hex[:12]}'
        
        logger.info(f"Processing collection: {usd_amount} USD -> {usdc_amount} USDC")
        logger.info(f"Wallet: {wallet_address[:10]}...{wallet_address[-6:]}")
        
        # Mock successful response
        response = {
            'transaction_id': transaction_id,
            'status': 'completed',
            'payment_method': payment_method,
            'usd_amount': f'{usd_amount} USD',
            'usdc_amount': f'{usdc_amount} USDC',
            'exchange_rate': exchange_rate,
            'wallet_address': wallet_address,
            'payment_details': {
                'payment_reference': payment_reference,
                'card_last_four': data.get('card_number', '')[-4:] if payment_method in ['credit_card', 'debit_card'] else None
            },
            'reference': reference,
            'processed_at': datetime.utcnow().isoformat() + 'Z',
            'estimated_settlement': 'immediate'
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        logger.error(f"Invalid amount format: {e}")
        return jsonify({
            'error': 'invalid_amount',
            'message': 'Amount must be a valid number'
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            'error': 'internal_server_error',
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/collect/simulate-failure', methods=['POST'])
def simulate_failure():
    """Endpoint to simulate various failure scenarios for testing"""
    data = request.get_json() or {}
    failure_type = data.get('failure_type', 'insufficient_funds')
    
    time.sleep(0.3)  # Mock processing time
    
    failures = {
        'insufficient_funds': {
            'error': 'insufficient_funds',
            'message': 'Payment method has insufficient funds',
            'status_code': 402
        },
        'invalid_card': {
            'error': 'invalid_payment_details',
            'message': 'Invalid card number or expired card',
            'status_code': 400
        },
        'fraud_detected': {
            'error': 'fraud_detection',
            'message': 'Transaction flagged by fraud detection system',
            'status_code': 423
        },
        'network_error': {
            'error': 'network_timeout',
            'message': 'Payment processor temporarily unavailable',
            'status_code': 503
        }
    }
    
    failure = failures.get(failure_type, failures['insufficient_funds'])
    
    return jsonify({
        'transaction_id': f'failed_{uuid.uuid4().hex[:8]}',
        'status': 'failed',
        **failure,
        'failed_at': datetime.utcnow().isoformat() + 'Z'
    }), failure['status_code']

if __name__ == '__main__':
    logger.info("Starting Mock Onramp Service...")
    logger.info("Available endpoints:")
    logger.info("  GET  / - Serve index.html")
    logger.info("  GET  /health - Health check")
    logger.info("  GET  /exchange-rates - Current exchange rates")
    logger.info("  POST /collect - Process USD collection and convert to USDC")
    logger.info("  POST /collect/simulate-failure - Simulate failure scenarios")
    
    app.run(host='0.0.0.0', port=8081, debug=True)
