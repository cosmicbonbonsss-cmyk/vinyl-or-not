#!/usr/bin/env python3
"""Rebuild the body copy of the 76 floor-look pages (floors/<look>-<room>.html).

Each page = one wood look x one room size. The text comes from three data
tables below so every page stays consistent with the site's standards
(12 mil wear layer normally, 20 mil with dogs; rigid core SPC/WPC for wet
rooms; about 4-8 mm total plank thickness; 10% waste):

  LOOKS  - what the look is, what it hides/shows, what it pairs with
  ROOMS  - practical notes and a quick buying spec for that room
  TONE_TIPS / PATTERN_TIPS - tips for a look *in* a room

The script edits pages in place: <title>, meta description, og/twitter
tags, image alt, JSON-LD description, and everything inside <main>.
Header, footer, and scripts are left alone. Run from the repo root:

    python3 scripts/build_floor_pages.py
    python3 scripts/build_search_index.py

Standard library only.
"""
from __future__ import annotations

import html
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLOORS = ROOT / "floors"
SITE = "https://vinylornot.com/"
BOX_SQFT = 20  # matches the measure tool default

# ---------------------------------------------------------------- rooms
ROOMS = {
    "living-room": {
        "label": "living room", "dims": (12, 10), "article": "a",
        "notes": (
            "Living rooms take furniture weight, sunlight, and foot traffic from the front door. "
            "Put felt pads under sofa and chair legs, and use rug pads that are labeled safe for vinyl, "
            "since some rubber or latex backings can stain or discolor the wear layer. Strong sun through "
            "large windows can fade or heat planks over time, so blinds or UV film help. In an open plan, "
            "check the manufacturer's maximum run length; long runs into a hallway or dining room often need "
            "a T-molding at the doorway."
        ),
        "spec": [
            ("Core", "rigid core (SPC or WPC); WPC feels a little softer and quieter underfoot"),
            ("Wear layer", "12 mil for most homes; 20 mil with dogs or a busy entry path"),
            ("Thickness", "about 5–8 mm total, ideally with an attached pad"),
            ("Waste", "10% for a straight lay; more if the room has angled walls or a fireplace hearth"),
        ],
        "guide": [("../guide/measure-plan.html", "Measure & plan", "which way to run planks and where transitions go"),
                  ("../guide/finish-care.html", "Finish & care", "baseboards, transitions, and furniture pads")],
    },
    "bedroom": {
        "label": "bedroom", "dims": (11, 12), "article": "an",
        "notes": (
            "Bedrooms are the easiest room for a first DIY floor: little water, light traffic, and fewer "
            "obstacles. Comfort and sound matter more here than toughness. A plank with an attached pad, or a "
            "manufacturer-approved underlayment, softens the feel and cuts the hollow click underfoot, which "
            "helps if someone sleeps below. Don't stack a second foam pad under planks that already have one. "
            "Undercut the door jamb so planks slide under it, and put felt pads on bed and dresser legs."
        ),
        "spec": [
            ("Core", "rigid core (SPC or WPC); WPC is a little quieter for bedrooms"),
            ("Wear layer", "12 mil is plenty; 20 mil if dogs sleep in the room"),
            ("Thickness", "about 5–8 mm total; an attached pad helps with comfort and sound"),
            ("Waste", "10%, plus a little extra if the closet has an odd shape"),
        ],
        "guide": [("../guide/prep.html", "Subfloor prep", "underlayment choices and flatness checks"),
                  ("../guide/is-it-okay.html", "Is vinyl okay for my room?", "pets, kids, and renters")],
    },
    "kitchen": {
        "label": "kitchen", "dims": (10, 12), "article": "a",
        "notes": (
            "Kitchens get water, grease, and dropped pans. Choose a waterproof rigid core plank with tight "
            "click joints, and wipe spills instead of letting them sit at the seams. Cabinets and islands "
            "should stay on the subfloor with the floating floor installed up to them, not under them, so the "
            "floor can move. Leave the expansion gap at walls and appliance openings, slide the fridge out on "
            "a scrap of hardboard so its wheels don't gouge the planks, and plan a transition strip where the "
            "kitchen meets another floor."
        ),
        "spec": [
            ("Core", "waterproof rigid core (SPC or WPC)"),
            ("Wear layer", "12 mil for most kitchens; 20 mil with dogs or heavy traffic"),
            ("Thickness", "about 5–7 mm total; check that the dishwasher can still slide out"),
            ("Waste", "10%; cuts around the island and cabinet toe-kicks use most of it"),
        ],
        "guide": [("../guide/is-it-okay.html", "Is vinyl plank good for kitchens?", "water, spills, and pets"),
                  ("../guide/lvp-over-tile.html", "LVP over tile", "if there's old tile on the floor now")],
    },
    "bathroom": {
        "label": "bathroom", "dims": (5, 8), "article": "a",
        "notes": (
            "A bathroom needs a waterproof rigid core plank; SPC is the usual pick. Waterproof planks still "
            "let water reach the subfloor at the edges, so leave the expansion gap around the tub, toilet "
            "flange, and vanity, then seal it in the wet zones with 100% silicone caulk. Pull the toilet, run "
            "planks under its footprint, and reset it with a new wax ring. Fit planks around a heavy built-in "
            "vanity rather than under it. In a small room the cuts around the toilet and door jamb take most "
            "of the time."
        ),
        "spec": [
            ("Core", "waterproof rigid core; SPC is the usual choice for bathrooms"),
            ("Wear layer", "12 mil; 20 mil if dogs use the room"),
            ("Thickness", "about 5–6 mm total; enough for a bathroom while keeping the toilet flange and door clearance simple"),
            ("Waste", "10%; in a 5 by 8 room you'll buy whole boxes, so the spare covers it"),
        ],
        "guide": [("../guide/is-it-okay.html", "Is vinyl plank good for bathrooms?", "water, steam, and wet zones"),
                  ("../guide/lvp-over-tile.html", "LVP over tile", "covering old bathroom tile and grout lines")],
    },
}
ROOM_ORDER = ["living-room", "bedroom", "kitchen", "bathroom"]

