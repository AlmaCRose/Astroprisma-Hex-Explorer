# -*- coding: utf-8 -*-
"""Build astro_data.json: the full Astroprisma exploration tables, extracted
from the Core Book PDF with column/gap-aware parsing. Dice structure (which
roll selects what, category/theme names, satellite counts) was read from the
page artwork; narrative text is pulled verbatim from the PDF text layer."""
import json
import re
import extract_entries as E

# Insert the space the PDF's tight kerning dropped after sentence punctuation.
# Only fires when a lowercase letter is followed by . , ! ? and then a letter,
# so page refs (p.57), decimals (v2.0) and acronyms (W.A.R.G.) are untouched.
_PUNCT = re.compile(r'([a-z])([.,!?])([A-Za-z])')
# The Challenge-Roll die icon drops out of the text layer, leaving one or two
# stray lowercase x's in front of ROLL prompts and ALL-CAPS action headers
# ("xROLL TECH", "xREPAIR THE GENERATOR"). Strip them.
_XROLL = re.compile(r'(?<![A-Za-z])x{1,2}(?=[A-Z]{2,})')
# The Serum currency icon is a glyph the PDF text layer drops, leaving an
# amount with a trailing space before punctuation (e.g. "for 120 ."). In these
# trade contexts the amount is Serum, so restore the unit name.
_SERUM = re.compile(r'(\d) ([.,])')


def clean(s):
    s = _XROLL.sub('', s)
    s = _SERUM.sub(r'\1 Serum\2', s)
    s = _PUNCT.sub(r'\1\2 \3', s)
    return s


def _cleanlist(lst):
    return [clean(x) for x in lst]


def cats(idx, x0, x1, y0, n_expected, sizes_expected=6,
         entry_gap=1.5, cat_gap=15.0):
    c = E.categories(idx, x0, x1, y0, entry_gap=entry_gap, cat_gap=cat_gap)
    assert len(c) == n_expected, f'p{idx}: got {len(c)} cats, want {n_expected}: {[len(x) for x in c]}'
    for cat in c:
        assert len(cat) == sizes_expected, f'p{idx}: cat size {[len(x) for x in c]}, want {sizes_expected}'
    return c


def six_blocks(idx):
    """Planet/satellite encounter page: 3 left + 3 right -> 6 d6 entries."""
    left = E.blocks(idx, 0, 205, 40)
    right = E.blocks(idx, 205, 9999, 40)
    assert len(left) == 3 and len(right) == 3, f'p{idx}: blocks {len(left)}/{len(right)}'
    return left + right


FACTION_TABLE = [
    {"range": "1-2", "faction": "Corsair Syndicate"},
    {"range": "3-4", "faction": "W.A.R.G."},
    {"range": "5-6", "faction": "Medusa Sector"},
    {"range": "7-8", "faction": "I.S.F."},
    {"range": "9-10", "faction": "Synth Arch"},
]

# ---- Rings: encounter d6, planet-shape d6, ring-event page + themes ----
RING_ENCOUNTER = ["Settlement", "{ring} Event", "Hostile Encounter",
                  "Neutral Encounter", "Planet", "Faction Encounter"]

