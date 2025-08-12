# Mock Offramp Service

A simple Flask API that simulates USDC to local currency conversion and bank payout functionality.

## API Endpoints

### Health Check
```
GET /health
```
Returns service health status.

### Exchange Rates
```
GET /exchange-rates
```
Returns current mock exchange rates for USDC conversions.

### Process Payout
```
POST /payout
```

Simulates converting USDC from a crypto wallet to local currency and depositing to a bank account.

**Request Body:**
```json
{
  "wallet_id": "mer_offramp_1234567890",
  "wallet_key": "wallet_secret_key_abc123",
  "routing_number": "021000021", 
  "account_number": "1234567890",
  "usdc_amount": "968.55",
  "target_currency": "EUR",
  "reference": "pay_1234567890"
}
```

**Successful Response (200):**
```json
{
  "transaction_id": "tx_a1b2c3d4e5f6",
  "status": "completed",
  "wallet_id": "mer_offramp_1234567890",
  "usdc_amount": "968.55 USDC",
  "final_amount": "832.95 EUR",
  "exchange_rate": 0.86,
  "target_currency": "EUR",
  "bank_details": {
    "routing_number": "021000021",
    "account_number": "***7890",
    "bank_reference": "bnk_ref_x9y8z7w6v5u4"
  },
  "reference": "pay_1234567890",
  "processed_at": "2025-08-12T17:21:09Z",
  "estimated_settlement": "2-3 business days"
}
```

### Simulate Failure
```
POST /payout/simulate-failure
```

Test endpoint to simulate various failure scenarios.

**Request Body:**
```json
{
  "failure_type": "insufficient_funds"
}
```

Available failure types:
- `insufficient_funds` (402)
- `invalid_routing` (400) 
- `compliance_hold` (423)
- `network_error` (503)

## Usage

Run with Docker Compose:
```bash
docker-compose up offramp-service
```

Or run locally:
```bash
cd offramp-service
pip install -r requirements.txt
python app.py
```

Service will be available at `http://localhost:8080`

## Supported Currencies

- EUR (Euro)
- USD (US Dollar)
- GBP (British Pound)
- CAD (Canadian Dollar)

Exchange rates are mocked and include simulated spreads and provider fees.