# ---------------------------------------------------------------- looks
# tone: light | lightmid | mid | dark | vdark   pattern: busy | even | plain | narrow | wide
LOOKS = {
    "white-oak": dict(name="White oak", tone="light", pattern="plain",
        about="White oak LVP copies pale, cool-to-neutral oak with a straight, fine grain. Light floors hide dust, light pet hair, and fine surface scratches well, but tracked-in mud and coffee drips stand out. It pairs with white or light gray cabinets, black hardware, and Scandinavian or modern farmhouse rooms, and it makes small or north-facing rooms feel brighter.",
        special="If the {room} has warm yellow walls or orange-toned wood trim, put a white oak sample next to them first; cool white oak can look gray beside very warm colors.",
        swatch="pale, cream-colored planks with a fine straight grain",
        short="pale and bright, hides dust", similar=["natural-oak", "maple", "gray-oak"]),
    "natural-oak": dict(name="Natural oak", tone="lightmid", pattern="plain",
        about="Natural oak sits in the middle of the light range: beige with a hint of yellow, clear cathedral and straight grain, and no strong stain color. It's one of the most forgiving looks, since mid-light tones hide crumbs, dust, and most scuffs. It works with nearly any cabinet or wall color, from white to navy to sage green.",
        special="Natural oak is the safe choice if you plan to repaint the {room} later; it rarely clashes with a new wall color.",
        swatch="light beige planks with soft gray-green streaks and fine grain",
        short="easygoing beige, hides crumbs", similar=["white-oak", "medium-oak", "honey-oak"]),
    "medium-oak": dict(name="Medium oak", tone="mid", pattern="plain",
        about="Medium oak is the classic tan-brown oak stain with clear grain and a few small knots. Its middle tone hides everyday dirt, dust, and minor scratches better than very light or very dark floors. It suits traditional and transitional rooms with white or cream trim, and it looks right in both sunny and dim rooms.",
        special="Medium oak hides the gray dust that collects along baseboards, so the {room} looks clean between deep cleanings.",
        swatch="brown oak planks with dark knots and a rustic grain",
        short="classic tan-brown, hides dirt", similar=["warm-oak", "natural-oak", "hickory"]),
    "warm-oak": dict(name="Warm oak", tone="mid", pattern="busy",
        about="Warm oak leans amber and caramel, often with a knotty, rustic character. The warm tone and busy grain hide crumbs, paw prints, and small dents well. It pairs with cream or warm white walls, olive or terracotta accents, and wood or black cabinets. In a dim room, pick a lighter warm oak so the floor doesn't read as plain brown.",
        special="Under warm-white bulbs warm oak deepens toward orange, so look at the sample in the {room} at night as well as in daylight.",
        swatch="dark, weathered brown planks with knots",
        short="amber, hides paw prints", similar=["medium-oak", "honey-oak", "hickory"]),
    "honey-oak": dict(name="Honey oak", tone="lightmid", pattern="plain",
        about="Honey oak is the golden-orange oak look common in 1990s homes, with a pronounced grain. It hides yellowish dust and crumbs well. If the house already has honey oak cabinets or trim, a near-match on the floor often looks off, while a cooler or darker floor creates a cleaner contrast. It suits warm white or soft green walls.",
        special="If the {room} connects to honey oak hardwood you're keeping elsewhere, honey oak LVP can carry the same tone across the doorway so the transition looks planned.",
        swatch="gray-brown planks with long, even vertical boards",
        short="golden and warm, hides crumbs", similar=["golden-oak", "natural-oak", "warm-oak"]),
    "golden-oak": dict(name="Golden oak", tone="lightmid", pattern="plain",
        about="Golden oak is a saturated yellow-gold stain with lively grain. It brightens rooms that get little sun and hides dust and light-colored pet hair. Pair it with white or cream walls and simple trim; yellow walls or orange-toned furniture can make the room feel too yellow overall.",
        special="Golden oak lifts a {room} that faces north or has small windows; balance it with white trim and cooler accents like blue or gray textiles.",
        swatch="bright golden-orange planks with a smooth, even grain",
        short="yellow-gold, lifts dim rooms", similar=["honey-oak", "pine-natural", "narrow-plank"]),
    "maple": dict(name="Maple", tone="light", pattern="even",
        about="Maple-look LVP is pale and creamy with a very fine, smooth grain and little figure. The clean, uniform surface shows dark dirt and scratches a bit more than busy grains do, but it keeps rooms bright and calm. It pairs with white, light gray, or soft blue walls and modern or minimal furniture.",
        special="Maple's quiet grain lets other things in the {room} stand out, so it's a good pick if you have patterned rugs, tile, or bold paint.",
        swatch="pale yellow planks with a very fine, smooth grain",
        short="pale and smooth, calm and bright", similar=["white-oak", "natural-oak", "golden-oak"]),
    "hickory": dict(name="Hickory", tone="mid", pattern="busy",
        about="Hickory looks rustic: strong contrast between light and dark streaks, knots, and big color shifts from plank to plank. That variation is one of the best at hiding dirt, pet hair, scratches, and dents. It suits cabin, farmhouse, and casual family rooms; keep walls and rugs simple so the floor doesn't feel loud.",
        special="When you lay hickory in the {room}, open three or four boxes and mix planks as you go, or you can end up with a patch of all-light or all-dark boards.",
        swatch="light tan planks with dark knots and long boards",
        short="rustic, hides almost everything", similar=["acacia", "pine-natural", "warm-oak"]),
    "acacia": dict(name="Acacia", tone="mid", pattern="busy",
        about="Acacia has dramatic color variation, with honey, chocolate, and near-black streaks in the same plank and a tight, wavy grain. Like hickory, that variation hides crumbs, paw prints, and scuffs. It pairs with white or warm white walls, black metal, and solid-color rugs; avoid putting it next to another busy pattern.",
        special="Acacia's dark streaks can look almost black in low light, so check the sample in the {room} under the lights you actually use.",
        swatch="dark brown planks with golden and black streaks",
        short="dramatic streaks, hides scuffs", similar=["hickory", "walnut", "warm-oak"]),
    "cherry": dict(name="Cherry", tone="dark", pattern="even",
        about="Cherry-look LVP is a reddish brown with a smooth, fine grain, a warm and slightly formal look. The red-brown tone hides dirt fairly well but shows dust and light pet hair. It pairs with cream or warm white walls and traditional furniture, and it can clash with red-brown wood furniture or orange-toned trim.",
        special="Cherry reads redder in a sunny {room} and browner in a dim one, so judge the sample where the floor will actually go.",
        swatch="reddish-brown planks with a smooth, fine grain",
        short="warm red-brown, a bit formal", similar=["walnut", "medium-oak", "acacia"]),
    "walnut": dict(name="Walnut", tone="dark", pattern="plain",
        about="Walnut is a rich medium-to-dark brown with a soft, flowing grain and a gray or purple undertone. It feels warm and upscale. It shows dust, lint, and light pet hair more than mid-tone floors, but hides darker dirt. It pairs with white, greige, or deep green walls and brass or black hardware, and it needs good light in a small room.",
        special="Walnut makes white trim and baseboards pop, so freshen the paint on the {room} trim before the new floor goes in.",
        swatch="gray-brown planks laid in a herringbone-style pattern",
        short="rich brown, warm and upscale", similar=["walnut-plank", "dark-walnut", "cherry"]),
    "walnut-plank": dict(name="Walnut plank", tone="dark", pattern="even",
        about="Walnut plank is a darker, more uniform walnut look with long boards and few knots, so the floor reads as calm, even lines. Like other dark floors, it shows dust and lint, and scratches in the wear layer tend to show as pale lines. It pairs with white or light walls, mid-century furniture, and brass or black accents.",
        special="Long walnut planks look best running toward the main light source or the longest wall of the {room}, which also keeps the seams less obvious.",
        swatch="dark brown planks in long, even rows",
        short="dark, calm long lines", similar=["walnut", "dark-walnut", "espresso"]),
    "dark-walnut": dict(name="Dark walnut", tone="vdark", pattern="plain",
        about="Dark walnut is a deep chocolate brown with soft grain, a high-contrast backdrop for white trim and light furniture. It's the least forgiving walnut look: dust, pet hair, footprints, and pale scratch lines show quickly. It works best in bright rooms with light walls; in a dim room it can make the space feel smaller.",
        special="Pick a dark walnut with some lighter streaks in the grain; a little variation hides dust and pale scratches in the {room} far better than a flat, solid brown.",
        swatch="deep brown planks with a mottled, darker grain",
        short="deep chocolate, high contrast", similar=["walnut", "walnut-plank", "espresso"]),
    "espresso": dict(name="Espresso", tone="vdark", pattern="even",
        about="Espresso is a near-black brown with very little visible grain. It looks crisp and modern with white walls and cabinets, but it shows dust, lint, water spots, and pale scratch lines more than any other look here. It suits lower-traffic rooms or households that don't mind sweeping often.",
        special="If you love espresso but worry about upkeep in the {room}, a 20 mil wear layer and a matte (low-gloss) finish make scratches and smudges much less obvious.",
        swatch="near-black brown planks in a staggered pattern",
        short="near-black and modern", similar=["dark-walnut", "walnut-plank", "walnut"]),
    "gray-oak": dict(name="Gray oak", tone="light", pattern="plain",
        about="Gray oak is oak grain with a cool gray or silvery stain. Light-to-mid grays hide dust and light pet hair well and suit modern rooms with white, black, or blue accents. Gray can read cold next to beige walls or yellow-toned wood cabinets, so check samples against whatever is staying in the room.",
        special="Gray oak can pick up a blue cast in a north-facing {room}; a gray sample with a slightly warm (greige) base avoids that.",
        swatch="very light, silvery gray planks with faint grain",
        short="cool and silvery, modern", similar=["gray-wash", "white-oak", "maple"]),
    "gray-wash": dict(name="Gray wash", tone="mid", pattern="busy",
        about="Gray wash, sometimes called weathered gray, imitates sun-bleached, whitewashed boards with visible streaks and color shifts. The streaky mid gray hides dirt, dust, and scratches very well. It suits coastal and farmhouse rooms with white, navy, or sage, and it keeps rooms from feeling yellow. In a dim room, choose a lighter wash so the floor doesn't look muddy.",
        special="Gray wash goes well with white and black fixtures and brushed-nickel hardware, so it rarely forces a change elsewhere in the {room}.",
        swatch="medium gray planks with streaks of lighter and darker gray",
        short="weathered gray, hides dirt well", similar=["gray-oak", "hickory", "natural-oak"]),
    "pine-natural": dict(name="Natural pine", tone="lightmid", pattern="busy",
        about="Natural pine is yellow-orange with bold knots and wide grain, a cottage or cabin look. The knots and color variation hide dirt and scratches. Real pine dents easily, but LVP with a decent wear layer doesn't share that weakness, so you get the look without the softness. It pairs with white, sage, and soft blue walls.",
        special="Pine-look planks have repeating knots, so in the {room} check that two identical planks don't end up side by side before you click them in.",
        swatch="orange-tan planks with dark knots and gaps between long boards",
        short="knotty cottage look", similar=["hickory", "golden-oak", "warm-oak"]),
    "narrow-plank": dict(name="Narrow plank", tone="lightmid", pattern="narrow",
        about="Narrow plank means thin boards, roughly 3 to 5 inches wide, which gives the busier, traditional look of older strip floors. The extra seams break up the surface and help hide scuffs, and running the planks along the long wall makes a small room look longer. The trade-off is more planks to click together, so the install takes longer.",
        special="Narrow planks change the plank count a lot: set the plank width in the measure tool (for example 4 inches instead of 7) so the {room} estimate is realistic.",
        swatch="orange-brown planks with a fine, even grain",
        short="thin traditional boards", similar=["golden-oak", "medium-oak", "honey-oak"]),
    "wide-plank": dict(name="Wide plank", tone="mid", pattern="wide",
        about="Wide plank uses boards about 8 to 9 inches wide or more, so there are fewer seams and a calmer, more open look. It suits larger rooms and open plans. Because there are fewer seams to absorb them, dips and humps in the subfloor show more, so wide planks need a flatter subfloor.",
        special="Before laying wide planks in the {room}, check flatness with a long straightedge and fill low spots; the manufacturer's flatness limit matters more with wide boards.",
        swatch="mixed light and dark brown planks in a staggered layout",
        short="fewer seams, open and calm", similar=["walnut-plank", "medium-oak", "natural-oak"]),
}

