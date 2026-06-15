# Astroprisma — Hex Explorer

A standalone Windows app for generating **exploration hexes** while playing the
Astroprisma TTRPG (Core Book v2.0). Pick the ring you've moved into and the hex
type — or let it roll at random — and the app performs the game's dice rolls and
prints the full generated location, with the encounter/planet/satellite text
taken verbatim from the Core Book tables.

## Run it

Double-click **`dist/Astroprisma Hex Explorer.exe`**. No Python install required —
everything (tables included) is bundled into the single executable.

## How it works

1. **RING** — choose Outer / Middle / Inner. Each ring has its own encounter,
   planet-shape and ring-event tables.
2. **HEX TYPE** — leave on *Roll Random (d6)* to make a real Exploration Roll, or
   force a specific result (Settlement, Ring Event, Hostile, Neutral, Planet,
   Faction Encounter).
3. **FAVOR** — only matters for Faction Encounters: ≥ 0 Favor yields a neutral
   encounter, negative Favor yields a hostile one (per the rulebook).
4. Press **GENERATE HEX**. Every die roll is shown next to its result, so you can
   follow exactly what was rolled.

The generator implements the book's full chain of rolls:

| Result | Dice rolled |
|---|---|
| Settlement | d10 → controlling faction |
| Ring Event | d66 (odd/even die → theme, second die → 1 of 6 events) |
| Hostile / Neutral | d6 (1 = nothing, 2–6 = category) → d6 entry |
| Planet | ring planet-shape d6 → planet type d6 → landing d6 → encounter d6, plus a full roll-out for each satellite |
| Satellite | type d6 → landing d6 → encounter d6 |
| Faction Encounter | d10 → faction, then a neutral or hostile encounter based on Favor |

## Source files

| File | Purpose |
|---|---|
| `astroprisma_explorer.py` | The Tkinter GUI |
| `astro_logic.py` | Dice-rolling / generation engine |
| `astro_data.json` | All table text, extracted from the PDF |
| `build_data.py` | Rebuilds `astro_data.json` from the Core Book PDF |
| `extract_entries.py` | Column/gap-aware PDF table parser used by `build_data.py` |
| `app.ico` | Application icon |

## Rebuilding

Regenerate the table data (needs `pdfplumber`, reads the PDF in `Resources/`):

```
python build_data.py
```

Rebuild the executable (needs `pyinstaller`):

```
python -m PyInstaller --onefile --windowed --name "Astroprisma Hex Explorer" \
    --icon app.ico --add-data "astro_data.json;." astroprisma_explorer.py
```

## Notes & limitations

- Encounter/planet/satellite **titles** in the book are drawn as outlined
  graphics (not real text), so they aren't reproduced; the full body text of
  each entry is. The dice number that selected the entry is always shown.
- A few currency icons (Serum) are not in the PDF's text layer; bare trade
  amounts are labelled "Serum", which is correct in those contexts.
- Settlement output lists which faction controls it plus its standard
  facilities; it is a hub rather than a random encounter.
