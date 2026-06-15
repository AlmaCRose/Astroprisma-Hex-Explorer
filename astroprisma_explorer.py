# -*- coding: utf-8 -*-
"""Astroprisma — Hex Explorer

A standalone exploration-roll generator for the Astroprisma TTRPG. Choose the
ring you've moved into and the hex type (or roll it at random), and the app
rolls the game's dice and prints the full generated location, verbatim from the
Core Book tables.

The window has two tabs: the latest roll (Current Roll) and a scrollable log of
everything rolled before it (Past Rolls), where each entry can be copied or
deleted individually, or copied all at once.
"""
import random
import tkinter as tk
from tkinter import ttk

import astro_logic as L

# ----------------------------------------------------------------- palette
BG = "#0b0c1a"          # deep space
PANEL = "#14162b"       # panel
PANEL2 = "#1c1f3a"
INK = "#e9e9f5"         # primary text
DIM = "#8b8fb5"         # secondary text
ACCENT = "#7ad7ff"      # cyan accent
GOLD = "#f4c53b"
EDGE = "#2c2f55"
TXT_BG = "#0e1024"
RING_COLOR = {"Outer Ring": "#ff4fa3",
              "Middle Ring": "#f4c53b",
              "Inner Ring": "#ff5230"}

HEX_CHOICES = ["🎲  Roll Random (d6)"] + L.HEX_TYPES


class StarBanner(tk.Canvas):
    """A small starfield banner with the title."""
    def __init__(self, master, height=92):
        super().__init__(master, height=height, bg=BG, highlightthickness=0)
        self.h = height
        self.bind("<Configure>", self._draw)

    def _draw(self, _evt=None):
        self.delete("all")
        w = self.winfo_width() or 800
        rng = random.Random(7)
        for _ in range(140):
            x, y = rng.randint(0, w), rng.randint(0, self.h)
            r = rng.choice([0, 0, 0, 1, 1])
            c = rng.choice(["#3a3d63", "#4a4e7d", "#6f74a8", "#9aa0d6"])
            self.create_oval(x - r, y - r, x + r, y + r, fill=c, outline="")
        self.create_text(26, self.h // 2 - 8, anchor="w", text="ASTROPRISMA",
                         fill=INK, font=("Bahnschrift", 30, "bold"))
        self.create_text(28, self.h // 2 + 22, anchor="w", text="HEX  EXPLORER",
                         fill=ACCENT, font=("Bahnschrift", 13, "bold"))
        self.create_text(w - 20, self.h // 2, anchor="e",
                         text="STAR SYSTEM  ·  EXPLORATION ROLLS",
                         fill=DIM, font=("Consolas", 9))


