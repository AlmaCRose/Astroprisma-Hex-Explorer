# -*- coding: utf-8 -*-
"""Column + vertical-gap aware extractor for Astroprisma table pages.

Within an entry, lines are ~0.3pt apart; between entries ~4pt; between
categories/sections ~15pt+. We segment on those thresholds.
"""
import pdfplumber

PDF = 'Resources/Astroprisma - [Crescent Chimera] - Astroprisma - Core Book v2.0 (Pages) [OEF][2025-03-24].pdf'
_pdf = pdfplumber.open(PDF)


def lines_of(words):
    words = sorted(words, key=lambda w: (round(w['top'] / 3), w['x0']))
    lines, cur, cur_top = [], [], None
    for w in words:
        if cur_top is None or abs(w['top'] - cur_top) <= 3:
            cur.append(w)
            cur_top = w['top'] if cur_top is None else cur_top
        else:
            lines.append(cur)
            cur, cur_top = [w], w['top']
    if cur:
        lines.append(cur)
    out = []
    for ln in lines:
        ln = sorted(ln, key=lambda w: w['x0'])
        out.append({'top': min(w['top'] for w in ln),
                    'bottom': max(w['bottom'] for w in ln),
                    'text': ' '.join(w['text'] for w in ln)})
    out.sort(key=lambda l: l['top'])
    return out


def _box_lines(page_idx, x0, x1, y0, y1):
    p = _pdf.pages[page_idx]
    ws = [w for w in p.extract_words(x_tolerance=1.2)
          if x0 <= w['x0'] < x1 and y0 <= w['top'] < y1]
    return lines_of(ws)


def entries(page_idx, x0=0, x1=9999, y0=0, y1=9999, entry_gap=2.5):
    """Flat list of entries in a column box."""
    ls = _box_lines(page_idx, x0, x1, y0, y1)
    if not ls:
        return []
    out, cur = [], [ls[0]['text']]
    for i in range(1, len(ls)):
        g = ls[i]['top'] - ls[i - 1]['bottom']
        if g > entry_gap:
            out.append(' '.join(cur))
            cur = [ls[i]['text']]
        else:
            cur.append(ls[i]['text'])
    out.append(' '.join(cur))
    return out


def categories(page_idx, x0=0, x1=9999, y0=0, y1=9999,
               entry_gap=2.5, cat_gap=15.0):
    """List of categories, each a list of entries."""
    ls = _box_lines(page_idx, x0, x1, y0, y1)
    if not ls:
        return []
    cats, cur_cat, cur_entry = [], [], [ls[0]['text']]
    for i in range(1, len(ls)):
        g = ls[i]['top'] - ls[i - 1]['bottom']
        if g > cat_gap:
            cur_cat.append(' '.join(cur_entry))
            cats.append(cur_cat)
            cur_cat, cur_entry = [], [ls[i]['text']]
        elif g > entry_gap:
            cur_cat.append(' '.join(cur_entry))
            cur_entry = [ls[i]['text']]
        else:
            cur_entry.append(ls[i]['text'])
    cur_cat.append(' '.join(cur_entry))
    cats.append(cur_cat)
    return cats


def blocks(page_idx, x0=0, x1=9999, y0=0, y1=9999,
           split_gap=15.0, newline_gap=1.6):
    """Split a column into blocks at big gaps; preserve internal structure
    by inserting newlines at medium (structural) gaps. Used for the
    planet/satellite encounter pages where each block is one d6 encounter."""
    ls = _box_lines(page_idx, x0, x1, y0, y1)
    if not ls:
        return []
    out, cur = [], [ls[0]['text']]
    for i in range(1, len(ls)):
        g = ls[i]['top'] - ls[i - 1]['bottom']
        if g > split_gap:
            out.append('\n'.join(cur))
            cur = [ls[i]['text']]
        elif g > newline_gap:
            cur.append(ls[i]['text'])          # new physical line -> new \n part
        else:
            cur[-1] = cur[-1] + ' ' + ls[i]['text']  # continuation of same line
    out.append('\n'.join(cur))
    return out


if __name__ == '__main__':
    import sys
    idx = int(sys.argv[1])
    x0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0
    x1 = float(sys.argv[3]) if len(sys.argv) > 3 else 9999
    y0 = float(sys.argv[4]) if len(sys.argv) > 4 else 0
    cats = categories(idx, x0, x1, y0)
    print(f'== page {idx} x[{x0},{x1}] y>{y0} -> {len(cats)} categories ==')
    for ci, cat in enumerate(cats):
        print(f'--- CATEGORY {ci+1} ({len(cat)} entries) ---')
        for i, e in enumerate(cat):
            print(f'  [{i+1}] {e}')
