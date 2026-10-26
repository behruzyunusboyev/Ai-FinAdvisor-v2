# Payme SaaS subscription setup

The integration uses Payme Merchant API checkout. A user starts and renews the
configured subscription manually; the application does not save card data or
charge a card automatically. The Payme Subscribe API's card-token flow is a
separate integration and is not enabled here.

Configure these backend environment variables before enabling checkout:

- `PAYME_MERCHANT_ID`: merchant/cashbox identifier used in the checkout link.
- `PAYME_MERCHANT_LOGIN` and `PAYME_MERCHANT_KEY`: HTTP Basic credentials
  Payme supplies for Merchant API callback authentication.
- `PAYME_SUBSCRIPTION_PRICE_TIYIN`: approved subscription price in tiyin.
- `PAYME_SUBSCRIPTION_PERIOD_DAYS`: approved period length in days.
- `PAYME_SUBSCRIPTION_PLAN_CODE`: stable identifier for the configured offer.
- `PAYME_CHECKOUT_URL`: production checkout URL; use the test URL in sandbox.
- `PAYME_RETURN_URL`: optional browser return URL after checkout.

Apply database migrations with `alembic upgrade head` from the backend project.
Register `POST https://<backend-host>/api/v1/payments/payme` as the Payme
Merchant API endpoint. The authenticated application endpoint
`POST /api/v1/payments/payme/checkout` creates a payment using the configured
price; `GET /api/v1/payments/subscription` returns the current entitlement.

The callback supports `CheckPerformTransaction`, `CreateTransaction`,
`PerformTransaction`, `CancelTransaction`, and `CheckTransaction`. Checkout
amounts are sent in tiyin as required by Payme. Subscription access changes only
after `PerformTransaction`; cancelling a completed payment does not silently
revoke already granted access.

Use Payme's merchant sandbox to test the Merchant API before switching the
checkout URL and credentials to production. Credentials belong in deployment
secrets or an untracked `.env`, never in source control.
