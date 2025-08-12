#!/usr/bin/env python3
"""
Mock Offramp Service - USDC to EUR Conversion & Payout
Simulates a service that converts USDC to EUR and deposits to bank accounts
"""

from flask import Flask, request, jsonify
import uuid
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Mock exchange rates (in production this would come from real rate feeds)
EXCHANGE_RATES = {
    'USDC_EUR': 0.86000,  # 1 USDC = 0.86 EUR (includes spread and provider fees)
    'USDC_USD': 1.00000,
    'USDC_GBP': 0.77000,
    'USDC_CAD': 1.25000,
}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'offramp-service',
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

@app.route('/payout', methods=['POST'])
def process_payout():
    """
    Process USDC to local currency conversion and bank payout
    
    Expected payload:
    {
        "wallet_id": "mer_offramp_1234567890",
        "wallet_key": "wallet_secret_key_abc123",
        "routing_number": "021000021", 
        "account_number": "1234567890",
        "usdc_amount": "968.55",
        "target_currency": "EUR",
        "reference": "pay_1234567890"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['wallet_id', 'wallet_key', 'routing_number', 
                          'account_number', 'usdc_amount', 'target_currency']
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'missing_required_fields',
                'missing_fields': missing_fields
            }), 400
        
        # Extract and validate inputs
        wallet_id = data['wallet_id']
        wallet_key = data['wallet_key']
        routing_number = data['routing_number']
        account_number = data['account_number']
        usdc_amount = float(data['usdc_amount'])
        target_currency = data['target_currency'].upper()
        reference = data.get('reference', f'payout_{int(time.time())}')
        
        # Validate currency support
        rate_key = f'USDC_{target_currency}'
        if rate_key not in EXCHANGE_RATES:
            return jsonify({
                'error': 'unsupported_currency',
                'supported_currencies': list([key.split('_')[1] for key in EXCHANGE_RATES.keys()]),
                'requested_currency': target_currency
            }), 400
        
        # Mock wallet authentication (in real system would verify wallet_key)
        if not wallet_key or len(wallet_key) < 10:
            return jsonify({
                'error': 'invalid_wallet_credentials',
                'message': 'Wallet key must be at least 10 characters'
            }), 401
        
        # Simulate processing delay
        time.sleep(0.5)  # Mock network/processing time
        
        # Calculate conversion
        exchange_rate = EXCHANGE_RATES[rate_key]
        final_amount = round(usdc_amount * exchange_rate, 2)
        
        # Generate mock transaction IDs
        transaction_id = f'tx_{uuid.uuid4().hex[:12]}'
        bank_reference = f'bnk_ref_{uuid.uuid4().hex[:12]}'
        
        logger.info(f"Processing payout: {usdc_amount} USDC -> {final_amount} {target_currency}")
        logger.info(f"Wallet: {wallet_id}, Account: ***{account_number[-4:]}")
        
        # Mock successful response
        response = {
            'transaction_id': transaction_id,
            'status': 'completed',
            'wallet_id': wallet_id,
            'usdc_amount': f'{usdc_amount} USDC',
            'final_amount': f'{final_amount} {target_currency}',
            'exchange_rate': exchange_rate,
            'target_currency': target_currency,
            'bank_details': {
                'routing_number': routing_number,
                'account_number': f'***{account_number[-4:]}',  # Masked for security
                'bank_reference': bank_reference
            },
            'reference': reference,
            'processed_at': datetime.utcnow().isoformat() + 'Z',
            'estimated_settlement': '2-3 business days'
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

@app.route('/payout/simulate-failure', methods=['POST'])
def simulate_failure():
    """Endpoint to simulate various failure scenarios for testing"""
    data = request.get_json() or {}
    failure_type = data.get('failure_type', 'insufficient_funds')
    
    time.sleep(0.3)  # Mock processing time
    
    failures = {
        'insufficient_funds': {
            'error': 'insufficient_funds',
            'message': 'Wallet does not have sufficient USDC balance',
            'status_code': 402
        },
        'invalid_routing': {
            'error': 'invalid_bank_details',
            'message': 'Invalid routing number or account number',
            'status_code': 400
        },
        'compliance_hold': {
            'error': 'compliance_review',
            'message': 'Transaction flagged for compliance review',
            'status_code': 423
        },
        'network_error': {
            'error': 'network_timeout',
            'message': 'Banking network temporarily unavailable',
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
    logger.info("Starting Mock Offramp Service...")
    logger.info("Available endpoints:")
    logger.info("  GET  /health - Health check")
    logger.info("  GET  /exchange-rates - Current exchange rates")
    logger.info("  POST /payout - Process USDC to local currency payout")
    logger.info("  POST /payout/simulate-failure - Simulate failure scenarios")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
