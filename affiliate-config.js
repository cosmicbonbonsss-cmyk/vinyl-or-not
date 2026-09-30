/* Public affiliate settings for Vinyl or Not.
 * Keep amazonTag empty until you have an approved Amazon Associates store ID.
 * The category URLs below are ordinary retailer links and remain usable without IDs.
 */
window.VINYL_OR_NOT_AFFILIATE = {
  enabled: true,
  // Fill these after joining programs:
  amazonTag: "", // Amazon Associates store ID, e.g. yourstore-20 (do not invent one)
  // Optional path templates; if tag is empty, links are plain retailer URLs.
  links: {
    amazon: "https://www.amazon.com/s?k=luxury+vinyl+plank+flooring",
    homeDepot: "https://www.homedepot.com/b/Flooring-Vinyl-Flooring-Vinyl-Plank-Flooring/N-5yc1vZbzjz",
    lowes: "https://www.lowes.com/pl/vinyl-flooring/vinyl-plank/4294608591",
    floorAndDecor: "https://www.flooranddecor.com/luxury-vinyl-plank-and-tile"
  }
};
