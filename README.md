## Double-Entry Accounting System + Fee Engine

### Core Principles
1. **Every transaction must balance** - Total debits = Total credits
2. **Currency conversions are explicit transactions** with clear exchange rates
3. **Fees are collected atomically** with the triggering event, not pre-assessed
4. **Clear separation** between operational accounts and fee revenue accounts
5. **Transaction state management** with proper rollback capability

### Account Structure

#### Operational Accounts
- `PAYER_BANK_ACCOUNT` - Payer's USD bank account
- `INFINITE_USD_BANK` - Our USD operating account (receives from Stripe)
- `INFINITE_CUSTODY_USDC` - Our USDC wallet for cross-border transfers
- `MERCHANT_OFFRAMP_USDC` - Merchant-specific USDC account for offramp
- `MERCHANT_BANK_ACCOUNT` - Merchant's local currency bank account
- `STRIPE_CLEARING` - Stripe's clearing account
- `STRIPE_FEE_EXPENSE` - Stripe processing fees expense

#### Fee Revenue Accounts
- `FEE_REVENUE_USD` - USD fees collected
- `FEE_REVENUE_USDC` - USDC fees collected

#### Suspense/Working Accounts
- `CURRENCY_EXCHANGE_SUSPENSE` - Temporary account for conversion calculations
- `TRANSACTION_IN_PROGRESS` - Holds funds during multi-step processes

### Transaction Flow with Proper Double-Entry Accounting

#### Event 1: Invoice Payment ($1000 USD + $5 Fee)
**Fee: $5 flat fee charged to payer on top of invoice amount**
**Stripe Fee: $29.45 ($0.30 + 2.9% of $1005) - owed to Stripe**

**⚠️ Compliance Note**: This flow violates Stripe's Terms of Service since we're not the merchant of record for the underlying transaction. In production, this would require:
- Proper merchant onboarding and KYC
- Stripe Connect or marketplace setup
- Alternative payment processors designed for this use case
- Direct bank integration bypassing card networks entirely
*This is a coding demonstration only - real implementation would need compliant payment collection!!*

**Journal Entry Format:**
```
Dr STRIPE_CLEARING          1,005.00 USD   (asset ↑, payment received from payer)
    Cr EXTERNAL_PAYER             1,005.00 USD   (off-books, payer's payment)

Dr STRIPE_FEE_EXPENSE          29.45 USD   (expense ↑, Stripe processing fees)
Dr INFINITE_USD_BANK          970.55 USD   (asset ↑, net funds to our account)
    Cr FEE_REVENUE_USD            5.00 USD   (revenue ↑, our payment processing fee)
    Cr STRIPE_CLEARING        1,005.00 USD   (asset ↓, funds cleared from Stripe)
```

**Transaction Table Format:**
| txn_id | account                | debit_amount | credit_amount | currency | description |
|--------|------------------------|--------------|---------------|----------|-------------|
| tx_001 | STRIPE_CLEARING        | 1005.00      | 0.00          | USD      | Payment received from payer |
| tx_001 | STRIPE_FEE_EXPENSE     | 29.45        | 0.00          | USD      | Stripe processing fees |
| tx_001 | INFINITE_USD_BANK      | 970.55       | 0.00          | USD      | Net funds to our account |
| tx_001 | FEE_REVENUE_USD        | 0.00         | 5.00          | USD      | Our payment processing fee |
| tx_001 | STRIPE_CLEARING        | 0.00         | 1005.00       | USD      | Funds cleared from Stripe |

**Balance Check**: 1005 = 29.45 + 5 + 970.55 ✓

#### Event 2: USD to USDC Conversion
**Fee: $1.00 (0.1% of invoice amount) assessed to merchant**
**Exchange Rate: 1 USD = 1 USDC**

**Journal Entry Format:**
```
Dr INFINITE_CUSTODY_USDC      969.55 USDC  (asset ↑, USDC acquired from USD conversion)
    Cr FEE_REVENUE_USD            1.00 USD   (revenue ↑, onramp fee)
    Cr INFINITE_USD_BANK        970.55 USD   (asset ↓, USD converted + fee collected)
```

