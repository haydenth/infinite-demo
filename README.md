
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

## Transaction Ledger + Fee Engine
To support this whole operation, we need an atomic transaction ledger that tracks all the events and fees associated with each transaction. Each event should be logged with a timestamp, the parties involved, the amounts, and any fees assessed. An example (table) ledger might look like this:

```
| Timestamp           | Event Type          | Debit                      | Credit                      | Currency | Amount    | Description                                   |
|---------------------|---------------------|-----------------------------|-----------------------------|----------|-----------|-----------------------------------------------|
| 2023-10-01 12:00:00 | invoice_create      | MERCHANT_PAYABLE            | INFINITE_FEE_BANK_ACCOUNT   | USD      | 10.00     | Fee assessed to merchant (not yet collected)  |
| 2023-10-01 12:00:00 | invoice_create      | PAYER_RECEIVABLE            | MERCHANT_PAYABLE            | USD      | 1000.00   | Invoice issued for Work Order #12345          |
| 2023-10-01 12:05:00 | invoice_payment     | STRIPE_CLEARING_ACCOUNT     | PAYER_RECEIVABLE            | USD      | 1000.00   | Payer submits payment via Stripe              |
| 2023-10-01 12:06:00 | stripe_settlement   | INFINITE_BANK_ACCOUNT       | STRIPE_CLEARING_ACCOUNT     | USD      | 1000.00   | Stripe settles funds to Infinite              |
| 2023-10-01 12:10:00 | payment_onramp      | CUSTODY_WALLET              | INFINITE_BANK_ACCOUNT       | USD      | 1000.00   | Infinite converts fiat to USDC                |
| 2023-10-01 12:10:00 | payment_onramp_fee  | INFINITE_FEE_BANK_ACCOUNT   | CUSTODY_WALLET              | USD      | 10.00     | Collection of previously assessed invoice fee |
| 2023-10-01 12:12:00 | fx_conversion       | FX_CLEARING_ACCOUNT         | CUSTODY_WALLET              | USD      | 990.00    | Move USDC to FX/offramp engine                 |
| 2023-10-01 12:12:00 | fx_conversion       | MERCHANT_PAYABLE            | FX_CLEARING_ACCOUNT         | EUR      | 920.00    | Converted USD to EUR for merchant             |
| 2023-10-01 12:15:00 | offramp_settlement  | MERCHANT_BANK_ACCOUNT       | MERCHANT_PAYABLE            | EUR      | 905.00    | Payout to merchant after offramp fee          |
| 2023-10-01 12:15:00 | offramp_fee         | INFINITE_FEE_BANK_ACCOUNT   | MERCHANT_PAYABLE            | EUR      | 15.00     | Offramp fee collected from merchant           |
```

At the end of this, the final balances should be:
```
| Account                        | Currency | Final Balance |
|--------------------------------|----------|---------------|
| MERCHANT_BANK_ACCOUNT          | EUR      | 905.00        |
| MERCHANT_PAYABLE               | EUR      | 0.00          |
| PAYER_BANK_ACCOUNT             | USD      | -1000.00      |
| PAYER_RECEIVABLE               | USD      | 0.00          |
| STRIPE_CLEARING_ACCOUNT        | USD      | 0.00          |
| INFINITE_BANK_ACCOUNT          | USD      | 0.00          |
| CUSTODY_WALLET                 | USD      | 0.00          |
| FX_CLEARING_ACCOUNT            | USD      | 0.00          |
| INFINITE_FEE_BANK_ACCOUNT      | USD      | 10.00         |
| INFINITE_FEE_BANK_ACCOUNT      | EUR      | 15.00         |
```

## Regulatory Notes
- **Co-mingling of Funds**: The custody wallet (`CUSTODY_WALLET`) will hold funds from multiple merchants and payers. This is a serious risk for regulatory compliance, especially in terms of KYC/AML regulations. In a production system, it would be advisable to have separate custody wallets for each merchant or recipient bank to mitigate this risk.
- **KYC/AML Compliance**: Ensure that both the merchant and payer are compliant with KYC/AML regulations. This existing flow is a compliance nightmare!
- **Transaction Limits**: Implement transaction limits to prevent money laundering and fraud. This is a must for the offramp service.
- **Transaction Monitoring**: Monitor transactions for suspicious activity and report any suspicious transactions to the relevant authorities. This is a must for the offramp service.