TONE_TIPS = {
    ("light", "kitchen"): "{look} hides flour and dust but shows coffee drips and tracked-in dirt in the lane between sink and stove; a washable runner there cuts down on mopping.",
    ("light", "bathroom"): "A light floor like {look_lc} makes a 5 by 8 bathroom feel bigger, but dark hair and grime show around the toilet base, so plan a quick wipe there.",
    ("light", "bedroom"): "{look} keeps a bedroom bright and hides dust bunnies and light pet hair; dirt from shoes shows most just inside the door.",
    ("light", "living-room"): "{look} shows dark grit on the path from the front door, so a doormat and a rug on the main walkway keep the room looking clean.",
    ("lightmid", "kitchen"): "{look} is forgiving in a kitchen: crumbs, flour, and light spills blend in, and only darker sauces stand out.",
    ("lightmid", "bathroom"): "{look} keeps a small bathroom bright while hiding dust and most stray hairs; only dark hair stands out near the sink.",
    ("lightmid", "bedroom"): "{look} keeps a bedroom warm and bright, and its tone hides dust between cleanings.",
    ("lightmid", "living-room"): "{look} handles living room traffic well; dust and crumbs blend in, and only muddy footprints stand out.",
    ("mid", "kitchen"): "{look} is a practical kitchen tone: it hides crumbs, flour, and coffee drips better than very light or very dark floors.",
    ("mid", "bathroom"): "{look} hides both light and dark hair in a bathroom, which very light and very dark floors can't.",
    ("mid", "bedroom"): "{look} gives a bedroom a grounded, cozy feel and hides the dust that collects under the bed and along the walls.",
    ("mid", "living-room"): "{look} hides the usual living room mix of crumbs, pet hair, and grit, so it looks clean longer between vacuums.",
    ("dark", "kitchen"): "{look} hides grease and darker spills, but crumbs, flour, and water spots show, especially near the sink.",
    ("dark", "bathroom"): "{look} hides dark hair but shows dust, powder, and dried water spots, so keep a microfiber mop handy.",
    ("dark", "bedroom"): "{look} suits a bedroom's low traffic; lint and dust show, but there's less of it than in busier rooms.",
    ("dark", "living-room"): "{look} shows dust and light pet hair in sunlit spots, so consider where the sun lands when you place rugs.",
    ("vdark", "kitchen"): "{look} is the hardest look to keep tidy in a kitchen: crumbs, flour, water spots, and pale scratch lines all show. Washable rugs at the sink and stove help.",
    ("vdark", "bathroom"): "{look} looks striking with white fixtures, but every hair, drop of toothpaste, and dried water spot shows on it.",
    ("vdark", "bedroom"): "{look} works well in a bedroom, which has the least traffic in the house, so dust is the main thing you'll notice.",
    ("vdark", "living-room"): "{look} shows footprints and dust in the main walkway; a large rug in the seating area cuts the cleaning a lot.",
}