class App:
    def __init__(self, root):
        self.root = root
        root.title("Astroprisma — Hex Explorer")
        root.configure(bg=BG)
        root.geometry("880x740")
        root.minsize(700, 580)

        self.current = None        # latest roll record
        self.history = []          # past rolls, most recent first
        self._next_id = 0
        self._hist_widgets = []    # embedded button frames to clean up
        self._skip_confirm = False  # "Do not ask me again" for deletions

        self._init_style()

        StarBanner(root).pack(fill="x", side="top")
        tk.Frame(root, bg=EDGE, height=2).pack(fill="x")

        self._build_controls()
        self._build_footer()
        self._build_tabs()

        self.generate()  # show one on launch

    # -------------------------------------------------------------- styling
    def _init_style(self):
        st = ttk.Style()
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("TCombobox", fieldbackground=PANEL2, background=PANEL2,
                     foreground=INK, arrowcolor=ACCENT, bordercolor=EDGE,
                     lightcolor=EDGE, darkcolor=EDGE, selectbackground=PANEL2,
                     selectforeground=INK, padding=5)
        st.map("TCombobox",
               fieldbackground=[("readonly", PANEL2)],
               foreground=[("readonly", INK)],
               selectbackground=[("readonly", PANEL2)],
               selectforeground=[("readonly", INK)])
        self.root.option_add("*TCombobox*Listbox.background", PANEL2)
        self.root.option_add("*TCombobox*Listbox.foreground", INK)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", BG)
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))

        st.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(8, 6, 8, 0))
        st.configure("TNotebook.Tab", background=PANEL, foreground=DIM,
                     padding=(20, 8), borderwidth=0, font=("Segoe UI", 10, "bold"))
        st.map("TNotebook.Tab",
               background=[("selected", PANEL2)],
               foreground=[("selected", INK)])
        st.configure("Vertical.TScrollbar", background=PANEL2, troughcolor=BG,
                     bordercolor=BG, arrowcolor=DIM)

    def _label(self, parent, text):
        return tk.Label(parent, text=text, bg=PANEL, fg=DIM,
                        font=("Segoe UI", 9, "bold"))

    def _mini_btn(self, parent, text, command, accent=False):
        return tk.Button(parent, text=text, command=command, relief="flat",
                         bg=(ACCENT if accent else PANEL2),
                         fg=(BG if accent else INK),
                         activebackground=("#9be4ff" if accent else EDGE),
                         activeforeground=BG if accent else INK,
                         font=("Segoe UI", 9, "bold" if accent else "normal"),
                         padx=10, pady=3, cursor="hand2", bd=0)

    # -------------------------------------------------------------- controls
    def _build_controls(self):
        bar = tk.Frame(self.root, bg=PANEL, padx=16, pady=14)
        bar.pack(fill="x")

        self._label(bar, "RING").grid(row=0, column=0, sticky="w")
        self.ring_var = tk.StringVar(value="Outer Ring")
        ring_cb = ttk.Combobox(bar, textvariable=self.ring_var, width=16,
                               state="readonly", values=list(RING_COLOR))
        ring_cb.grid(row=1, column=0, padx=(0, 14), sticky="w")
        ring_cb.bind("<<ComboboxSelected>>", lambda e: self._tint_ring())

        self._label(bar, "HEX TYPE").grid(row=0, column=1, sticky="w")
        self.hex_var = tk.StringVar(value=HEX_CHOICES[0])
        ttk.Combobox(bar, textvariable=self.hex_var, width=24, state="readonly",
                     values=HEX_CHOICES).grid(row=1, column=1, padx=(0, 14),
                                              sticky="w")

        self._label(bar, "FAVOR (factions)").grid(row=0, column=2, sticky="w")
        self.favor_var = tk.StringVar(value="Neutral / Positive  (≥ 0)")
        ttk.Combobox(bar, textvariable=self.favor_var, width=22, state="readonly",
                     values=["Neutral / Positive  (≥ 0)", "Negative  (< 0)"]
                     ).grid(row=1, column=2, padx=(0, 14), sticky="w")

        tk.Button(bar, text="◆  GENERATE HEX", command=self.generate,
                  bg=ACCENT, fg=BG, activebackground="#9be4ff",
                  activeforeground=BG, relief="flat",
                  font=("Bahnschrift", 11, "bold"), padx=16, pady=6,
                  cursor="hand2").grid(row=1, column=3, padx=(4, 6))

        bar.grid_columnconfigure(4, weight=1)
        self.ring_pip = tk.Frame(bar, bg=RING_COLOR["Outer Ring"], width=10)
        self.ring_pip.grid(row=0, column=4, rowspan=2, sticky="nse", padx=(8, 0))

    def _tint_ring(self):
        self.ring_pip.configure(bg=RING_COLOR[self.ring_var.get()])

    def _build_footer(self):
        foot = tk.Frame(self.root, bg=BG, padx=14)
        foot.pack(side="bottom", fill="x")
        tk.Label(foot, text="By Almarose", bg=BG, fg=DIM,
                 font=("Segoe UI", 8)).pack(side="right", pady=2)

    # ------------------------------------------------------------------ tabs
    def _build_tabs(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(8, 4))

        # --- Current Roll tab ---
        cur = tk.Frame(self.nb, bg=BG)
        cbar = tk.Frame(cur, bg=BG)
        cbar.pack(fill="x", pady=(6, 4), padx=2)
        self.cur_copy_btn = self._mini_btn(cbar, "⧉  Copy", self._copy_current,
                                           accent=True)
        self.cur_copy_btn.pack(side="right")
        self.cur_txt = self._make_text(cur)
        self.nb.add(cur, text="Current Roll")

        # --- Past Rolls tab ---
        past = tk.Frame(self.nb, bg=BG)
        pbar = tk.Frame(past, bg=BG)
        pbar.pack(fill="x", pady=(6, 4), padx=2)
        self.copyall_btn = self._mini_btn(pbar, "⧉  Copy All", self._copy_all,
                                          accent=True)
        self.copyall_btn.pack(side="right")
        self._mini_btn(pbar, "🗑  Clear History", self._request_clear
                       ).pack(side="right", padx=(0, 6))
        self.past_count = tk.Label(pbar, text="", bg=BG, fg=DIM,
                                   font=("Segoe UI", 9))
        self.past_count.pack(side="left")
        self.hist_txt = self._make_text(past)
        self.nb.add(past, text="Past Rolls (0)")

    def _make_text(self, parent):
        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill="both", expand=True, padx=2, pady=(0, 4))
        txt = tk.Text(wrap, bg=TXT_BG, fg=INK, bd=0, wrap="word",
                      padx=18, pady=14, font=("Segoe UI", 11),
                      spacing1=2, spacing3=4, insertbackground=INK,
                      cursor="arrow")
        sb = ttk.Scrollbar(wrap, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        self._config_tags(txt)
        txt.configure(state="disabled")
        return txt

    def _config_tags(self, t):
        t.tag_configure("roll", foreground=GOLD,
                        font=("Consolas", 10, "bold"), spacing3=6)
        t.tag_configure("h1", font=("Bahnschrift", 15, "bold"),
                        spacing1=10, spacing3=4)
        t.tag_configure("title", font=("Bahnschrift", 13, "bold"),
                        spacing1=4, spacing3=2)
        t.tag_configure("h2", foreground=ACCENT, font=("Bahnschrift", 12, "bold"),
                        spacing1=8, spacing3=2, lmargin1=18, lmargin2=18)
        t.tag_configure("dice", foreground=DIM, font=("Consolas", 9), spacing3=4)
        t.tag_configure("dice2", foreground=DIM, font=("Consolas", 9),
                        spacing3=4, lmargin1=18, lmargin2=18)
        t.tag_configure("body", foreground="#d9dbf0",
                        lmargin1=4, lmargin2=4, spacing3=8)
        t.tag_configure("body2", foreground="#d9dbf0",
                        lmargin1=18, lmargin2=18, spacing3=8)
        t.tag_configure("rule", foreground=EDGE, spacing1=6, spacing3=6)
        t.tag_configure("muted", foreground=DIM, font=("Segoe UI", 11, "italic"))
        for ring, color in RING_COLOR.items():
            t.tag_configure("ring_" + ring, foreground=color)

    # --------------------------------------------------------------- records
    def generate(self):
        ring = self.ring_var.get()
        choice = self.hex_var.get()
        hex_type = "random" if choice.startswith("🎲") else choice
        favor_pos = self.favor_var.get().startswith("Neutral")

        note, resolved, sections = L.generate(ring, hex_type, favor_pos)
        self._tint_ring()

        rec = {"id": self._next_id, "ring": ring, "type": resolved,
               "note": note, "sections": sections,
               "title": f"{ring}  ·  {resolved}"}
        rec["plain"] = self._plain(rec)
        self._next_id += 1

        if self.current is not None:
            self.history.insert(0, self.current)
        self.current = rec

        self._render_current()
        self._render_history()
        self.nb.select(0)

    def _plain(self, rec):
        out = [f"{rec['ring'].upper()} — {rec['type']}", rec["note"], ""]
        for s in rec["sections"]:
            ind = "    " if s.level else ""
            out.append(ind + s.header)
            if s.dice:
                out.append(ind + s.dice)
            if s.body:
                out.extend(ind + ln for ln in s.body.split("\n"))
            out.append("")
        return "\n".join(out).strip()

    def _insert_body(self, t, rec):
        rtag = "ring_" + rec["ring"]
        t.insert("end", rec["note"] + "\n", ("roll",))
        for s in rec["sections"]:
            htag = "h2" if s.level else "h1"
            dtag = "dice2" if s.level else "dice"
            btag = "body2" if s.level else "body"
            t.insert("end", s.header + "\n", (htag,))
            if not s.level:
                ls = t.index("end-2l linestart")
                t.tag_add(rtag, ls, f"{ls} lineend")
            if s.dice:
                t.insert("end", s.dice + "\n", (dtag,))
            if s.body:
                t.insert("end", s.body + "\n", (btag,))

    def _render_current(self):
        t = self.cur_txt
        t.configure(state="normal")
        t.delete("1.0", "end")
        if self.current is None:
            t.insert("end", "Press GENERATE HEX to roll a location.", ("muted",))
        else:
            rec = self.current
            t.insert("end", f"◆ {rec['ring'].upper()}\n", ("h1",))
            ls = t.index("end-2l linestart")
            t.tag_add("ring_" + rec["ring"], ls, f"{ls} lineend")
            self._insert_body(t, rec)
        t.configure(state="disabled")
        t.yview_moveto(0.0)

    def _render_history(self):
        for w in self._hist_widgets:
            w.destroy()
        self._hist_widgets = []

        t = self.hist_txt
        t.configure(state="normal")
        t.delete("1.0", "end")

        n = len(self.history)
        self.nb.tab(1, text=f"Past Rolls ({n})")
        self.past_count.configure(
            text=f"{n} past roll" + ("" if n == 1 else "s"))

        if n == 0:
            t.insert("end", "No past rolls yet. Each new roll pushes the previous "
                            "one here.", ("muted",))
            t.configure(state="disabled")
            return

        for i, rec in enumerate(self.history):
            if i > 0:
                t.insert("end", "─" * 96 + "\n", ("rule",))
            row = tk.Frame(t, bg=TXT_BG)
            cbtn = self._mini_btn(row, "⧉ Copy", lambda: None)
            cbtn.configure(command=lambda r=rec, b=cbtn: self._copy_record(r, b))
            cbtn.pack(side="left", padx=(0, 6))
            dbtn = self._mini_btn(row, "🗑 Delete", lambda: None)
            dbtn.configure(command=lambda r=rec: self._request_delete(r["id"]))
            dbtn.pack(side="left")
            self._hist_widgets.append(row)

            t.window_create("end", window=row)
            t.insert("end", "  " + rec["title"] + "\n",
                     ("title", "ring_" + rec["ring"]))
            self._insert_body(t, rec)

        t.configure(state="disabled")
        t.yview_moveto(0.0)

    # --------------------------------------------------------------- actions
    def _flash(self, btn, normal):
        btn.configure(text="✓  Copied!")
        self.root.after(1100, lambda: btn.configure(text=normal))

    def _to_clip(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _copy_current(self):
        if self.current is None:
            return
        self._to_clip(self.current["plain"])
        self._flash(self.cur_copy_btn, "⧉  Copy")

    def _copy_record(self, rec, btn):
        self._to_clip(rec["plain"])
        old = btn["text"]
        btn.configure(text="✓ Copied")
        self.root.after(1100, lambda: btn.configure(text=old))

    def _copy_all(self):
        if not self.history:
            return
        sep = "\n\n" + "=" * 60 + "\n\n"
        self._to_clip(sep.join(r["plain"] for r in self.history))
        self._flash(self.copyall_btn, "⧉  Copy All")

    def _request_delete(self, rec_id):
        self._confirm("This roll will be removed from your history.",
                      "Delete", lambda: self._delete(rec_id))

    def _request_clear(self):
        n = len(self.history)
        if n == 0:
            return
        msg = f"All {n} past roll" + ("" if n == 1 else "s") + " will be removed."
        self._confirm(msg, "Clear All", self._clear_history)

    def _delete(self, rec_id):
        self.history = [r for r in self.history if r["id"] != rec_id]
        self._render_history()

    def _clear_history(self):
        self.history = []
        self._render_history()

    def _confirm(self, message, confirm_label, on_yes):
        if self._skip_confirm:
            on_yes()
            return
        dlg = tk.Toplevel(self.root, bg=PANEL, padx=22, pady=18)
        dlg.title("Confirm")
        dlg.transient(self.root)
        dlg.resizable(False, False)

        tk.Label(dlg, text="⚠  Are you sure?", bg=PANEL, fg=INK,
                 font=("Bahnschrift", 15, "bold")).pack(anchor="w")
        tk.Label(dlg, text=message, bg=PANEL, fg=DIM, justify="left",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 12))

        ask_var = tk.BooleanVar(value=False)
        tk.Checkbutton(dlg, text="Do not ask me again", variable=ask_var,
                       bg=PANEL, fg=DIM, selectcolor=PANEL2,
                       activebackground=PANEL, activeforeground=INK,
                       font=("Segoe UI", 9), bd=0, highlightthickness=0,
                       cursor="hand2").pack(anchor="w", pady=(0, 14))

        btns = tk.Frame(dlg, bg=PANEL)
        btns.pack(fill="x")

        def yes(_evt=None):
            if ask_var.get():
                self._skip_confirm = True
            dlg.destroy()
            on_yes()

        def no(_evt=None):
            dlg.destroy()

        tk.Button(btns, text=confirm_label, command=yes, bg="#e0533d",
                  fg="white", activebackground="#ff6a52", activeforeground="white",
                  relief="flat", font=("Segoe UI", 10, "bold"),
                  padx=16, pady=5, cursor="hand2").pack(side="right")
        tk.Button(btns, text="Cancel", command=no, bg=PANEL2, fg=INK,
                  activebackground=EDGE, activeforeground=INK, relief="flat",
                  font=("Segoe UI", 10), padx=14, pady=5,
                  cursor="hand2").pack(side="right", padx=(0, 8))

        dlg.bind("<Escape>", no)
        dlg.bind("<Return>", yes)
        dlg.protocol("WM_DELETE_WINDOW", no)

        dlg.update_idletasks()
        rx, ry = self.root.winfo_rootx(), self.root.winfo_rooty()
        rw, rh = self.root.winfo_width(), self.root.winfo_height()
        w, h = dlg.winfo_width(), dlg.winfo_height()
        dlg.geometry(f"+{rx + (rw - w) // 2}+{ry + (rh - h) // 3}")
        dlg.grab_set()
        dlg.focus_set()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