RINGS_META = {
    "Outer Ring": {
        "color": "#FF4FA3",
        "blurb": "The largest and most hostile ring. Asteroid fields make travel "
                 "difficult, and remote formations hide space pirates and outlaws.",
        "shapes": [  # one per d6 face (1..6)
            ("Two Moons", 2, "Medium-sized planet with two satellites orbiting around its gravitational core."),
            ("Two Moons", 2, "Medium-sized planet with two satellites orbiting around its gravitational core."),
            ("Ringed Planet", 0, "Large planet that features a series of asteroid or ice rings orbiting around it."),
            ("Ringed Planet", 0, "Large planet that features a series of asteroid or ice rings orbiting around it."),
            ("Giant Planet", 0, "These planets are of unusually large size and mass, and lack satellites of any kind."),
            ("Giant Planet", 0, "These planets are of unusually large size and mass, and lack satellites of any kind."),
        ],
        "event_page": 66, "odd_theme": "Pirate Hideout", "even_theme": "Asteroid Sea",
    },
    "Middle Ring": {
        "color": "#F4C53B",
        "blurb": "Located between the other two rings. Abundant life and water; in the "
                 "Old World, human settlements and exocolonies were established here. "
                 "Abandoned star cruisers and research outposts are common.",
        "shapes": [
            ("One Moon", 1, "Medium-sized planet that has a single observable satellite in orbit."),
            ("One Moon", 1, "Medium-sized planet that has a single observable satellite in orbit."),
            ("Two Moons", 2, "Small-sized planet with two satellites orbiting around its gravitational core."),
            ("Two Moons", 2, "Small-sized planet with two satellites orbiting around its gravitational core."),
            ("Medium Planet", 0, "Medium planet with no satellites, commonly found in the Circumstellar Habitable Zone."),
            ("Medium Planet", 0, "Medium planet with no satellites, commonly found in the Circumstellar Habitable Zone."),
        ],
        "event_page": 68, "odd_theme": "Star Cruiser", "even_theme": "Research Outpost",
    },
    "Inner Ring": {
        "color": "#FF5230",
        "blurb": "The zone bordering the central star. Extremely high temperatures and "
                 "frequent solar flares. Ancient helios farms built to capture the "
                 "star's energy are found here.",
        "shapes": [
            ("Small Planet", 0, "Small-sized planet with no orbiting moons, commonly found near the system's star."),
            ("Small Planet", 0, "Small-sized planet with no orbiting moons, commonly found near the system's star."),
            ("One Moon", 1, "Medium-sized planet that has a single observable satellite in orbit."),
            ("One Moon", 1, "Medium-sized planet that has a single observable satellite in orbit."),
            ("Void Planet", 0, "Whether the result of a supernatural event or a human experiment, its surface is partly corrupted by void."),
            ("Void Planet", 0, "Whether the result of a supernatural event or a human experiment, its surface is partly corrupted by void."),
        ],
        "event_page": 70, "odd_theme": "Solar Flare", "even_theme": "Helios Farm",
    },
}

HOSTILE_CATS = ["Outlaws & Looters", "Space Pirates", "Mercenaries",
                "Spacefarers", "Faction Battles"]
NEUTRAL_CATS = ["Derelict Ships", "Cargo Transport", "Civilian Transport",
                "Radio Signals", "Supranatural Events"]

# planet type -> (landing page, landing col side, encounter page)
PLANET_TYPES = [
    ("Gaian", 75, "right", 77, "Dry, rocky worlds dominated by sand deserts. Despite their arid nature they were heavily settled by the ancient empires for precious jewels found below the surface; many were terraformed."),
    ("Calorian", 75, "right", 78, "Rocky and barren, one of the hardest environments to survive in due to regular earthquakes, seismic activity and high temperatures. Their surface is rough, often red and maroon from iron-oxide dust."),
    ("Vaporian", 75, "right", 79, "Hydrogen, helium and other chemicals form a thick layer of gas making up most of their mass. Landing or exploring the surface is impossible due to colossal, never-ending storms of toxic gas and vapor."),
    ("Aquarian", 76, "left", 80, "Planets with a high amount of water in their hydrosphere. Oceans cover most of their surface; some present islands or archipelagos, others are completely covered in water."),
    ("Sylvanian", 76, "left", 81, "Biodiverse worlds with humid atmospheres and rich flora and fauna. Lush rainforests, jungles, shallow inland seas and swamps. High predatory-life density leaves most still unsettled."),
    ("Ecumenopolis", 76, "left", 82, "The greatest marvels of the Old World: massive planets whose surface is entirely consumed by urban sprawl. All natural life was destroyed for the megacity; now they are deserted orbiting ghost towns."),
]

# satellite type -> (landing page, landing col side, encounter page)
SATELLITE_TYPES = [
    ("Asteroid", 83, "right", 85, "Minor planets of varying sizes composed of rock, metal and even ice. Hundreds of thousands lie unexplored, making them perfect spots for illegal activity; pirate hideouts are commonly hidden in large asteroid formations."),
    ("Crater Moon", 83, "right", 86, "The most common type of moon. Rocky bodies with a very thin atmosphere unable to stop meteorites, so their barren surface is covered with large craters and impacts."),
    ("Nuclear Moon", 83, "right", 87, "Moons with high radiation, from failed terraforming or damage from nuclear weapons in past wars. Some have toxic, threatening ecosystems of dangerous mutated alien life."),
    ("Frost Moon", 84, "left", 88, "Natural satellites composed of ice and water; the most common water-bearing bodies. Hard to traverse due to cold temperatures and geysers. Some hold a subsurface ocean of liquid water."),
    ("Volcanic Moon", 84, "left", 89, "Characterized by extreme volcanic activity and high temperatures, housing hundreds of active volcanoes. Rivers of lava flow across their surface, sometimes forming oceans of molten rock, iron and sulfur."),
    ("Hollow Moon", 84, "left", 90, "Man-made orbiting megastructures with a metallic outer layer and a hollow core. Their interiors often housed population centers or entertainment facilities, with breathable air and large gardens."),
]


