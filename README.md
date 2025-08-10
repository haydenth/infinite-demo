
## Parties and Wallets

- **Merchant**: The user who initiates the invoice request and is the recipient of the payment. They have a native currency that may not be in USD. This user has the following accounts:
  - **Bank Account (`MERCHANT_BANK_ACCOUNT`)**: A non-US bank account attached to payment credentials (visible to us) that will receive offramped funds
- **Payer**: The user who receives the invoice and makes the payment. They will pay in USD, but the merchant may want to receive the payment in a different currency.
  - **Bank Account (`PAYER_BANK_ACCOUNT`)**: A US bank account attached to payment credentials (invisible to us) used to onramp funds
- **Stripe Payment Processing**: The service that handles the payment transactions: Stripe
- **Infinite Custody Bank Account (`INFINITE_BANK_ACCOUNT`)**: A US bank account that holds USD and is used to facilitate the transfer of funds between the merchant and payer. This account is managed by us and is used to hold custody of funds during transfer.
- **Infinite Custody Wallet (`CUSTODY_WALLET`)**: A wallet that holds the stablecoins (USDC) and is used to facilitate the transfer of funds between the merchant and payer. This wallet is managed by us and is used to hold custody of funds during transfer. Practically, it might make sense to have a separate custody wallet for each merchant (privacy issues) or with each receipient bank (e.g. one for EUR, one for GBP, etc.). This wallet is used to hold the stablecoins during the transfer process.


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

The user sends the invoice to the payer via email or other communication channels. The payer receives a link to view and pay the invoice.  The payer clicks the link in the invoice and is directed to a secure payment page. The payer selects their preferred payment method (credit card, bank transfer, etc.) and enters the required payment details. This will go through Stripe. At this point, we may need to assess fees to the payer in addition to stripe's default fees (optional).

### 2) Payment Onramp (USD) (`payment_onramp`)
At least in theory (ignoring settlement delays and MTL compliance) we'll have our US bank account funded with USD. At this point, we need to go out an make a purchase of USDC. To keep it simple this is done by making a purchase of USDC on a centralized exchange. It is then held in the custody wallet (`CUSTODY_WALLET`) where it is comingled with other funds (note: this is a bad idea but we're trying to get a simple demo here, not a final production product). 

We may also need to assess fees at this point as well. In fact, this is probably the final place where we may wish to assess fees since we can keep them in our `INFINITE_BANK_ACCOUNT` and not have to worry about them being in the custody wallet.

### 3) Stablecoin Offramp (Native Currency) (`stablecoin_offramp`)
At this point, the merchant has a bank account in their native currency `MERCHANT_BANK_ACCOUNT`. We need to offramp the USDC to the merchant's bank account. This is done by using a mocked offramp service that simulates the process of converting USDC to the merchant's native currency and sending it to their bank account. In a real-world scenario, this would involve using a service like Fireblocks, Circle, or similar to handle the conversion and transfer. This is probably the hardest and riskiest part of the entire exchange.




## Regulatory Notes
- **Co-mingling of Funds**: The custody wallet (`CUSTODY_WALLET`) will hold funds from multiple merchants and payers. This is a serious risk for regulatory compliance, especially in terms of KYC/AML regulations. In a production system, it would be advisable to have separate custody wallets for each merchant or recipient bank to mitigate this risk.
- **KYC/AML Compliance**: Ensure that both the merchant and payer are compliant with KYC/AML regulations. This existing flow is a compliance nightmare!
- **Transaction Limits**: Implement transaction limits to prevent money laundering and fraud. This is a must for the offramp service.
- **Transaction Monitoring**: Monitor transactions for suspicious activity and report any suspicious transactions to the relevant authorities. This is a must for the offramp service.