**Transaction Table Format:**
| txn_id | account                | debit_amount | credit_amount | currency | description |
|--------|------------------------|--------------|---------------|----------|-------------|
| tx_002 | INFINITE_CUSTODY_USDC  | 969.55       | 0.00          | USDC     | USDC acquired from USD conversion |
| tx_002 | FEE_REVENUE_USD        | 0.00         | 1.00          | USD      | Onramp fee |
| tx_002 | INFINITE_USD_BANK      | 0.00         | 970.55        | USD      | USD converted + fee collected |

**Balance Check**: 970.55 = 1.00 + 969.55 ✓

#### Event 3: Transfer to Merchant Offramp Account
**Fee: $1 USDC transfer fee assessed to merchant**
**Prepare merchant-specific USDC for offramp**

**Journal Entry Format:**
```
Dr MERCHANT_OFFRAMP_USDC      968.55 USDC  (asset ↑, USDC allocated to merchant)
    Cr FEE_REVENUE_USDC          1.00 USDC  (revenue ↑, transfer fee)
    Cr INFINITE_CUSTODY_USDC    969.55 USDC  (asset ↓, USDC transferred + fee)
```

**Transaction Table Format:**
| txn_id | account                  | debit_amount | credit_amount | currency | description |
|--------|--------------------------|--------------|---------------|----------|-------------|
| tx_003 | MERCHANT_OFFRAMP_USDC    | 968.55       | 0.00          | USDC     | USDC allocated to merchant |
| tx_003 | FEE_REVENUE_USDC         | 0.00         | 1.00          | USDC     | Transfer fee |
| tx_003 | INFINITE_CUSTODY_USDC    | 0.00         | 969.55        | USDC     | USDC transferred + fee |

**Balance Check**: 969.55 = 1 + 968.55 ✓

#### Event 4: USDC to EUR Conversion & Payout
**Exchange Rate: 1 USDC = 0.86 EUR as of 8/11/2025 (including theoretical offramp provider fees and spread)**
**Net to merchant: 968.55 USDC → €832.95**

**Design Notes**: 
1. **Offramp Provider Fees**: Real offramp providers (Circle, Fireblocks, etc.) charge additional fees beyond the exchange rate spread, but these are provider-specific and excluded from this demo for simplicity. In theory, you'd want to track that and have a line item for that.
2. **No Additional Platform Fees**: I've intentionally chosen not to charge additional fees at the offramp stage to maintain accounting simplicity and keep all our platform fees denominated in USD/USDC rather than dealing with multi-currency fee revenue tracking.

**Journal Entry Format:**
```
Dr MERCHANT_BANK_ACCOUNT      832.95 EUR   (asset ↑, EUR received from offramp)
    Cr MERCHANT_OFFRAMP_USDC    968.55 USDC  (asset ↓, USDC offramped to EUR)
```

**Transaction Table Format:**
| txn_id | account                  | debit_amount | credit_amount | currency | description |
|--------|--------------------------|--------------|---------------|----------|-------------|
| tx_004 | MERCHANT_BANK_ACCOUNT    | 832.95       | 0.00          | EUR      | EUR received from offramp |
| tx_004 | MERCHANT_OFFRAMP_USDC    | 0.00         | 968.55        | USDC     | USDC offramped to EUR |

**Balance Check**: 968.55 USDC → 832.95 EUR at rate ✓

### Final Account Balances

```
| Account                     | Currency | Balance  | Notes                           |
|----------------------------|----------|----------|---------------------------------|
| PAYER_BANK_ACCOUNT         | USD      | -1005.00 | Paid $1000 invoice + $5 fee     |
| MERCHANT_BANK_ACCOUNT      | EUR      | +832.95  | Received €832.95 payout         |
| FEE_REVENUE_USD            | USD      | +6.00    | Revenue: $5 payment + $1 onramp |
| FEE_REVENUE_USDC           | USDC     | +1.00    | Revenue: $1 USDC transfer fee   |
| STRIPE_FEE_EXPENSE         | USD      | +29.45   | Stripe processing fee expense   |
| STRIPE_CLEARING            | USD      | 0.00     | Cleared                         |
| INFINITE_USD_BANK          | USD      | 0.00     | Cleared                         |
| INFINITE_CUSTODY_USDC      | USDC     | 0.00     | Cleared                         |
| MERCHANT_OFFRAMP_USDC      | USDC     | 0.00     | Cleared                         |
```

## Payment Events Index

The following events are emitted during the cross-border payment flow, tied directly to our transaction stages:

### Transaction-Based Events

Each event corresponds to a completed transaction in our double-entry accounting system:

#### **Event 1: `payment.collected`**
- **Trigger**: Completion of Transaction `tx_001` (Invoice Payment)
- **Payload**: 
  ```json
  {
    "payment_id": "pay_1234567890",
    "transaction_id": "tx_001",
    "gross_amount": "1005.00 USD",
    "stripe_fee": "29.45 USD", 
    "our_fee": "5.00 USD",
    "net_received": "970.55 USD",
    "stripe_transaction_id": "pi_1234567890"
  }
  ```
- **Status**: `collected`

#### **Event 2: `onramp.converted`** 
- **Trigger**: Completion of Transaction `tx_002` (USD to USDC Conversion)
- **Payload**:
  ```json
  {
    "payment_id": "pay_1234567890", 
    "transaction_id": "tx_002",
    "usd_amount": "970.55 USD",
    "usdc_received": "969.55 USDC",
    "exchange_rate": "1.00000",
    "onramp_fee": "1.00 USD"
  }
  ```
- **Status**: `converted`

#### **Event 3: `custody.transferred`**
- **Trigger**: Completion of Transaction `tx_003` (Transfer to Merchant Offramp Account)
- **Payload**:
  ```json
  {
    "payment_id": "pay_1234567890",
    "transaction_id": "tx_003", 
    "usdc_transferred": "969.55 USDC",
    "transfer_fee": "1.00 USDC",
    "net_to_offramp": "968.55 USDC",
    "merchant_offramp_account": "mer_offramp_1234567890"
  }
  ```
- **Status**: `transferred`

#### **Event 4: `payout.completed`**
- **Trigger**: Completion of Transaction `tx_004` (USDC to EUR Conversion & Payout)
- **Payload**:
  ```json
  {
    "payment_id": "pay_1234567890",
    "transaction_id": "tx_004",
    "usdc_amount": "968.55 USDC",
    "final_amount": "832.95 EUR", 
    "exchange_rate": "0.86000",
    "merchant_bank_reference": "bnk_ref_1234567890"
  }
  ```
- **Status**: `completed`

#### **Event 5: `payment.completed`**
- **Trigger**: All transactions completed successfully
- **Payload**: Complete payment summary
  ```json
  {
    "payment_id": "pay_1234567890",
    "original_amount": "1000.00 USD",
    "total_fees_collected": "7.00 USD + 1.00 USDC",
    "final_payout": "832.95 EUR",
    "completion_time": "2025-08-12T17:02:45Z",
    "transaction_ids": ["tx_001", "tx_002", "tx_003", "tx_004"]
  }
  ```
- **Status**: `completed`

### Event Payload Schema

Each event follows this standard structure:
```json
{
  "event_id": "evt_1234567890",
  "event_type": "payment.collection.succeeded",
  "created_at": "2025-08-12T16:58:45Z",
  "payment_id": "pay_1234567890",
  "merchant_id": "mer_1234567890",
  "data": {
    // Event-specific payload data
  },
  "metadata": {
    "idempotency_key": "unique_key_123",
    "source_ip": "192.168.1.1",
    "user_agent": "API Client v1.0"
  }
}
```

### Webhook Configuration

Merchants can subscribe to specific events via webhook endpoints:

```json
{
  "webhook_url": "https://merchant.example.com/webhooks/infinite",
  "events": [
    "payment.collected",
    "onramp.converted", 
    "custody.transferred",
    "payout.completed",
    "payment.completed"
  ],
  "secret": "whsec_1234567890abcdef"
}
```

## Regulatory Notes
- **Co-mingling of Funds**: The custody wallet (`CUSTODY_WALLET`) will hold funds from multiple merchants and payers. This is a serious risk for regulatory compliance, especially in terms of KYC/AML regulations. In a production system, it would be advisable to have separate custody wallets for each merchant or recipient bank to mitigate this risk.
- **KYC/AML Compliance**: Ensure that both the merchant and payer are compliant with KYC/AML regulations. This existing flow is a compliance nightmare!
- **Transaction Limits**: Implement transaction limits to prevent money laundering and fraud. This is a must for the offramp service.
- **Transaction Monitoring**: Monitor transactions for suspicious activity and report any suspicious transactions to the relevant authorities. This is a must for the offramp service.