PATTERN_TIPS = {
    ("busy", "kitchen"): "The knots and color variation hide dropped-pan dents and stool scuffs, which kitchens collect fast.",
    ("busy", "bathroom"): "In a small bathroom, a busy grain can compete with patterned tile or shower walls, so keep the other surfaces simple.",
    ("busy", "bedroom"): "The busy grain hides scratches from moving furniture and dragging laundry baskets.",
    ("busy", "living-room"): "The variation hides scuffs from furniture and toys, so a little wear won't show for years.",
    ("even", "kitchen"): "Because the grain is calm and even, pale scratch lines from chairs and stools show more, so put felt pads on every leg.",
    ("even", "bathroom"): "The even grain keeps a small bathroom looking tidy and uncluttered.",
    ("even", "bedroom"): "The smooth, even grain feels calm in a bedroom; felt pads under the bed and dresser keep it unscratched.",
    ("even", "living-room"): "The even grain shows chair and sofa scuffs more than a knotty look, so felt pads matter here.",
    ("plain", "kitchen"): "Run the planks parallel to the longest wall or the main path into the kitchen; it looks more natural and simplifies cuts at the cabinets.",
    ("plain", "bathroom"): "Run the planks the long way in a 5 by 8 room so it looks longer, and start with a full-width row against the tub, the edge people notice most.",
    ("plain", "bedroom"): "Run the planks toward the window or along the longest wall, and plan the last row so it isn't a thin sliver against the closet.",
    ("plain", "living-room"): "Run the planks toward the main window or along the longest wall, and continue the same direction into connected rooms for a seamless look.",
    ("narrow", "kitchen"): "In a kitchen, the extra seams of narrow planks mean more joints near the sink, so pick a plank with a tight, water-resistant click lock.",
    ("narrow", "bathroom"): "Narrow planks suit a 5 by 8 bathroom well, since they fit around the toilet and vanity with less waste than wide boards.",
    ("narrow", "bedroom"): "In a bedroom, narrow planks make an 11 by 12 room look a little longer when they run the long way.",
    ("narrow", "living-room"): "In a living room, narrow planks give a traditional look; expect the install to take longer than with standard 7 inch planks.",
    ("wide", "kitchen"): "Wide planks make a 10 by 12 kitchen feel more open, but cuts around cabinets and the island waste more per plank.",
    ("wide", "bathroom"): "In a 5 by 8 bathroom, wide planks can look out of scale and waste more at the toilet and vanity cuts; a standard width is often easier.",
    ("wide", "bedroom"): "Wide planks give an 11 by 12 bedroom a calm, open feel with very few visible seams.",
    ("wide", "living-room"): "Wide planks shine in a living room, especially in an open plan where the floor continues into the next room.",
}