def build():
    data = {"factions": [f["faction"] for f in FACTION_TABLE],
            "settlement_control": FACTION_TABLE,
            "faction_encounter_table": FACTION_TABLE,
            "rings": {}, "hostile": {}, "neutral": {},
            "planets": [], "satellites": []}

    # Rings
    for ring, meta in RINGS_META.items():
        ev = cats(meta["event_page"], 40, 9999, 40, 2)  # [odd6, even6]
        data["rings"][ring] = {
            "color": meta["color"],
            "blurb": meta["blurb"],
            "encounter": [s.format(ring=ring.replace(" Ring", " Ring"))
                          if "{ring}" in s else s for s in RING_ENCOUNTER],
            "planet_shape": [{"name": n, "satellites": s, "desc": d}
                             for (n, s, d) in meta["shapes"]],
            "ring_event": {
                "odd_theme": meta["odd_theme"], "even_theme": meta["even_theme"],
                "odd": ev[0], "even": ev[1],
            },
        }
    # fix the ring-event label for encounter list
    data["rings"]["Outer Ring"]["encounter"][1] = "Outer Ring Event"
    data["rings"]["Middle Ring"]["encounter"][1] = "Middle Ring Event"
    data["rings"]["Inner Ring"]["encounter"][1] = "Inner Ring Event"

    # Hostile: page 71 cats 2,3 ; page 72 cats 4,5,6
    h = cats(71, 40, 9999, 205, 2) + cats(72, 40, 9999, 60, 3)
    assert len(h) == 5
    data["hostile"]["categories"] = [{"name": HOSTILE_CATS[i], "entries": h[i]}
                                     for i in range(5)]

    # Neutral: page 73 cats 2,3 ; page 74 cats 4,5,6
    n = cats(73, 40, 9999, 205, 2) + cats(74, 40, 9999, 60, 3)
    assert len(n) == 5
    data["neutral"]["categories"] = [{"name": NEUTRAL_CATS[i], "entries": n[i]}
                                    for i in range(5)]

    # Planets
    for name, lpage, side, epage, desc in PLANET_TYPES:
        x = (180, 9999) if side == "right" else (0, 195)
        c = cats(lpage, x[0], x[1], 60 if side == "right" else 75, 3)
        landing = [c[0], c[1], c[2]]  # placeholder; pick correct type column below
        data["planets"].append({"name": name, "desc": desc,
                                "landing": None, "encounters": six_blocks(epage),
                                "_lpage": lpage, "_side": side})
    _fill_landing(data["planets"], PLANET_TYPES)

    # Satellites
    for name, lpage, side, epage, desc in SATELLITE_TYPES:
        data["satellites"].append({"name": name, "desc": desc,
                                   "landing": None, "encounters": six_blocks(epage),
                                   "_lpage": lpage, "_side": side})
    _fill_landing(data["satellites"], SATELLITE_TYPES)

    # strip helpers
    for arr in (data["planets"], data["satellites"]):
        for t in arr:
            t.pop("_lpage", None)
            t.pop("_side", None)
    return data


def _fill_landing(arr, types):
    """Each landing page holds 3 types' landing tables stacked; assign by order."""
    # group types by page
    bypage = {}
    for i, (name, lpage, side, epage, desc) in enumerate(types):
        bypage.setdefault((lpage, side), []).append(i)
    for (lpage, side), idxs in bypage.items():
        x = (180, 9999) if side == "right" else (0, 195)
        y0 = 60 if side == "right" else 75
        c = cats(lpage, x[0], x[1], y0, 3)
        for slot, type_i in enumerate(idxs):
            arr[type_i]["landing"] = c[slot]


def deep_clean(o):
    if isinstance(o, str):
        return clean(o)
    if isinstance(o, list):
        return [deep_clean(x) for x in o]
    if isinstance(o, dict):
        return {k: deep_clean(v) for k, v in o.items()}
    return o


if __name__ == "__main__":
    d = deep_clean(build())
    with open("astro_data.json", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print("astro_data.json written OK")
    print("rings:", list(d["rings"]))
    print("planets:", [p["name"] for p in d["planets"]])
    print("satellites:", [s["name"] for s in d["satellites"]])
    print("sample hostile cat:", d["hostile"]["categories"][1]["name"],
          "->", d["hostile"]["categories"][1]["entries"][0][:50])
