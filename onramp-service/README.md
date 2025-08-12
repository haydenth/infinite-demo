# Mock Onramp Service

A mock USD collection and USDC conversion service for testing payment flows.

## Features

- **USD Collection**: Accepts various payment methods (credit card, bank transfer, ACH)
- **USDC Conversion**: Converts collected USD to USDC using mock exchange rates
- **Payment Validation**: Basic validation of payment details
- **Failure Simulation**: Endpoint to simulate various failure scenarios
- **Web Interface**: Serves an index.html page at the root endpoint

## API Endpoints

### GET `/`
Serves the index.html file.

### GET `/health`
Health check endpoint that returns service status.

### GET `/exchange-rates`
Returns current exchange rates for supported currency pairs.

### POST `/collect`
Process USD collection and conversion to USDC.

**Request Body:**
```json
{
    "payment_method": "credit_card",
    "card_number": "4111111111111111",
    "card_expiry": "12/25",
    "card_cvv": "123",
    "usd_amount": "1000.00",
    "wallet_address": "0x742d35cc543b6c70800d36d6c24b3c7e1e8c9c5e",
    "reference": "collection_1234567890"
}
```

### POST `/collect/simulate-failure`
Simulate various failure scenarios for testing.

**Request Body:**
```json
{
    "failure_type": "insufficient_funds"
}
```

Supported failure types:
- `insufficient_funds`: Payment method has insufficient funds
- `invalid_card`: Invalid card details
- `fraud_detected`: Transaction flagged by fraud detection
- `network_error`: Payment processor unavailable

## Running the Service

The service runs on port 8081 and is designed to be used with Docker Compose.

```bash
docker-compose up onramp-service
```

## Exchange Rates

Current mock rates (includes fees and spread):
- USD → USDC: 0.995 (0.5% fee)
- EUR → USDC: 1.16
- GBP → USDC: 1.30
- CAD → USDC: 0.80