# What each look pairs with in each room (cabinets, tile, bedding, sofas)
PAIRS = {
 "white-oak": {
  "kitchen": "White oak goes with white, cream, or pale gray cabinets and black or brass pulls; with white cabinets, a slightly warmer white oak keeps the kitchen from feeling sterile.",
  "bathroom": "With white oak, white or soft gray tile on the walls, a wood or white vanity, and black or chrome fixtures all work; avoid a pale beige tile that nearly matches the floor.",
  "bedroom": "White oak pairs with white or linen bedding, light wood or black furniture, and soft wall colors like warm white, pale sage, or light gray.",
  "living-room": "White oak suits a light sofa in linen or oatmeal, a wool or jute rug, and black accents like lamp bases or picture frames for contrast."},
 "natural-oak": {
  "kitchen": "Natural oak works with almost any cabinet color: white, navy, sage, or even wood cabinets one or two shades darker than the floor.",
  "bathroom": "Natural oak warms up white subway tile and pairs well with a navy, green, or white vanity and brushed brass or nickel fixtures.",
  "bedroom": "Natural oak looks relaxed with cream bedding, rattan or light wood furniture, and walls in warm white, clay, or muted green.",
  "living-room": "Natural oak handles a gray, green, or rust sofa equally well, so it's a good choice if the furniture may change in a few years."},
 "medium-oak": {
  "kitchen": "Medium oak pairs with white or cream cabinets and contrasts well with a dark island; avoid cabinets in the exact same brown.",
  "bathroom": "Medium oak looks good with a white vanity, white or cream tile, and oil-rubbed bronze or matte black fixtures.",
  "bedroom": "Medium oak pairs with white trim, cream or blue bedding, and darker wood furniture, giving a traditional look.",
  "living-room": "Medium oak works with leather or tan sofas, cream walls, and patterned rugs in blue, red, or green."},
 "warm-oak": {
  "kitchen": "Warm oak pairs with cream or warm white cabinets, butcher-block counters, and copper or brass hardware; cool gray cabinets can clash with it.",
  "bathroom": "Warm oak looks good with cream or terracotta-toned tile, a white or olive vanity, and brass fixtures.",
  "bedroom": "Warm oak pairs with rust, olive, or cream bedding and walls in warm white or soft clay for a cozy feel.",
  "living-room": "Warm oak suits leather, rust, or olive sofas, and a cream or muted patterned rug keeps the room from looking too orange."},
 "honey-oak": {
  "kitchen": "If the kitchen keeps honey oak cabinets, a floor in a cooler or darker tone usually looks better than a close match; with painted cabinets, honey oak adds warmth.",
  "bathroom": "Honey oak pairs with white tile, a white or sage vanity, and brushed nickel or brass fixtures; it can look dated next to almond-colored tile.",
  "bedroom": "Honey oak works with white bedding, sage or soft blue walls, and white or black furniture rather than more honey-toned wood.",
  "living-room": "Honey oak pairs with a green, blue, or gray sofa; a sofa in a similar golden tone can make the room feel flat."},
 "golden-oak": {
  "kitchen": "Golden oak pairs with white cabinets and white or light gray counters; skip yellow walls and orange-toned cabinets.",
  "bathroom": "Golden oak brightens a white bathroom; white tile and a white or navy vanity balance its yellow tone.",
  "bedroom": "Golden oak looks good with white walls, navy or gray bedding, and simple black or white furniture.",
  "living-room": "Golden oak pairs with blue, gray, or green upholstery, which cools down its yellow, and with white walls."},
 "maple": {
  "kitchen": "Maple suits white, light gray, or soft blue cabinets and lets a patterned backsplash take center stage.",
  "bathroom": "Maple pairs with white or pale blue tile and a white vanity for a light, clean bathroom.",
  "bedroom": "Maple pairs with white or gray bedding, light furniture, and soft blue or gray walls for a calm bedroom.",
  "living-room": "Maple works with gray or blue sofas and modern or Scandinavian furniture, and lets a colorful rug stand out."},
 "hickory": {
  "kitchen": "Hickory pairs with white, cream, or black cabinets in plain shaker or flat fronts; ornate cabinet doors plus hickory grain can look busy.",
  "bathroom": "Hickory works with plain white tile and a white or black vanity, so the floor carries the rustic character.",
  "bedroom": "Hickory pairs with plain white or cream bedding, iron or simple wood furniture, and a solid-color rug.",
  "living-room": "Hickory suits leather or solid-color sofas and plain rugs; skip large patterns that compete with the grain."},
 "acacia": {
  "kitchen": "Acacia pairs with white or black cabinets and plain quartz or butcher-block counters; skip busy granite.",
  "bathroom": "Acacia works with white tile and a black or white vanity; a busy tile pattern next to it can feel crowded.",
  "bedroom": "Acacia pairs with white bedding, black metal or white furniture, and warm white walls.",
  "living-room": "Acacia pairs with cream, white, or charcoal sofas and a solid rug that gives the eye a place to rest."},
 "cherry": {
  "kitchen": "Cherry pairs with white or cream cabinets and dark green or black counters; avoid cabinets in a red-brown that nearly matches.",
  "bathroom": "Cherry looks good with cream tile, a white vanity, and bronze or brass fixtures in a traditional bathroom.",
  "bedroom": "Cherry pairs with cream or deep green bedding and traditional furniture in a lighter or painted finish.",
  "living-room": "Cherry pairs with cream, navy, or forest green sofas and traditional rugs with red or gold tones."},
 "walnut": {
  "kitchen": "Walnut pairs with white or deep green cabinets and brass hardware; in a small kitchen, keep walls and counters light.",
  "bathroom": "Walnut looks good with white tile, a white or green vanity, and brass or matte black fixtures.",
  "bedroom": "Walnut pairs with white or cream bedding, brass lamps, and walls in white, greige, or deep green.",
  "living-room": "Walnut suits cream, camel, or green sofas, and a lighter rug keeps the room from feeling heavy."},
 "walnut-plank": {
  "kitchen": "Walnut plank pairs with white or light gray cabinets and simple slab or shaker doors for a mid-century or modern kitchen.",
  "bathroom": "Walnut plank looks good with white tile, a floating white or wood vanity, and matte black fixtures.",
  "bedroom": "Walnut plank pairs with mid-century furniture, white bedding, and light walls that balance the dark floor.",
  "living-room": "Walnut plank suits mid-century sofas in green, mustard, or cream, and a light rug under the seating area."},
 "dark-walnut": {
  "kitchen": "Dark walnut pairs with white cabinets and light counters; with dark cabinets too, the kitchen can feel closed in.",
  "bathroom": "Dark walnut works with white tile, a white vanity, and good lighting; it can make a windowless bathroom feel smaller.",
  "bedroom": "Dark walnut pairs with white or cream walls, light bedding, and lamps that keep the room from feeling heavy at night.",
  "living-room": "Dark walnut suits white, cream, or gray sofas and a large light rug that breaks up the dark area."},
 "espresso": {
  "kitchen": "Espresso pairs with white cabinets and white or light gray counters for a high-contrast modern kitchen.",
  "bathroom": "Espresso looks striking with white tile, white fixtures, and a white or light wood vanity; bright lighting keeps a small bathroom from feeling dark.",
  "bedroom": "Espresso pairs with white walls and bedding and modern furniture for a calm, high-contrast bedroom.",
  "living-room": "Espresso suits white or light gray sofas and a large pale rug in the seating area."},
 "gray-oak": {
  "kitchen": "Gray oak pairs with white, black, or navy cabinets and white or gray quartz; it can clash with beige granite or oak cabinets.",
  "bathroom": "Gray oak works with white or marble-look tile, a white or navy vanity, and chrome or nickel fixtures.",
  "bedroom": "Gray oak pairs with white, navy, or blush bedding and white or black furniture.",
  "living-room": "Gray oak suits gray, navy, or white sofas and cool-toned rugs; warm beige walls may make it look cold."},
 "gray-wash": {
  "kitchen": "Gray wash pairs with white or navy cabinets and white counters for a coastal or farmhouse kitchen.",
  "bathroom": "Gray wash works with white shiplap or subway tile, a navy or white vanity, and nickel fixtures.",
  "bedroom": "Gray wash pairs with white and blue bedding, white furniture, and soft blue or sage walls.",
  "living-room": "Gray wash suits slipcovered white or blue sofas and natural fiber rugs."},
 "pine-natural": {
  "kitchen": "Natural pine pairs with white, sage, or soft blue cabinets for a cottage kitchen; pine-colored cabinets on a pine floor look heavy.",
  "bathroom": "Natural pine looks good with white beadboard or tile, a white or blue vanity, and simple brass or nickel fixtures.",
  "bedroom": "Natural pine pairs with quilts, white or blue bedding, and painted furniture for a cabin or cottage bedroom.",
  "living-room": "Natural pine suits blue, green, or plaid upholstery and braided or wool rugs."},
 "narrow-plank": {
  "kitchen": "Narrow planks give a traditional kitchen a classic strip-floor look under white or cream cabinets.",
  "bathroom": "Narrow planks pair with white tile and a traditional vanity and fit around tight spots with less waste.",
  "bedroom": "Narrow planks suit traditional bedrooms with white trim and wood or painted furniture.",
  "living-room": "Narrow planks give a classic look under traditional sofas and patterned rugs, much like older homes."},
 "wide-plank": {
  "kitchen": "Wide planks pair with white or wood cabinets and suit open kitchens that flow into a dining or living area.",
  "bathroom": "Wide planks look best with simple white tile and a floating vanity, so the room doesn't feel crowded.",
  "bedroom": "Wide planks pair with a simple bed frame, light bedding, and few rugs, so the floor's calm lines show.",
  "living-room": "Wide planks suit open-plan living rooms with a large rug and modern or farmhouse furniture."},
}
FINISH = {
 "light": "low-gloss finish with light texture; it hides dark scuffs better than a shiny surface",
 "lightmid": "matte or low-gloss finish; embossed grain makes the look more realistic",
 "mid": "matte finish with embossed grain that follows the pattern (often called embossed-in-register)",
 "dark": "matte finish; gloss shows footprints and dust on darker floors",
 "vdark": "matte finish and a 20 mil wear layer if you can; both make pale scratch lines less obvious",
}

