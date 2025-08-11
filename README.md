
## Parties and Wallets

- **Merchant**: The user who initiates the invoice request and is the recipient of the payment. They have a native currency that may not be in USD. This user has the following accounts:
  - **Bank Account (`MERCHANT_BANK_ACCOUNT`)**: A non-US bank account attached to payment credentials (visible to us) that will receive offramped funds
  - **Merchant Payable (`MERCHANT_PAYABLE`)**: A payable account that holds the amount due to the merchant in their native currency. 
- **Payer**: The user who receives the invoice and makes the payment. They will pay in USD, but the merchant may want to receive the payment in a different currency.
  - **Bank Account (`PAYER_BANK_ACCOUNT`)**: A US bank account attached to payment credentials (invisible to us) used to onramp funds
  - **Payer Receivable (`PAYER_RECEIVABLE`)**: A receivable account that holds the amount due from the payer in USD.
- **Stripe Payment Processing**: The service that handles the payment transactions: Stripe
- **Infinite Custody Bank Account (`INFINITE_BANK_ACCOUNT`)**: A US bank account that holds USD and is used to facilitate the transfer of funds between the merchant and payer. This account is managed by us and is used to hold custody of funds during transfer.
- **Infinite Fee Revenue Bank Account (`INFINITE_FEE_BANK_ACCOUNT`)**: A US bank account that holds fees collected from the payer and merchant. 
- **Infinite Custody Wallet (`CUSTODY_WALLET`)**: A wallet that holds the stablecoins (USDC) and is used to facilitate the transfer of funds between the merchant and payer. This wallet is managed by us and is used to hold custody of funds during transfer. Practically, it might make sense to have a separate custody wallet for each merchant (privacy issues) or with each receipient bank (e.g. one for EUR, one for GBP, etc.). This wallet is used to hold the stablecoins during the transfer process.
- **Stripe Clearing Account (`STRIPE_CLEARING_ACCOUNT`)**: A Stripe account that holds the funds during the payment process. This account is used to hold the funds until they are transferred to the `INFINITE_BANK_ACCOUNT`.
- **Mocked Off-ramp Provider (`OFFRAMP_CLEARING_ACCOUNT`)**: A mocked off-ramp provider that simulates the process of converting USDC to the merchant's native currency and sending it to their bank account. In a real-world scenario, this would involve using a service like Fireblocks, Circle, or similar to handle the conversion and transfer.


## Payment Events 

### 1) Invoice Creation (`invoice_create`)
The merchant initiates an invoice request that includes the following. All invoice currency is USD, even if the Merchant is in a different currency. The invoice request is sent to the payer via email or other communication channels. The invoice request includes the following details:

```json
{
  "amount": 1000,
  "currency": "USD",
  "description": "Payment for Work Order #12345",
  "customer_id": "cust_67890"
}
```

### 2) Invoice Payment (`invoice_payment`)
The user sends the invoice to the payer via email or other communication channels. The payer receives a link to view and pay the invoice.  The payer clicks the link in the invoice and is directed to a secure payment page. The payer selects their preferred payment method (credit card, bank transfer, etc.) and enters the required payment details. This will go through Stripe and funds will be deposited into the `INFINITE_BANK_ACCOUNT`. Note: I think this is probably in violation of Stripe's TOS since we're not the actual merchant of record here, so there are some compliance issues to work through for this in production.

### 3) Payment Onramp (USD) (`payment_onramp`)
At least in theory (ignoring settlement delays and MTL compliance) we'll have our US bank account funded with USD. At this point, we need to go out an make a purchase of USDC. To keep it simple this is done by making a purchase of USDC on a centralized exchange. It is then held in the custody wallet (`CUSTODY_WALLET`) where it is comingled with other funds (note: this is a bad idea but we're trying to get a simple demo here, not a final production product). 

We may also need to assess fees at this point as well. In fact, this is probably the final place where we may wish to assess fees since we can keep them in our `INFINITE_BANK_ACCOUNT` and not have to worry about them being in the custody wallet.

### 4) Stablecoin Offramp (Native Currency) (`stablecoin_offramp`)
At this point, the merchant has a bank account in their native currency `MERCHANT_BANK_ACCOUNT`. We need to offramp the USDC to the merchant's bank account. This is done by using a mocked offramp service that simulates the process of converting USDC to the merchant's native currency and sending it to their bank account. In a real-world scenario, this would involve using a service like Fireblocks, Circle, or similar to handle the conversion and transfer. This is probably the hardest and riskiest part of the entire exchange.

## Fee Engine
We need to have a pretty flexibile fee engine that can assess fees at different points along the process. The engine needs to support:

- Flat fees (e.g. $1.00 per transaction)
- Percentage fees (e.g. 1.5% of the transaction amount)
- Hybrid fees (e.g. $0.30 + 2.9% of the transaction amount)
- Tiered fees (in a future version)

And we need to be able to assess these fees against either the payer or the merchant.
- `invoice_payment`: Assess fees against the payer. Example: $0.30 + 2.9% of the transaction amount
- `payment_onramp`: Assess fees against the merchant. Example: 1.5% of the transaction amount. (This is the equivalent to say, a SWIFT fee part 1)
- `stablecoin_offramp`: Assess fees against the merchant. Example: $1.00 flat fee (This is the equivalent to say, a SWIFT fee part 2)

