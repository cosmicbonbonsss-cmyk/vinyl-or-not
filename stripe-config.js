/* Public Stripe config for Vinyl or Not.
 * Single paid tier: $10–$15 (default product $12).
 * Replace checkoutUrl with a Stripe Test Payment Link for that one-time price.
 * Success redirect: https://cosmicbonbonsss-cmyk.github.io/vinyl-or-not/?report=1
 */
window.VINYL_OR_NOT_STRIPE = {
  /* Placeholder — paste your Stripe Test Payment Link for the $12 (or $10–15) product */
  checkoutUrl: "",
  priceLabel: "$12",
  priceBand: "$10–$15",
  currency: "USD",
  mode: "payment" /* one-time, single paid tier */
};