LOOK_ORDER = list(LOOKS)


def room_phrase(room_key: str) -> str:
    r = ROOMS[room_key]
    a, b = r["dims"]
    return f"{r['article']} {a} by {b} {r['label']}"


def numbers(room_key: str):
    a, b = ROOMS[room_key]["dims"]
    net = a * b
    order = math.ceil(net * 1.1)
    boxes = math.ceil(net * 1.1 / BOX_SQFT - 1e-9)
    return net, order, boxes


def esc(s: str) -> str:
    """Escape text for HTML; apostrophes stay readable, double quotes are escaped for attributes."""
    return html.escape(s, quote=False).replace('"', "&quot;")


def page_path(look: str, room: str) -> str:
    return f"{look}-{room}.html"


def build(look_key: str, room_key: str):
    L, R = LOOKS[look_key], ROOMS[room_key]
    name, rp = L["name"], room_phrase(room_key)
    a, b = R["dims"]
    net, order, boxes = numbers(room_key)
    h1 = f"{name} floor for {rp}"
    # "Narrow plank vinyl plank" reads badly, so plank-named looks just say "vinyl"
    kind = "vinyl" if name.endswith("plank") else "vinyl plank"
    title = f"{name} {kind} floor for {rp}"
    desc = f"{name} {kind} for {rp}: {L['short']}. Plan about {order} sq ft with 10% waste (~{boxes} boxes), plus {R['label']} buying tips."
    alt = f"{name} {kind} sample for {rp}: {L['swatch']}"
    tip_tone = TONE_TIPS[(L["tone"], room_key)].format(look=name, look_lc=name.lower())
    tip_pat = PATTERN_TIPS[(L["pattern"], room_key)]
    tip_special = L["special"].format(room=R["label"])
    measure = f"../measure.html?l={a}&amp;w={b}"
    other_rooms = [r for r in ROOM_ORDER if r != room_key]
    similar = L["similar"]

    spec_items = "\n".join(
        f"          <li><strong>{esc(k)}:</strong> {esc(v)}</li>" for k, v in R["spec"]
    )
    guide_items = "\n".join(
        f'          <li><a href="{href}">{esc(text)}</a> — {esc(note)}</li>' for href, text, note in R["guide"]
    )
    same_look = "\n".join(
        f'          <li><a href="{page_path(look_key, r)}">{esc(name)} floor for {esc(room_phrase(r))}</a></li>' for r in other_rooms
    )
    sim_looks = "\n".join(
        f'          <li><a href="{page_path(s, room_key)}">{esc(LOOKS[s]["name"])} floor for {esc(rp)}</a></li>' for s in similar
    )
    main = f"""  <main id="main" class="wrap">
    <section class="card">
      <p class="badge">Floor look</p>
      <h1 class="page-title">{esc(h1)}</h1>
      <p class="pitch">{{PITCH}}</p>
      <p><img src="../textures/{L['_tex']}" alt="{esc(alt)}" width="{L['_w']}" height="{L['_h']}" /></p>
      <div class="nav-row cta-row">
        <a class="btn primary" href="{measure}">Measure this room</a>
        <a class="btn ghost" href="./">All floor looks</a>
      </div>

      <h2>About the {esc(name.lower())} look</h2>
      <p>{esc(L['about'])}</p>

      <h2>Styling {esc(name.lower())} in {esc(rp)}</h2>
      <p>{esc(PAIRS[look_key][room_key])}</p>

      <h2>{esc(R['label'].capitalize())} notes</h2>
      <p>{esc(R['notes'])}</p>

      <h2>{esc(name)} in {esc(rp)}: tips</h2>
      <ul>
        <li>{esc(tip_tone)}</li>
        <li>{esc(tip_pat)}</li>
        <li>{esc(tip_special)}</li>
      </ul>

      <h2>What to buy for this {esc(R['label'])}</h2>
      <ul>
{spec_items}
          <li><strong>Finish:</strong> {esc(FINISH[L['tone']])}</li>
      </ul>

      <div class="guide-site-tools floor-related">
        <h2>Next steps</h2>
        <ul>
          <li><a href="{measure}">Measure your {esc(R['label'])}</a> — the tool opens with {a} by {b} filled in; change it to your real size</li>
{guide_items}
          <li><a href="../guide/tools.html">Tools &amp; materials</a> — tapping block, pull bar, cutter, and spacers</li>
          <li><a href="../diy-install.html">How to install vinyl plank flooring yourself</a></li>
        </ul>
        <h3>{esc(name)} in other rooms</h3>
        <ul>
{same_look}
        </ul>
        <h3>Similar looks for {esc(rp)}</h3>
        <ul>
{sim_looks}
          <li><a href="./">All floor looks by room</a></li>
        </ul>
      </div>
    </section>
  </main>"""
    return dict(h1=h1, title=title, desc=desc, alt=alt, main=main)


