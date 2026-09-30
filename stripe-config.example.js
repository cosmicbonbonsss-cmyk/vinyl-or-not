/* Copy to stripe-config.js and fill in your Stripe Payment Link.
 * Create one one-time Payment Link for $12 (or any price in the $10–$15 band).
 * Success redirect: https://vinylornot.com/?report=1
 * Tiers: Free teaser | Paid full report only — no middle tier.
 */
window.VINYL_OR_NOT_STRIPE = {
  checkoutUrl: "https://buy.stripe.com/test_REPLACE_ME",
  priceLabel: "$12",
  priceBand: "$10–$15",
  currency: "USD",
  mode: "payment"
};
