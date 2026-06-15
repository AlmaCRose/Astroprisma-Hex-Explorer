# -*- coding: utf-8 -*-
"""Astroprisma exploration generator.

Implements the Core Book's Exploration Roll system: pick a ring, roll a d6 on
that ring's encounter table, then roll the additional dice each result calls for
(d66 ring events, d6 hostile/neutral categories, planet shape + type + landing +
encounter, satellite type + landing + encounter, d10 faction / settlement control).

All table text lives in astro_data.json (extracted verbatim from the PDF).
"""
import json
import os
import random
import sys

HEX_TYPES = ["Settlement", "Ring Event", "Hostile Encounter",
             "Neutral Encounter", "Planet", "Faction Encounter"]


def _data_path():
    # works both from source and from a PyInstaller one-file bundle
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "astro_data.json")


with open(_data_path(), encoding="utf-8") as _f:
    DATA = json.load(_f)


def d(n):
    return random.randint(1, n)


class Section:
    """One rendered block of the result: a header, an optional dice note,
    and a body (may contain newlines). `level` drives indentation/styling."""
    def __init__(self, header, dice="", body="", level=0):
        self.header = header
        self.dice = dice
        self.body = body
        self.level = level


def _faction_from_table(table, roll):
    for row in table:
        lo, _, hi = row["range"].partition("-")
        lo = int(lo)
        hi = int(hi) if hi else lo
        if lo <= roll <= hi:
            return row["faction"]
    return table[-1]["faction"]


# ---------------------------------------------------------------- encounters

def gen_settlement(ring):
    roll = d(10)
    fac = _faction_from_table(DATA["settlement_control"], roll)
    body = (f"You discover a Settlement controlled by {fac}.\n\n"
            "A space station and safe haven: your Hull and Health are fully "
            "restored on arrival. It offers a Hangar (ships, modules, refuel), "
            "a Wiredoc (healing & cybertech), a Trading Hub, Activities and "
            "Sidequests.\n"
            "(You cannot dock if your Favor with the ruling faction is negative.)")
    return [Section(f"SETTLEMENT — {fac}", f"Control (d10): {roll} → {fac}", body)]


def gen_ring_event(ring):
    re_data = DATA["rings"][ring]["ring_event"]
    a, b = d(6), d(6)
    if a % 2 == 1:
        theme, entries = re_data["odd_theme"], re_data["odd"]
        parity = "odd"
    else:
        theme, entries = re_data["even_theme"], re_data["even"]
        parity = "even"
    text = entries[b - 1]
    dice = f"d66: {a} ({parity} → {theme}) & {b} → event {b}"
    return [Section(f"{ring.upper()} EVENT — {theme}", dice, text)]


def _gen_category_table(block, ring, kind):
    """Hostile / Neutral: d6 -> 1 nothing, 2-6 category; then d6 -> entry."""
    cat_roll = d(6)
    if cat_roll == 1:
        return [Section(f"{kind.upper()} — Nothing",
                        f"{kind} (d6): 1 → no encounter",
                        "You don't encounter anything this time. Leave the tile "
                        "blank and make an Exploration Roll again next time you "
                        "cross it.")]
    cat = block["categories"][cat_roll - 2]
    entry_roll = d(6)
    text = cat["entries"][entry_roll - 1]
    dice = (f"{kind} (d6): {cat_roll} → {cat['name']}   |   "
            f"entry (d6): {entry_roll}")
    return [Section(f"{kind.upper()} — {cat['name']}", dice, text)]


def gen_hostile(ring):
    return _gen_category_table(DATA["hostile"], ring, "Hostile")


def gen_neutral(ring):
    return _gen_category_table(DATA["neutral"], ring, "Neutral")


def _gen_body(world, kind):
    """Generate landing + encounter for a planet/satellite type dict."""
    land = d(6)
    enc = d(6)
    body = (f"{world['desc']}\n\n"
            f"▸ Landing site (d6 {land}): {world['landing'][land - 1]}\n\n"
            f"▸ Exploring (d6 {enc}):\n{world['encounters'][enc - 1]}")
    return body


def gen_satellite(ring, sat_no):
    types = DATA["satellites"]
    t = d(6)
    world = types[t - 1]
    body = _gen_body(world, "satellite")
    return Section(f"SATELLITE {sat_no} — {world['name']}",
                   f"Type (d6): {t} → {world['name']}", body, level=1)


def gen_planet(ring):
    rd = DATA["rings"][ring]
    shape_roll = d(6)
    shape = rd["planet_shape"][shape_roll - 1]
    sections = []
    head = Section(
        f"PLANET — {shape['name']}",
        f"Planet shape (d6): {shape_roll} → {shape['name']} "
        f"({shape['satellites']} satellite(s))",
        shape["desc"])
    sections.append(head)

    # main planet type
    pt = d(6)
    world = DATA["planets"][pt - 1]
    sections.append(Section(f"MAIN PLANET — {world['name']}",
                            f"Planet type (d6): {pt} → {world['name']}",
                            _gen_body(world, "planet"), level=1))
    # satellites
    for i in range(shape["satellites"]):
        sections.append(gen_satellite(ring, i + 1))
    if shape["satellites"]:
        head.body += ("\n\nOn each visit to this hex you may explore the planet "
                      "or one of its satellites (details for all are rolled below).")
    return sections


def gen_faction(ring, favor_positive=True):
    roll = d(10)
    fac = _faction_from_table(DATA["faction_encounter_table"], roll)
    if favor_positive:
        sub = _gen_category_table(DATA["neutral"], ring, "Neutral")[0]
        mood = "Favor ≥ 0 → Neutral encounter"
    else:
        sub = _gen_category_table(DATA["hostile"], ring, "Hostile")[0]
        mood = "Favor < 0 → Hostile encounter"
    head = Section(f"FACTION ENCOUNTER — {fac}",
                   f"Faction (d10): {roll} → {fac}   |   {mood}",
                   f"You cross paths with the {fac}. Resolve the encounter below "
                   f"as it relates to this faction.")
    sub.level = 1
    return [head, sub]


_DISPATCH = {
    "Settlement": gen_settlement,
    "Ring Event": gen_ring_event,
    "Hostile Encounter": gen_hostile,
    "Neutral Encounter": gen_neutral,
    "Planet": gen_planet,
    "Faction Encounter": gen_faction,
}


def generate(ring, hex_type="random", favor_positive=True):
    """Return (exploration_roll_note, hex_type, [Section,...])."""
    if hex_type == "random":
        roll = d(6)
        hex_type = HEX_TYPES[roll - 1]
        label = DATA["rings"][ring]["encounter"][roll - 1]
        note = f"Exploration Roll (d6): {roll} → {label}"
    else:
        note = f"Hex type chosen: {hex_type}"

    if hex_type == "Faction Encounter":
        sections = gen_faction(ring, favor_positive)
    else:
        sections = _DISPATCH[hex_type](ring)
    return note, hex_type, sections


if __name__ == "__main__":
    # quick smoke test
    for ht in ["random"] + HEX_TYPES:
        note, t, secs = generate("Outer Ring", ht)
        print("=" * 60)
        print(note, "|", t)
        for s in secs:
            print(f"  [{'  ' * s.level}{s.header}]  ({s.dice})")