def replace_once(text: str, pattern: str, repl: str, path: Path) -> str:
    new, n = re.subn(pattern, lambda m: repl, text, count=1, flags=re.S)
    if n != 1:
        raise SystemExit(f"{path.name}: pattern not found: {pattern[:60]}")
    return new


def main() -> None:
    changed = 0
    for look_key in LOOK_ORDER:
        for room_key in ROOM_ORDER:
            path = FLOORS / page_path(look_key, room_key)
            t = path.read_text(encoding="utf-8")
            img = re.search(r'<img src="\.\./textures/([a-z-]+\.jpg)"[^>]*width="(\d+)" height="(\d+)"', t)
            LOOKS[look_key].update(_tex=img.group(1), _w=img.group(2), _h=img.group(3))
            pitch = re.search(r'<p class="pitch">(.*?)</p>', t, re.S).group(1)
            p = build(look_key, room_key)
            main_html = p["main"].replace("{PITCH}", pitch)
            t2 = replace_once(t, r"  <main id=\"main\" class=\"wrap\">.*?</main>", main_html, path)
            t2 = replace_once(t2, r"<title>.*?</title>", f"<title>{esc(p['title'])}</title>", path)
            for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
                t2 = replace_once(t2, rf'<meta {attr} content="[^"]*" />', f'<meta {attr} content="{esc(p["desc"])}" />', path)
            for attr in ('property="og:title"', 'name="twitter:title"'):
                t2 = replace_once(t2, rf'<meta {attr} content="[^"]*" />', f'<meta {attr} content="{esc(p["title"])}" />', path)
            t2 = replace_once(t2, r'<meta property="og:image:alt" content="[^"]*" />', f'<meta property="og:image:alt" content="{esc(p["alt"])}" />', path)
            t2 = re.sub(r'("@type": "WebPage",\s*"@id": "[^"]+",\s*"name": "[^"]*",\s*"description": )"[^"]*"',
                        lambda m: m.group(1) + '"' + p["desc"].replace('"', '\\"') + '"', t2, count=1)
            if t2 != t:
                path.write_text(t2, encoding="utf-8")
                changed += 1
    print(f"floor pages updated: {changed}")


if __name__ == "__main__":
    main()