The fee engine events are `fee_invoice_payment`, `fee_payment_onramp`, and `fee_stablecoin_offramp`. Each event should log the fee amount, the party it was assessed against, and the timestamp of the fee assessment.

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
- `FEE_REVENUE_EUR` - EUR fees collected (per currency)

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

```
| Timestamp           | Debit                    | Credit              | Amount | Currency | Description                    |
|---------------------|--------------------------|---------------------|--------|----------|--------------------------------|
| 2023-10-01 12:05:00 | STRIPE_CLEARING          | PAYER_BANK_ACCOUNT  | 1005   | USD      | Payment + fee received via Stripe |
| 2023-10-01 12:05:00 | STRIPE_FEE_EXPENSE       | STRIPE_CLEARING     | 29.45  | USD      | Stripe processing fees ($0.30 + 2.9%) |
| 2023-10-01 12:05:00 | FEE_REVENUE_USD          | STRIPE_CLEARING     | 5      | USD      | Our payment processing fee     |
| 2023-10-01 12:05:00 | INFINITE_USD_BANK        | STRIPE_CLEARING     | 970.55 | USD      | Net amount after Stripe fees  |
```
**Balance Check**: 1005 = 29.45 + 5 + 970.55 ✓

#### Event 2: USD to USDC Conversion
**Fee: $1.00 (0.1% of invoice amount) assessed to merchant**
**Exchange Rate: 1 USD = 1 USDC**

```
| Timestamp           | Debit                       | Credit                | Amount | Currency | Description                        |
|---------------------|-----------------------------|-----------------------|--------|----------|------------------------------------|
| 2023-10-01 12:10:00 | FEE_REVENUE_USD             | INFINITE_USD_BANK     | 1.00   | USD      | Onramp fee (0.1% of 1000)        |
| 2023-10-01 12:10:00 | INFINITE_CUSTODY_USDC       | INFINITE_USD_BANK     | 969.55 | USDC     | USD converted to USDC (969.55 * 1.0) |
```
**Balance Check**: 970.55 = 1.00 + 969.55 ✓

#### Event 3: Transfer to Merchant Offramp Account
**Fee: $1 USDC transfer fee assessed to merchant**
**Prepare merchant-specific USDC for offramp**

```
| Timestamp           | Debit                       | Credit                | Amount | Currency | Description                        |
|---------------------|-----------------------------|-----------------------|--------|----------|------------------------------------|
| 2023-10-01 12:15:00 | FEE_REVENUE_USDC            | INFINITE_CUSTODY_USDC | 1      | USDC     | Transfer fee (1 USDC)             |
| 2023-10-01 12:15:00 | MERCHANT_OFFRAMP_USDC       | INFINITE_CUSTODY_USDC | 968.55 | USDC     | Net transfer to merchant offramp account |
```
**Balance Check**: 969.55 = 1 + 968.55 ✓

#### Event 4: USDC to EUR Conversion & Payout
**Exchange Rate: 1 USDC = 0.86 EUR as of 8/11/2025 (including theoretical offramp provider fees and spread)**
**Net to merchant: 968.55 USDC → €832.95**

**Design Notes**: 
1. **Offramp Provider Fees**: Real offramp providers (Circle, Fireblocks, etc.) charge additional fees beyond the exchange rate spread, but these are provider-specific and excluded from this demo for simplicity. In theory, you'd want to track that and have a line item for that.
2. **No Additional Platform Fees**: I've intentionally chosen not to charge additional fees at the offramp stage to maintain accounting simplicity and keep all our platform fees denominated in USD/USDC rather than dealing with multi-currency fee revenue tracking.

```
| Timestamp           | Debit                      | Credit                  | Amount | Currency | Description                      |
|---------------------|----------------------------|-------------------------|--------|----------|----------------------------------|
| 2023-10-01 12:20:00 | MERCHANT_BANK_ACCOUNT      | MERCHANT_OFFRAMP_USDC   | 832.95 | EUR      | USDC offramped to EUR (968.55 * 0.86) |
```
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

### Key Improvements
- **Perfect Balance**: Every transaction balances completely with explicit exchange rates
- **Atomic Fee Collection**: Fees are collected during the actual transaction, not pre-assessed
- **Clear Currency Conversions**: Exchange rates are explicit with dedicated suspense accounts
- **Rollback Capability**: Each step can be reversed by creating offsetting entries
- **Audit Trail**: Every movement of funds is tracked with clear descriptions
- **Separation of Concerns**: Fee revenue is separate from operational accounts

## Regulatory Notes
- **Co-mingling of Funds**: The custody wallet (`CUSTODY_WALLET`) will hold funds from multiple merchants and payers. This is a serious risk for regulatory compliance, especially in terms of KYC/AML regulations. In a production system, it would be advisable to have separate custody wallets for each merchant or recipient bank to mitigate this risk.
- **KYC/AML Compliance**: Ensure that both the merchant and payer are compliant with KYC/AML regulations. This existing flow is a compliance nightmare!
- **Transaction Limits**: Implement transaction limits to prevent money laundering and fraud. This is a must for the offramp service.
- **Transaction Monitoring**: Monitor transactions for suspicious activity and report any suspicious transactions to the relevant authorities. This is a must for the offramp service.

