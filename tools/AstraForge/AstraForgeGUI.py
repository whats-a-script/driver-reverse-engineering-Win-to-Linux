# SPDX-License-Identifier: LicenseRef-AstraForge-Proprietary
# Copyright (C) 2026 linuxwifi7 (Charles Ellison). All Rights Reserved.
# Proprietary and confidential. Unauthorized copying, distribution, or
# modification of this file, via any medium, is strictly prohibited.
# See LICENSE at the repository root for full terms.
#
# AstraForge GUI — Windows-to-Linux Driver Reverse Engineering Toolkit
# Version: 1.2.0

import sys
import os
import threading
import json
import subprocess
from pathlib import Path
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ── ensure AstraForge.py is importable ──────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
import AstraForge as af

# ── theme definitions ─────────────────────────────────────────────────────────

THEMES = {
    "Dark (Default)": {
        # Windows 11 Mica Dark palette
        "BG": "#202020", "BG2": "#2d2d2d", "ACCENT": "#0078d4",
        "ACCENT_HVR": "#106ebe", "FG": "#ffffff", "FG_DIM": "#9d9d9d",
        "SUCCESS": "#6ccb5f", "WARNING": "#fce100", "ERROR": "#ff4343",
        "INFO": "#60cdff", "LOG_BG": "#161616",
    },
    "Windows 11 Light": {
        "BG": "#f3f3f3", "BG2": "#ffffff", "ACCENT": "#0078d4",
        "ACCENT_HVR": "#106ebe", "FG": "#1a1a1a", "FG_DIM": "#666666",
        "SUCCESS": "#107c10", "WARNING": "#7a7700", "ERROR": "#c42b1c",
        "INFO": "#0078d4", "LOG_BG": "#f9f9f9",
    },
    "Pride (LGBTQ+)": {
        "BG":        "#111111",   # near-black — lets flag colors shine
        "BG2":       "#1c1c1c",
        "ACCENT":    "#FF8C00",   # orange stripe — primary action
        "ACCENT_HVR":"#cc7000",
        "FG":        "#ffffff",
        "FG_DIM":    "#bbbbbb",
        "SUCCESS":   "#008026",   # green stripe
        "WARNING":   "#FFED00",   # yellow stripe
        "ERROR":     "#E40303",   # red stripe
        "INFO":      "#004DFF",   # blue stripe
        "LOG_BG":    "#0a0a0a",
    },
    "Cyberpunk": {
        "BG": "#0d0221", "BG2": "#1a0442", "ACCENT": "#00ff9f",
        "ACCENT_HVR": "#00cc7f", "FG": "#ffffff", "FG_DIM": "#9b59b6",
        "SUCCESS": "#00ff9f", "WARNING": "#ff00ff", "ERROR": "#ff073a",
        "INFO": "#00e5ff", "LOG_BG": "#050011",
    },
    "Monokai": {
        "BG": "#272822", "BG2": "#3e3d32", "ACCENT": "#a6e22e",
        "ACCENT_HVR": "#7fbf1f", "FG": "#f8f8f2", "FG_DIM": "#75715e",
        "SUCCESS": "#a6e22e", "WARNING": "#e6db74", "ERROR": "#f92672",
        "INFO": "#66d9e8", "LOG_BG": "#1e1f1c",
    },
    "Ocean": {
        "BG": "#0f2027", "BG2": "#203a43", "ACCENT": "#2c7da0",
        "ACCENT_HVR": "#1a5c78", "FG": "#e0f7fa", "FG_DIM": "#80cbc4",
        "SUCCESS": "#4db6ac", "WARNING": "#ffb74d", "ERROR": "#ef5350",
        "INFO": "#4fc3f7", "LOG_BG": "#0a1a20",
    },
    "Solarized": {
        "BG": "#002b36", "BG2": "#073642", "ACCENT": "#268bd2",
        "ACCENT_HVR": "#1a6da3", "FG": "#839496", "FG_DIM": "#586e75",
        "SUCCESS": "#859900", "WARNING": "#b58900", "ERROR": "#dc322f",
        "INFO": "#2aa198", "LOG_BG": "#001f28",
    },
}

# Pride flag stripe colors (shown in title bar for Pride theme)
PRIDE_STRIPES = ["#E40303", "#FF8C00", "#FFED00", "#008026", "#004DFF", "#750787"]

# Active palette — mutable, updated by _apply_color_theme()
BG         = THEMES["Dark (Default)"]["BG"]
BG2        = THEMES["Dark (Default)"]["BG2"]
ACCENT     = THEMES["Dark (Default)"]["ACCENT"]
ACCENT_HVR = THEMES["Dark (Default)"]["ACCENT_HVR"]
FG         = THEMES["Dark (Default)"]["FG"]
FG_DIM     = THEMES["Dark (Default)"]["FG_DIM"]
SUCCESS    = THEMES["Dark (Default)"]["SUCCESS"]
WARNING    = THEMES["Dark (Default)"]["WARNING"]
ERROR      = THEMES["Dark (Default)"]["ERROR"]
INFO       = THEMES["Dark (Default)"]["INFO"]
LOG_BG     = THEMES["Dark (Default)"]["LOG_BG"]
ACTIVE_THEME_NAME = "Dark (Default)"

FONT       = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_MONO  = ("Cascadia Code", 9)   # Win11 terminal font; falls back gracefully
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_LABEL = ("Segoe UI", 8, "bold")  # section header caps


def _apply_color_theme(name: str):
    """Update module-level colour globals from the named theme."""
    global BG, BG2, ACCENT, ACCENT_HVR, FG, FG_DIM
    global SUCCESS, WARNING, ERROR, INFO, LOG_BG, ACTIVE_THEME_NAME
    t = THEMES.get(name, THEMES["Dark (Default)"])
    BG         = t["BG"];  BG2        = t["BG2"]
    ACCENT     = t["ACCENT"];  ACCENT_HVR = t["ACCENT_HVR"]
    FG         = t["FG"];  FG_DIM     = t["FG_DIM"]
    SUCCESS    = t["SUCCESS"];  WARNING = t["WARNING"]
    ERROR      = t["ERROR"];  INFO     = t["INFO"]
    LOG_BG     = t["LOG_BG"]
    ACTIVE_THEME_NAME = name
    # Persist choice
    cfg = af.load_config()
    cfg["theme"] = name
    af.save_config(cfg)


# Load saved theme on import
_saved_theme = af.load_config().get("theme", "Dark (Default)")
if _saved_theme in THEMES:
    _apply_color_theme(_saved_theme)


# ── helpers ───────────────────────────────────────────────────────────────────

def _pad(w, px=8, py=4):
    w.pack_configure(padx=px, pady=py)
    return w


def _label(parent, text, font=FONT, fg=FG, bg=BG2, anchor="w", **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg,
                    anchor=anchor, **kw)


def _sep(parent, bg=BG):
    return tk.Frame(parent, bg=ACCENT, height=1)


# ═══════════════════════════════════════════════════════════════════════════════
# Main application window
# ═══════════════════════════════════════════════════════════════════════════════

class AstraForgeApp:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AstraForge — Windows → Linux Driver Converter")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(1080, 720)

        self.canonical: dict | None = None
        self._analysis_done = False

        # StringVars
        self.sv_input   = tk.StringVar()
        self.sv_output  = tk.StringVar()
        self.sv_vendor  = tk.StringVar()
        self.sv_device  = tk.StringVar()
        self.sv_modname = tk.StringVar()   # editable module/driver name

        # Restore last paths from AstraForge config
        cfg = af.load_config()
        self.sv_input.set(cfg.get("windows_raw", ""))
        self.sv_output.set(cfg.get("driver_out", ""))

        self._build_ui()
        self._patch_log()

        # Load saved paths into UI
        if self.sv_input.get():
            self._on_input_change()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        root = self.root
        root.configure(bg=BG)

        # ── menu bar ───────────────────────────────────────────────────────────
        menubar = tk.Menu(root, bg=BG2, fg=FG, activebackground=ACCENT,
                          activeforeground="#fff", relief="flat", bd=0)

        theme_menu = tk.Menu(menubar, tearoff=0, bg=BG2, fg=FG,
                             activebackground=ACCENT, activeforeground="#fff")
        for tname in THEMES:
            theme_menu.add_command(
                label=("✓ " if tname == ACTIVE_THEME_NAME else "   ") + tname,
                command=lambda n=tname: self._change_theme(n))
        menubar.add_cascade(label="Theme", menu=theme_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=BG2, fg=FG,
                            activebackground=ACCENT, activeforeground="#fff")
        help_menu.add_command(label="About AstraForge…", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        root.configure(menu=menubar)

        is_pride = ACTIVE_THEME_NAME == "Pride (LGBTQ+)"

        # ── pride flag rainbow bar (thick, prominent) ──────────────────────────
        if is_pride:
            flag = tk.Frame(root, height=30)
            flag.pack(fill="x")
            flag.pack_propagate(False)
            for colour in PRIDE_STRIPES:
                tk.Frame(flag, bg=colour).pack(
                    side="left", fill="both", expand=True)

        # ── title bar ──────────────────────────────────────────────────────────
        title_bar = tk.Frame(root, bg=BG, pady=14)
        title_bar.pack(fill="x", padx=20)

        if is_pride:
            for i, char in enumerate("AstraForge"):
                tk.Label(title_bar, text=char, font=FONT_TITLE,
                         fg=PRIDE_STRIPES[i % len(PRIDE_STRIPES)],
                         bg=BG).pack(side="left")
            tk.Label(title_bar, text="  Windows → Linux Driver Converter",
                     font=("Segoe UI", 11), fg=FG_DIM, bg=BG).pack(side="left")
        else:
            tk.Label(title_bar, text="AstraForge",
                     font=FONT_TITLE, fg=ACCENT, bg=BG).pack(side="left")
            tk.Label(title_bar, text="  Windows → Linux Driver Converter",
                     font=("Segoe UI", 11), fg=FG_DIM, bg=BG).pack(side="left")

        # version badge
        tk.Label(title_bar, text=" v1.2 ", font=("Segoe UI", 8),
                 fg=BG, bg=ACCENT).pack(side="right", padx=(0, 4))

        # ── divider ────────────────────────────────────────────────────────────
        tk.Frame(root, bg=BG2, height=1).pack(fill="x")

        # ── main body ─────────────────────────────────────────────────────────
        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True)

        # Left panel — fixed width card
        left_wrap = tk.Frame(body, bg=BG2, bd=0)
        left_wrap.pack(side="left", fill="y", padx=0, pady=0)
        left = tk.Frame(left_wrap, bg=BG2, width=460)
        left.pack(side="left", fill="both", expand=False, padx=0, pady=0)
        left.pack_propagate(False)

        # Thin separator between panels
        tk.Frame(body, bg=BG, width=1).pack(side="left", fill="y")

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=16, pady=12)

        self._build_left(left)
        self._build_right(right)

        # ── status bar ─────────────────────────────────────────────────────────
        tk.Frame(root, bg=BG2, height=1).pack(fill="x", side="bottom")
        status_frame = tk.Frame(root, bg=BG, pady=5)
        status_frame.pack(fill="x", side="bottom")
        self._status_dot = tk.Label(status_frame, text="●", font=("Segoe UI", 8),
                                    fg=FG_DIM, bg=BG)
        self._status_dot.pack(side="left", padx=(12, 4))
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(status_frame, textvariable=self.status_var,
                 font=FONT_SMALL, fg=FG_DIM, bg=BG, anchor="w").pack(side="left")

    def _build_left(self, parent):
        # Scrollable inner frame
        canvas = tk.Canvas(parent, bg=BG2, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG2)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(inner_id, width=canvas.winfo_width())
        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(inner_id, width=e.width))

        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        P = 16  # left/right padding constant

        # ── STEP 1 ─────────────────────────────────────────────────────────────
        self._section(inner, "Step 1 — Windows Driver Input", pad=P)

        self._entry_row(inner, self.sv_input, browse_fn=self._browse_input,
                        placeholder="Path to folder from collect_windows.ps1", pad=P)

        sub_row = tk.Frame(inner, bg=BG2)
        sub_row.pack(fill="x", padx=P, pady=(2, 6))
        tk.Button(sub_row, text="⊕  Scan folder for drivers…",
                  font=FONT_SMALL, fg=INFO, bg=BG2, relief="flat",
                  activebackground=BG, activeforeground=INFO,
                  cursor="hand2", bd=0,
                  command=self._open_scan_dialog).pack(side="left")
        if sys.platform == "win32":
            tk.Button(sub_row, text="Run collect_windows.ps1",
                      font=FONT_SMALL, fg=FG_DIM, bg=BG2, relief="flat",
                      activebackground=BG, cursor="hand2", bd=0,
                      command=self._run_collect).pack(side="right")

        # Advanced options
        adv_frame = tk.Frame(inner, bg=BG, bd=0)
        adv_frame.pack(fill="x", padx=P, pady=(0, 6))
        tk.Label(adv_frame, text="OPTIONAL OVERRIDES",
                 font=FONT_LABEL, fg=FG_DIM, bg=BG).pack(anchor="w", pady=(4, 2))
        adv = tk.Frame(adv_frame, bg=BG2, bd=0)
        adv.pack(fill="x")
        self._labeled_entry(adv, "Vendor ID", self.sv_vendor, "e.g. 0x14C3")
        self._labeled_entry(adv, "Device ID", self.sv_device, "e.g. 0x7927")

        analyse_color = PRIDE_STRIPES[1] if ACTIVE_THEME_NAME == "Pride (LGBTQ+)" else ACCENT
        self.btn_analyse = self._action_btn(
            inner, "  Analyse Driver", self._run_analyse, analyse_color, pad=P)

        # ── divider ────────────────────────────────────────────────────────────
        tk.Frame(inner, bg=BG, height=1).pack(fill="x", pady=10)

        # ── Device Info ────────────────────────────────────────────────────────
        self._section(inner, "Device Info", pad=P)

        info_card = tk.Frame(inner, bg=BG, bd=0)
        info_card.pack(fill="x", padx=P, pady=(0, 6))
        info_card.columnconfigure(1, weight=1)

        self.info_vars = {}
        fields = [
            ("Description", "description"),
            ("Type",        "_type"),
            ("Bus",         "bus"),
            ("Vendor ID",   "vendor_id"),
            ("Device ID",   "device_id"),
            ("Subsystem",   "subsystem_id"),
            ("Version",     "version"),
            ("Provider",    "provider"),
            ("Bands",       "bands"),
            ("Modes",       "modes"),
        ]
        for row_idx, (label, key) in enumerate(fields):
            tk.Label(info_card, text=label,
                     font=FONT_SMALL, fg=FG_DIM, bg=BG,
                     anchor="w", width=11).grid(row=row_idx, column=0,
                                                sticky="w", padx=(0, 8), pady=2)
            sv = tk.StringVar(value="—")
            self.info_vars[key] = sv
            tk.Label(info_card, textvariable=sv,
                     font=FONT_MONO, fg=INFO, bg=BG,
                     anchor="w").grid(row=row_idx, column=1, sticky="ew", pady=2)

        # ── divider ────────────────────────────────────────────────────────────
        tk.Frame(inner, bg=BG, height=1).pack(fill="x", pady=10)

        # ── STEP 2 ─────────────────────────────────────────────────────────────
        self._section(inner, "Step 2 — Generate Linux Driver", pad=P)

        self._entry_row(inner, self.sv_output, browse_fn=self._browse_output,
                        placeholder="Output folder for .c / .h / Makefile / Kconfig",
                        pad=P)

        name_row = tk.Frame(inner, bg=BG2)
        name_row.pack(fill="x", padx=P, pady=(0, 6))
        tk.Label(name_row, text="Module name:", font=FONT_SMALL,
                 fg=FG_DIM, bg=BG2, width=13, anchor="w").pack(side="left")
        self._name_entry = tk.Entry(
            name_row, textvariable=self.sv_modname,
            font=FONT_MONO, fg=SUCCESS, bg=BG,
            insertbackground=FG, relief="flat", bd=0, width=22)
        self._name_entry.pack(side="left", ipady=4)
        tk.Label(name_row, text="(auto-filled — editable)",
                 font=FONT_SMALL, fg=FG_DIM, bg=BG2).pack(side="left", padx=6)

        gen_color = PRIDE_STRIPES[4] if ACTIVE_THEME_NAME == "Pride (LGBTQ+)" else "#107c10"
        self.btn_generate = self._action_btn(
            inner, "  Generate Linux Driver", self._run_generate,
            gen_color, state="disabled", pad=P)

        self.btn_save_kb = self._action_btn(
            inner, "  Save to Knowledge Base", self._save_to_kb,
            "#7c3aed", state="disabled", pad=P)

        # ── Code Preview ───────────────────────────────────────────────────────
        tk.Frame(inner, bg=BG, height=1).pack(fill="x", pady=(10, 0))
        self._section(inner, "Generated .c Preview", pad=P)
        self.preview_text = scrolledtext.ScrolledText(
            inner, font=("Cascadia Code", 8), fg=FG, bg=LOG_BG,
            relief="flat", bd=0, state="disabled", wrap="none", height=16)
        self.preview_text.pack(fill="both", expand=True, padx=P, pady=(0, 12))

    def _build_right(self, parent):
        self._section(parent, "Output Log")

        self.log_text = scrolledtext.ScrolledText(
            parent, font=("Cascadia Code", 9), fg=FG, bg=LOG_BG,
            insertbackground=FG, relief="flat", bd=0,
            state="disabled", wrap="word",
        )
        self.log_text.pack(fill="both", expand=True, pady=(0, 4))

        if ACTIVE_THEME_NAME == "Pride (LGBTQ+)":
            self.log_text.tag_config("info",    foreground=PRIDE_STRIPES[4])
            self.log_text.tag_config("success", foreground=PRIDE_STRIPES[3])
            self.log_text.tag_config("warning", foreground=PRIDE_STRIPES[2])
            self.log_text.tag_config("error",   foreground=PRIDE_STRIPES[0])
            self.log_text.tag_config("dim",     foreground=PRIDE_STRIPES[5])
        else:
            self.log_text.tag_config("info",    foreground=INFO)
            self.log_text.tag_config("success", foreground=SUCCESS)
            self.log_text.tag_config("warning", foreground=WARNING)
            self.log_text.tag_config("error",   foreground=ERROR)
            self.log_text.tag_config("dim",     foreground=FG_DIM)

        btn_row = tk.Frame(parent, bg=BG)
        btn_row.pack(fill="x", pady=(2, 0))

        for txt, cmd, side in [("Clear log", self._clear_log, "left"),
                                ("Open output folder", self._open_output, "right")]:
            b = tk.Button(btn_row, text=txt, font=FONT_SMALL,
                          fg=FG_DIM, bg=BG, relief="flat", bd=0,
                          activebackground=BG2, activeforeground=FG,
                          cursor="hand2", padx=4, pady=2, command=cmd)
            b.pack(side=side)
            b.bind("<Enter>", lambda e, w=b: w.configure(fg=FG))
            b.bind("<Leave>", lambda e, w=b: w.configure(fg=FG_DIM))
            if txt == "Open output folder":
                self.btn_open = b
                self.btn_open.configure(state="disabled")

    # ── widget helpers ─────────────────────────────────────────────────────────

    def _section(self, parent, title: str, pad: int = 0):
        row = tk.Frame(parent, bg=BG2 if parent.cget("bg") == BG2 else BG)
        bg  = row.cget("bg")
        row.pack(fill="x", padx=pad, pady=(12, 4))

        if ACTIVE_THEME_NAME == "Pride (LGBTQ+)":
            words = title.split()
            for i, word in enumerate(words):
                tk.Label(row, text=word + " ", font=FONT_LABEL,
                         fg=PRIDE_STRIPES[i % len(PRIDE_STRIPES)],
                         bg=bg).pack(side="left")
        else:
            # Accent bar + uppercase label (Win11 style)
            tk.Frame(row, bg=ACCENT, width=3, height=14).pack(
                side="left", fill="y", padx=(0, 7))
            tk.Label(row, text=title.upper(), font=FONT_LABEL,
                     fg=FG_DIM, bg=bg, anchor="w").pack(side="left")

    def _entry_row(self, parent, sv, browse_fn, placeholder="", pad: int = 6):
        bg = BG2 if parent.cget("bg") == BG2 else BG2
        frame = tk.Frame(parent, bg=bg)
        frame.pack(fill="x", padx=pad, pady=(0, 4))

        # Border simulation: 1px accent-colored outer frame
        border = tk.Frame(frame, bg=FG_DIM, bd=0)
        border.pack(fill="x", expand=True, side="left")
        entry = tk.Entry(border, textvariable=sv,
                         font=FONT_MONO, fg=FG, bg=LOG_BG,
                         insertbackground=FG, relief="flat", bd=6)
        entry.pack(fill="x", expand=True, ipady=3)

        def _focus_in(_):
            border.configure(bg=ACCENT)
        def _focus_out(_):
            border.configure(bg=FG_DIM)
        entry.bind("<FocusIn>",  _focus_in)
        entry.bind("<FocusOut>", _focus_out)

        if placeholder and not sv.get():
            self._add_placeholder(entry, sv, placeholder)

        browse_btn = tk.Button(frame, text="Browse",
                               font=FONT_SMALL, fg="#fff", bg=ACCENT,
                               activebackground=ACCENT_HVR, activeforeground="#fff",
                               relief="flat", cursor="hand2", bd=0, padx=12, pady=7,
                               command=browse_fn)
        browse_btn.pack(side="left", padx=(4, 0))
        browse_btn.bind("<Enter>", lambda e: browse_btn.configure(bg=ACCENT_HVR))
        browse_btn.bind("<Leave>", lambda e: browse_btn.configure(bg=ACCENT))

    def _labeled_entry(self, parent, label, sv, hint=""):
        row = tk.Frame(parent, bg=parent.cget("bg"))
        row.pack(fill="x", padx=8, pady=3)
        tk.Label(row, text=label, font=FONT_SMALL,
                 fg=FG_DIM, bg=row.cget("bg"),
                 width=11, anchor="w").pack(side="left")
        e = tk.Entry(row, textvariable=sv, font=FONT_MONO,
                     fg=FG, bg=LOG_BG, insertbackground=FG,
                     relief="flat", bd=4, width=16)
        e.pack(side="left", ipady=3)
        if hint:
            tk.Label(row, text=hint, font=FONT_SMALL,
                     fg=FG_DIM, bg=row.cget("bg")).pack(side="left", padx=8)

    def _action_btn(self, parent, text, cmd, color, state="normal", pad: int = 16):
        btn = tk.Button(
            parent, text=text, font=FONT_BOLD,
            fg="#ffffff", bg=color,
            activeforeground="#ffffff", activebackground=ACCENT_HVR,
            relief="flat", cursor="hand2", bd=0,
            padx=16, pady=10, state=state, command=cmd,
        )
        btn.pack(fill="x", padx=pad, pady=(4, 0))

        def _enter(_):
            if str(btn["state"]) != "disabled":
                btn.configure(bg=ACCENT_HVR)
        def _leave(_):
            if str(btn["state"]) != "disabled":
                btn.configure(bg=color)
        btn.bind("<Enter>", _enter)
        btn.bind("<Leave>", _leave)
        return btn

    def _add_placeholder(self, entry, sv, text):
        def on_focus_in(_):
            if sv.get() == text:
                sv.set("")
                entry.configure(fg=FG)
        def on_focus_out(_):
            if not sv.get():
                sv.set(text)
                entry.configure(fg=FG_DIM)
        sv.set(text)
        entry.configure(fg=FG_DIM)
        entry.bind("<FocusIn>",  on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    # ── log helpers ────────────────────────────────────────────────────────────

    def _patch_log(self):
        """Redirect af.log() to the GUI log panel (thread-safe)."""
        original = af.log
        app = self

        def gui_log(msg: str):
            original(msg)
            app.root.after(0, app._append_log, msg)

        af.log = gui_log

    def _append_log(self, msg: str, tag: str = ""):
        self.log_text.configure(state="normal")
        ts = f"[{datetime.now().strftime('%H:%M:%S')}]  "

        if not tag:
            low = msg.lower()
            if "error" in low or "fail" in low or "could not" in low:
                tag = "error"
            elif "warning" in low or "warn" in low or "not found" in low:
                tag = "warning"
            elif "written" in low or "complete" in low or "passed" in low:
                tag = "success"
            elif "loading" in low or "extracting" in low or "skipping" in low:
                tag = "dim"
            else:
                tag = "info"

        self.log_text.insert("end", ts, "dim")
        self.log_text.insert("end", msg + "\n", tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _status(self, msg: str, level: str = ""):
        self.status_var.set(msg)
        low = msg.lower()
        if level == "error" or "fail" in low or "error" in low:
            dot_color = ERROR
        elif level == "success" or "done" in low or "complete" in low:
            dot_color = SUCCESS
        elif "analysing" in low or "generating" in low:
            dot_color = WARNING
        else:
            dot_color = FG_DIM
        if hasattr(self, "_status_dot"):
            self._status_dot.configure(fg=dot_color)
        self.root.update_idletasks()

    # ── info panel ─────────────────────────────────────────────────────────────

    def _populate_info(self, canonical: dict):
        dev  = canonical.get("device", {})
        drv  = canonical.get("driver", {})
        caps = drv.get("capabilities", {})
        dtype = af.detect_device_type(canonical)

        self.info_vars["description"].set(dev.get("description") or "—")
        self.info_vars["_type"].set(
            f"{dtype}  [{af.DEVICE_TYPES.get(dtype, '')}]")
        self.info_vars["bus"].set(dev.get("bus") or "pci")
        self.info_vars["vendor_id"].set(dev.get("vendor_id") or "—")
        self.info_vars["device_id"].set(dev.get("device_id") or "—")
        self.info_vars["subsystem_id"].set(dev.get("subsystem_id") or "—")
        self.info_vars["version"].set(drv.get("version") or "—")
        self.info_vars["provider"].set(drv.get("provider") or "—")
        self.info_vars["bands"].set(
            "  ".join(caps.get("bands") or []) or "—")
        self.info_vars["modes"].set(
            "  ".join(caps.get("modes") or []) or "—")

    def _clear_info(self):
        for sv in self.info_vars.values():
            sv.set("—")

    # ── browse callbacks ───────────────────────────────────────────────────────

    def _browse_input(self):
        folder = filedialog.askdirectory(
            title="Select Windows driver data folder",
            initialdir=self.sv_input.get() or Path.home(),
        )
        if folder:
            self.sv_input.set(folder)
            self._on_input_change()

    def _browse_output(self):
        folder = filedialog.askdirectory(
            title="Select output folder for Linux driver",
            initialdir=self.sv_output.get() or Path.home(),
        )
        if folder:
            self.sv_output.set(folder)

    def _on_input_change(self):
        """Auto-suggest output path when input changes."""
        inp = self.sv_input.get()
        if inp and Path(inp).exists():
            out = str(Path(inp).parent / "linux_driver_generated")
            if not self.sv_output.get():
                self.sv_output.set(out)

    # ── collect_windows.ps1 runner ─────────────────────────────────────────────

    def _run_collect(self):
        script = Path(__file__).parent.parent.parent / "collect_windows.ps1"
        if not script.exists():
            messagebox.showerror("Not found",
                                 f"collect_windows.ps1 not found at:\n{script}")
            return
        try:
            subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass",
                 "-File", str(script)],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            self._append_log(
                f"Launched collect_windows.ps1 in a new console window.", "info")
            self._append_log(
                "Once it finishes, select its output folder above.", "dim")
        except Exception as e:
            messagebox.showerror("Launch failed", str(e))

    # ── analyse ────────────────────────────────────────────────────────────────

    def _run_analyse(self):
        inp = self.sv_input.get().strip()
        if not inp or not Path(inp).exists():
            messagebox.showwarning("No folder",
                "Please select a valid Windows driver data folder first.")
            return

        self._clear_info()
        self.btn_analyse.configure(state="disabled", text="Analysing…")
        self.btn_generate.configure(state="disabled")
        self.btn_save_kb.configure(state="disabled")
        self._status("Analysing driver data…")
        self._analysis_done = False

        threading.Thread(target=self._analyse_thread,
                         args=(inp,), daemon=True).start()

    def _analyse_thread(self, raw_path: str):
        try:
            vendor_id = self.sv_vendor.get().strip() or None
            device_id = self.sv_device.get().strip() or None

            raw = Path(raw_path)
            chipset = raw.name
            canonical = af.empty_canonical("windows", chipset)

            af.extract_device_from_windows(
                af.load_json(raw / "pci_device.json"), canonical,
                vendor_id, device_id)
            af.extract_driver_package_windows(
                af.load_json(raw / "driver_package.json"), canonical,
                vendor_id, device_id)
            af.extract_driver_files_windows(
                af.load_json(raw / "driver_files.json"), canonical)
            af.extract_capabilities_from_netsh_windows(
                af.load_text(raw / "netsh_wlan_drivers.txt"), canonical)
            af.extract_systeminfo_windows(
                af.load_text(raw / "systeminfo.txt"), canonical)

            self.canonical = canonical
            self._analysis_done = True

            # Save detected input path to config
            cfg = af.load_config()
            cfg["windows_raw"] = raw_path
            af.save_config(cfg)

            self.root.after(0, self._analyse_done)

        except Exception as exc:
            self.root.after(0, self._analyse_error, str(exc))

    def _analyse_done(self):
        self._populate_info(self.canonical)
        # Auto-fill module name from derived chipset name
        chipset = self.canonical["device"].get("name") or \
                  af._derive_chipset_name(self.canonical, fallback="driver")
        self.sv_modname.set(chipset)
        dtype  = af.detect_device_type(self.canonical)
        subsys = af.DEVICE_TYPES.get(dtype, dtype)
        self._append_log(
            f"Analysis complete.  Type: {dtype}  ({subsys})", "success")
        self._append_log(f"Module name set to: {chipset}  (edit above to rename)", "dim")
        self.btn_analyse.configure(state="normal", text="Analyse Driver")
        self.btn_generate.configure(state="normal")
        self.btn_save_kb.configure(state="normal")
        self._status(f"Ready to generate — {dtype} driver detected.")

    def _analyse_error(self, msg: str):
        self._append_log(f"Analysis failed: {msg}", "error")
        self.btn_analyse.configure(state="normal", text="Analyse Driver")
        self._status("Analysis failed.  Check the log.")
        messagebox.showerror("Analysis failed", msg)

    # ── generate ───────────────────────────────────────────────────────────────

    def _run_generate(self):
        if not self._analysis_done or not self.canonical:
            messagebox.showwarning("No data",
                "Please run Analyse first.")
            return

        out = self.sv_output.get().strip()
        if not out:
            messagebox.showwarning("No output folder",
                "Please choose an output folder for the Linux driver.")
            return

        self.btn_generate.configure(state="disabled", text="Generating…")
        self.btn_analyse.configure(state="disabled")
        self._status("Generating Linux driver…")

        name_override = self.sv_modname.get().strip()
        threading.Thread(target=self._generate_thread,
                         args=(out, name_override), daemon=True).start()

    def _generate_thread(self, out_dir: str, name_override: str):
        try:
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            af.generate_linux_driver(self.canonical, out_dir,
                                     name_override=name_override)

            # Save config
            cfg = af.load_config()
            cfg["driver_out"] = out_dir
            af.save_config(cfg)

            self.root.after(0, self._generate_done, out_dir)

        except Exception as exc:
            self.root.after(0, self._generate_error, str(exc))

    def _generate_done(self, out_dir: str):
        chipset = af._c_ident(
            self.canonical["device"].get("name") or "unknown")
        self._append_log(
            f"Driver skeleton written to: {out_dir}", "success")
        self._append_log(
            f"Files: {chipset}.c  {chipset}.h  Makefile  Kconfig  install.sh", "success")
        self._append_log(
            "To build on Linux:  cd <output>  &&  make", "info")
        self.btn_generate.configure(state="normal", text="Generate Linux Driver")
        self.btn_analyse.configure(state="normal")
        self.btn_open.configure(state="normal")
        self._last_output = out_dir
        self._status(f"Done!  Driver written to {out_dir}")

        # Load generated .c into preview panel
        c_file = Path(out_dir) / f"{chipset}.c"
        if c_file.exists():
            try:
                src = c_file.read_text(encoding="utf-8", errors="replace")
                self.preview_text.configure(state="normal")
                self.preview_text.delete("1.0", "end")
                self.preview_text.insert("end", src)
                self.preview_text.configure(state="disabled")
            except Exception:
                pass

        if messagebox.askyesno("Done!",
                f"Linux driver skeleton generated.\n\n"
                f"Output: {out_dir}\n\n"
                f"Open the output folder now?"):
            self._open_output()

    def _save_to_kb(self):
        if not self.canonical:
            return
        try:
            out = af.kb_save_device(self.canonical)
            self._append_log(f"Saved to Knowledge Base: {out}", "success")
            self._status(f"KB entry saved: {out.name}")
            messagebox.showinfo("Knowledge Base", f"Device saved to KB:\n{out}")
        except Exception as exc:
            self._append_log(f"KB save failed: {exc}", "error")
            messagebox.showerror("KB Save Failed", str(exc))

    def _generate_error(self, msg: str):
        self._append_log(f"Generation failed: {msg}", "error")
        self.btn_generate.configure(state="normal", text="Generate Linux Driver")
        self.btn_analyse.configure(state="normal")
        self._status("Generation failed.  Check the log.")
        messagebox.showerror("Generation failed", msg)

    # ── theme switching ────────────────────────────────────────────────────────

    def _show_about(self):
        win = tk.Toplevel(self.root)
        win.title("About AstraForge")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg=BG)
        tk.Label(win, text="AstraForge", font=("Segoe UI", 18, "bold"),
                 bg=BG, fg=ACCENT).pack(pady=(20, 2))
        tk.Label(win, text="Windows-to-Linux Driver Reverse Engineering Toolkit",
                 font=("Segoe UI", 10), bg=BG, fg=FG).pack()
        tk.Label(win, text="Version 1.2.0", font=("Segoe UI", 9),
                 bg=BG, fg=FG).pack(pady=(8, 0))
        tk.Label(win, text="Copyright © 2026 linuxwifi7 (Charles Ellison)",
                 font=("Segoe UI", 9), bg=BG, fg=FG).pack()
        tk.Label(win, text="All Rights Reserved — Proprietary Software",
                 font=("Segoe UI", 9), bg=BG, fg=FG).pack()
        tk.Label(win, text="Generated driver output licensed under GPL-2.0-only",
                 font=("Segoe UI", 8), bg=BG, fg=FG_DIM).pack(pady=(4, 0))
        tk.Frame(win, bg=ACCENT, height=1).pack(fill="x", padx=20, pady=12)
        tk.Label(win, text="github.com/linuxwifi7/TP-link-wifi-MT7927-reverse-engineer",
                 font=("Segoe UI", 9), bg=BG, fg=ACCENT).pack()
        tk.Button(win, text="Close", command=win.destroy,
                  bg=ACCENT, fg="#fff", relief="flat",
                  padx=20, pady=6, cursor="hand2").pack(pady=16)

    def _change_theme(self, name: str):
        _apply_color_theme(name)
        # Preserve live state across rebuild
        saved_canonical      = self.canonical
        saved_analysis_done  = self._analysis_done
        saved_input          = self.sv_input.get()
        saved_output         = self.sv_output.get()
        saved_vendor         = self.sv_vendor.get()
        saved_device         = self.sv_device.get()
        saved_modname        = self.sv_modname.get()

        # Destroy all children and rebuild
        for child in self.root.winfo_children():
            child.destroy()

        # Re-init StringVars with saved values
        self.sv_input   = tk.StringVar(value=saved_input)
        self.sv_output  = tk.StringVar(value=saved_output)
        self.sv_vendor  = tk.StringVar(value=saved_vendor)
        self.sv_device  = tk.StringVar(value=saved_device)
        self.sv_modname = tk.StringVar(value=saved_modname)

        self._build_ui()
        self._patch_log()

        # Restore state
        self.canonical      = saved_canonical
        self._analysis_done = saved_analysis_done
        if saved_canonical:
            self._populate_info(saved_canonical)
            self.btn_generate.configure(state="normal")
            self.btn_save_kb.configure(state="normal")
        if saved_modname:
            self.sv_modname.set(saved_modname)

        self._append_log(f"Theme changed to: {name}", "info")
        self._status(f"Theme: {name}")

    # ── open output folder ─────────────────────────────────────────────────────

    def _open_output(self):
        path = getattr(self, "_last_output", self.sv_output.get())
        if path and Path(path).exists():
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        else:
            messagebox.showwarning("Not found",
                "Output folder does not exist yet.")

    # ── scan dialog ────────────────────────────────────────────────────────────

    def _open_scan_dialog(self):
        ScanDialog(self.root, on_select=self._on_driver_selected)

    def _on_driver_selected(self, entry: dict):
        """Called by ScanDialog when user loads a driver entry."""
        file_type = entry.get("file_type", "INF")
        src_path  = Path(entry.get("inf_path", ""))
        src_dir   = str(src_path.parent) if src_path.exists() else ""

        # Populate input path with the containing folder
        if src_dir:
            self.sv_input.set(src_dir)
            self._on_input_change()

        # Populate ID override fields
        self.sv_vendor.set(entry.get("vendor_id") or "")
        self.sv_device.set(entry.get("device_id") or "")

        # --- Build / update canonical ---
        if self.canonical and file_type in ("DLL", "SYS"):
            # Enrich existing canonical with firmware refs + device IDs from binary
            fw_refs  = entry.get("firmware_refs", [])
            dev_ids  = entry.get("device_ids", [])
            existing_fw = self.canonical["driver"].get("firmware", []) or []
            for ref in fw_refs:
                if ref not in existing_fw:
                    existing_fw.append(ref)
            self.canonical["driver"]["firmware"] = existing_fw

            if dev_ids and not self.canonical["device"].get("vendor_id"):
                parsed = af._parse_hw_id(dev_ids[0])
                if parsed:
                    self.canonical["device"].update(parsed)

            self._populate_info(self.canonical)
            self._append_log(
                f"Enriched canonical from {src_path.name}: "
                f"{len(fw_refs)} firmware refs, {len(dev_ids)} device IDs",
                "success")
            self._status(f"Canonical enriched from {file_type}")
            return

        # --- Fresh canonical from INF (or DLL with no existing canonical) ---
        canonical = af.empty_canonical("windows", "unknown")
        canonical["device"]["description"]  = entry.get("description")
        canonical["device"]["class"]        = entry.get("class")
        canonical["device"]["bus"]          = entry.get("bus", "pci")
        canonical["device"]["vendor_id"]    = entry.get("vendor_id")
        canonical["device"]["device_id"]    = entry.get("device_id")
        canonical["device"]["subsystem_id"] = entry.get("subsystem_id")
        canonical["device"]["revision"]     = entry.get("revision")
        canonical["driver"]["version"]      = entry.get("version")
        canonical["driver"]["provider"]     = (entry.get("provider") or
                                               entry.get("company"))
        canonical["driver"]["firmware"]     = entry.get("firmware_refs", [])

        # Embed DLL/SYS device IDs into files list
        if file_type in ("DLL", "SYS"):
            canonical["driver"]["files"] = [src_path.name]

        # Derive proper chipset name from extracted IDs
        chipset = af._derive_chipset_name(
            canonical, fallback=Path(src_dir).name if src_dir else "unknown")
        canonical["device"]["name"] = chipset

        self.canonical       = canonical
        self._analysis_done  = True

        self._populate_info(canonical)
        self.btn_generate.configure(state="normal")
        dtype = af.detect_device_type(canonical)
        self._append_log(
            f"Loaded [{file_type}] {entry.get('description')}  "
            f"[{entry.get('vendor_id')}:{entry.get('device_id')}]  "
            f"type={dtype}", "success")
        self._status(f"Driver loaded from scan — {dtype}")


# ═══════════════════════════════════════════════════════════════════════════════
# Scan dialog
# ═══════════════════════════════════════════════════════════════════════════════

class ScanDialog(tk.Toplevel):
    """
    Modal window that scans a folder tree for .inf files, lists every
    device found, and lets the user select one to load into the main window.
    """

    COLS = [
        ("Type",          42),
        ("Description",  260),
        ("Class/Arch",    80),
        ("Bus",           42),
        ("Vendor ID",     72),
        ("Device ID",     72),
        ("Version",       90),
        ("Provider",     120),
        ("File",         200),
    ]

    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.title("Scan for Drivers")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(980, 520)
        self.grab_set()          # modal

        self._on_select = on_select
        self._results: list = []
        self._scan_folder = tk.StringVar()

        self._build()
        self._centre(parent)

    def _centre(self, parent):
        self.update_idletasks()
        pw = parent.winfo_x(); ph = parent.winfo_y()
        w, h = 980, 560
        x = pw + (parent.winfo_width()  - w) // 2
        y = ph + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        # ── header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG, pady=8)
        hdr.pack(fill="x", padx=14)
        tk.Label(hdr, text="Scan Folder for Drivers",
                 font=FONT_BOLD, fg=ACCENT, bg=BG).pack(side="left")

        # ── folder picker row ─────────────────────────────────────────────────
        pick = tk.Frame(self, bg=BG)
        pick.pack(fill="x", padx=14, pady=(0,6))

        entry = tk.Entry(pick, textvariable=self._scan_folder,
                         font=FONT_MONO, fg=FG, bg="#13131f",
                         insertbackground=FG, relief="flat", bd=4)
        entry.pack(side="left", fill="x", expand=True, ipady=4)

        tk.Button(pick, text="Browse…",
                  font=FONT_SMALL, fg=FG, bg=ACCENT,
                  activebackground=ACCENT_HVR, relief="flat",
                  cursor="hand2", padx=10,
                  command=self._browse).pack(side="left", padx=(4,0))

        # Recursive checkbox
        self._recursive = tk.BooleanVar(value=True)
        tk.Checkbutton(pick, text="Recursive",
                       variable=self._recursive,
                       font=FONT_SMALL, fg=FG_DIM, bg=BG,
                       activebackground=BG,
                       selectcolor=BG2).pack(side="left", padx=8)

        tk.Button(pick, text="Scan",
                  font=FONT_BOLD, fg="#fff", bg="#059669",
                  activebackground="#047857", relief="flat",
                  cursor="hand2", padx=14, pady=6,
                  command=self._start_scan).pack(side="left", padx=(4,0))

        # ── filter bar ────────────────────────────────────────────────────────
        filt = tk.Frame(self, bg=BG)
        filt.pack(fill="x", padx=14, pady=(0,4))
        tk.Label(filt, text="Filter:", font=FONT_SMALL,
                 fg=FG_DIM, bg=BG).pack(side="left")
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        tk.Entry(filt, textvariable=self._filter_var,
                 font=FONT_MONO, fg=FG, bg="#13131f",
                 insertbackground=FG, relief="flat", bd=3,
                 width=36).pack(side="left", padx=6, ipady=3)
        self._count_var = tk.StringVar(value="No results yet.")
        tk.Label(filt, textvariable=self._count_var,
                 font=FONT_SMALL, fg=FG_DIM, bg=BG).pack(side="right")

        # ── treeview ──────────────────────────────────────────────────────────
        tree_frame = tk.Frame(self, bg=BG)
        tree_frame.pack(fill="both", expand=True, padx=14, pady=(0,6))

        style = ttk.Style(self)
        style.configure("Scan.Treeview",
                         background="#0d0d1a", foreground=FG,
                         fieldbackground="#0d0d1a",
                         rowheight=22, font=FONT_MONO)
        style.configure("Scan.Treeview.Heading",
                         background=BG2, foreground=FG_DIM, font=FONT_SMALL)
        style.map("Scan.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "#fff")])

        cols = [c[0] for c in self.COLS]
        self.tree = ttk.Treeview(tree_frame, columns=cols,
                                  show="headings", style="Scan.Treeview",
                                  selectmode="extended")   # Ctrl/Shift multi-select

        for name, width in self.COLS:
            self.tree.heading(name, text=name,
                              command=lambda c=name: self._sort_by(c))
            self.tree.column(name, width=width, minwidth=40, stretch=False)
        self.tree.column("Description", stretch=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal",
                             command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
                             xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>",          lambda _: self._load_selected())
        self.tree.bind("<<TreeviewSelect>>",  lambda _: self._on_selection_change())
        self.tree.bind("<Control-a>",         lambda _: self._select_all())
        self.tree.bind("<Control-A>",         lambda _: self._select_all())

        # ── progress bar ──────────────────────────────────────────────────────
        self._progress = ttk.Progressbar(self, mode="indeterminate",
                                          length=200)

        # ── bottom buttons ─────────────────────────────────────────────────────
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(fill="x", padx=14, pady=(0,10))

        self.btn_load = tk.Button(
            btn_row, text="Load Selected",
            font=FONT_BOLD, fg="#fff", bg=ACCENT,
            activebackground=ACCENT_HVR, relief="flat",
            cursor="hand2", padx=14, pady=6,
            state="disabled",
            command=self._load_selected)
        self.btn_load.pack(side="left", padx=(0, 6))

        self.btn_batch = tk.Button(
            btn_row, text="Generate All Selected…",
            font=FONT_BOLD, fg="#fff", bg="#059669",
            activebackground="#047857", relief="flat",
            cursor="hand2", padx=14, pady=6,
            state="disabled",
            command=self._batch_generate)
        self.btn_batch.pack(side="left")

        self._sel_label = tk.Label(btn_row, text="",
                                   font=FONT_SMALL, fg=INFO, bg=BG)
        self._sel_label.pack(side="left", padx=10)

        tk.Button(btn_row, text="Close",
                  font=FONT_SMALL, fg=FG_DIM, bg=BG,
                  relief="flat", cursor="hand2",
                  command=self.destroy).pack(side="right")

    # ── scan ──────────────────────────────────────────────────────────────────

    def _browse(self):
        folder = filedialog.askdirectory(
            title="Select folder to scan for .inf driver files",
            parent=self,
        )
        if folder:
            self._scan_folder.set(folder)

    def _start_scan(self):
        folder = self._scan_folder.get().strip()
        if not folder or not Path(folder).exists():
            messagebox.showwarning("No folder",
                "Please select a valid folder to scan.", parent=self)
            return

        # Clear previous results
        for row in self.tree.get_children():
            self.tree.delete(row)
        self._results = []
        self._count_var.set("Scanning…")
        self.btn_load.configure(state="disabled")

        # Show progress bar
        self._progress.pack(fill="x", padx=14, pady=(0,4))
        self._progress.start(12)

        threading.Thread(
            target=self._scan_thread,
            args=(folder, self._recursive.get()),
            daemon=True).start()

    def _scan_thread(self, folder: str, recursive: bool):
        def progress(path, found):
            self.after(0, self._count_var.set,
                       f"Scanning… {found} found  |  {Path(path).name}")

        results = af.scan_for_drivers(folder, recursive=recursive,
                                       progress_cb=progress)
        self.after(0, self._scan_done, results)

    def _scan_done(self, results: list):
        self._progress.stop()
        self._progress.pack_forget()
        self._results = results
        self._apply_filter()
        n = len(results)
        self._count_var.set(f"{n} device{'s' if n != 1 else ''} found.")
        if n == 0:
            messagebox.showinfo("No drivers found",
                "No .inf files with recognised device IDs were found "
                "in the selected folder.", parent=self)

    # ── filter + display ──────────────────────────────────────────────────────

    def _apply_filter(self):
        filt = self._filter_var.get().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)

        shown = 0
        for entry in self._results:
            ft       = entry.get("file_type", "INF")
            cls_arch = entry.get("arch") if ft in ("DLL", "SYS") \
                       else entry.get("class", "")
            # DLLs/SYS show firmware refs count in description suffix
            desc = entry.get("description", "")
            if ft in ("DLL", "SYS"):
                n_fw  = len(entry.get("firmware_refs", []))
                n_ids = len(entry.get("device_ids", []))
                hints = []
                if n_ids:
                    hints.append(f"{n_ids} ID{'s' if n_ids > 1 else ''}")
                if n_fw:
                    hints.append(f"{n_fw} fw")
                if hints:
                    desc = f"{desc}  [{', '.join(hints)}]"

            values = (
                ft,
                desc,
                cls_arch or "",
                (entry.get("bus") or "pci").upper(),
                entry.get("vendor_id") or "",
                entry.get("device_id") or "",
                entry.get("version") or "",
                entry.get("provider") or entry.get("company") or "",
                Path(entry.get("inf_path", "")).name,
            )
            row_text = " ".join(str(v).lower() for v in values)
            if filt and filt not in row_text:
                continue

            # Tag: DLL/SYS get their own colour; INF gets device-type colour
            if ft in ("DLL", "SYS"):
                tag = ft.lower()
            else:
                tag = af.detect_device_type({
                    "device": {
                        "description": entry.get("description", ""),
                        "class":       entry.get("class", ""),
                        "bus":         entry.get("bus", "pci"),
                        "vendor_id":   entry.get("vendor_id"),
                        "device_id":   entry.get("device_id"),
                    },
                    "driver": {"capabilities": {"modes": []}},
                })

            self.tree.insert("", "end", values=values, tags=(tag,))
            shown += 1

        # Row colours
        colours = {
            "wifi":         "#1e3a2e",
            "ethernet_pci": "#1e2a3a",
            "ethernet_usb": "#1e2535",
            "bluetooth":    "#2a1e3a",
            "audio":        "#3a2a1e",
            "hid":          "#3a1e2a",
            "storage":      "#2a2a1e",
            "usb_generic":  "#1e2a2a",
            "generic_pci":  "#252525",
            "dll":          "#2a2010",   # amber tint for DLLs
            "sys":          "#201020",   # purple tint for SYS
        }
        for tag, colour in colours.items():
            self.tree.tag_configure(tag, background=colour)

        total = len(self._results)
        n_inf = sum(1 for e in self._results if e.get("file_type","INF") == "INF")
        n_dll = sum(1 for e in self._results if e.get("file_type") == "DLL")
        n_sys = sum(1 for e in self._results if e.get("file_type") == "SYS")
        self._count_var.set(
            f"Showing {shown} of {total}  "
            f"({n_inf} INF  {n_dll} DLL  {n_sys} SYS)")

        if shown > 0:
            self.btn_load.configure(state="normal")

    # ── select all ────────────────────────────────────────────────────────────

    def _select_all(self):
        all_items = self.tree.get_children()
        self.tree.selection_set(all_items)
        self._on_selection_change()
        return "break"   # prevent default Ctrl+A text-select behaviour

    # ── selection tracking ────────────────────────────────────────────────────

    def _on_selection_change(self):
        n = len(self.tree.selection())
        if n == 0:
            self._sel_label.configure(text="")
            self.btn_load.configure(state="disabled", text="Load Selected")
            self.btn_batch.configure(state="disabled")
        elif n == 1:
            self._sel_label.configure(text="1 selected")
            self.btn_load.configure(state="normal", text="Load Selected")
            self.btn_batch.configure(state="normal")
        else:
            self._sel_label.configure(text=f"{n} selected  (Ctrl+click to add)")
            self.btn_load.configure(state="normal",
                                    text=f"Load First Selected")
            self.btn_batch.configure(state="normal",
                                     text=f"Generate {n} Selected…")

    # ── sort ──────────────────────────────────────────────────────────────────

    def _sort_by(self, col: str):
        col_names = [c[0] for c in self.COLS]
        idx = col_names.index(col)
        data = [(self.tree.set(r, col), r) for r in self.tree.get_children()]
        data.sort(key=lambda x: x[0].lower())
        for i, (_, row) in enumerate(data):
            self.tree.move(row, "", i)

    # ── batch generate ────────────────────────────────────────────────────────

    def _batch_generate(self):
        sel = self.tree.selection()
        if not sel:
            return

        entries = [e for e in self._get_selected_entries(sel) if e]
        if not entries:
            messagebox.showwarning("No entries", "Could not resolve selected rows.", parent=self)
            return

        out_dir = filedialog.askdirectory(
            title=f"Output folder for {len(entries)} driver(s)",
            parent=self)
        if not out_dir:
            return

        # Show progress dialog
        dlg = _BatchProgressDialog(self, len(entries))

        def _worker():
            def _cb(chipset, ok, err):
                self.after(0, dlg.update, chipset, ok, err)

            results = af.batch_generate_drivers(
                entries, out_dir,
                workers=0,         # auto = all CPUs
                progress_cb=_cb)
            self.after(0, dlg.done, results, out_dir)

        threading.Thread(target=_worker, daemon=True).start()

    def _get_selected_entries(self, sel_ids) -> list:
        col_names = [c[0] for c in self.COLS]
        entries = []
        for iid in sel_ids:
            values    = self.tree.item(iid, "values")
            file_name = values[col_names.index("File")]
            vendor_id = values[col_names.index("Vendor ID")]
            device_id = values[col_names.index("Device ID")]
            entry = next(
                (e for e in self._results
                 if Path(e.get("inf_path", "")).name == file_name
                 and (e.get("vendor_id") or "") == vendor_id
                 and (e.get("device_id") or "") == device_id),
                None)
            entries.append(entry)
        return entries

    # ── load selected ─────────────────────────────────────────────────────────

    def _load_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nothing selected",
                "Click a row to select a driver first.", parent=self)
            return
        # Load only the first selected row into the main window
        entries = self._get_selected_entries([sel[0]])
        if entries and entries[0]:
            self._on_select(entries[0])
            self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# Batch progress dialog
# ═══════════════════════════════════════════════════════════════════════════════

class _BatchProgressDialog(tk.Toplevel):
    """
    Small progress window shown while batch_generate_drivers runs.
    Updates in real-time as each driver completes.
    """

    def __init__(self, parent, total: int):
        super().__init__(parent)
        self.title("Generating drivers…")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self._total   = total
        self._done    = 0
        self._ok      = 0
        self._err     = 0

        tk.Label(self, text=f"Generating {total} driver(s) in parallel",
                 font=FONT_BOLD, fg=FG, bg=BG,
                 padx=20, pady=10).pack()

        self._prog = ttk.Progressbar(self, length=380, maximum=total,
                                      mode="determinate")
        self._prog.pack(padx=20, pady=(0, 6))

        self._status = tk.StringVar(value="Starting…")
        tk.Label(self, textvariable=self._status,
                 font=FONT_SMALL, fg=FG_DIM, bg=BG).pack(pady=(0, 4))

        self._log = scrolledtext.ScrolledText(
            self, font=FONT_MONO, fg=FG, bg="#0d0d1a",
            relief="flat", height=10, width=52, state="disabled")
        self._log.pack(padx=16, pady=(0, 10))
        self._log.tag_config("ok",  foreground=SUCCESS)
        self._log.tag_config("err", foreground=ERROR)

        self._centre(parent)

    def _centre(self, parent):
        self.update_idletasks()
        w, h = 420, 320
        x = parent.winfo_x() + (parent.winfo_width()  - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def update(self, chipset: str, ok: bool, err):
        self._done += 1
        if ok:
            self._ok += 1
        else:
            self._err += 1
        self._prog["value"] = self._done
        self._status.set(
            f"{self._done}/{self._total}  —  {self._ok} OK  {self._err} errors")
        self._log.configure(state="normal")
        tag  = "ok" if ok else "err"
        icon = "OK " if ok else "ERR"
        self._log.insert("end", f"[{icon}] {chipset}\n", tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def done(self, results: list, out_dir: str):
        n_ok  = sum(1 for r in results if r[2])
        n_err = sum(1 for r in results if not r[2])
        self._status.set(f"Complete — {n_ok} OK  {n_err} errors")
        self.grab_release()

        if messagebox.askyesno(
                "Batch complete",
                f"{n_ok}/{len(results)} drivers generated successfully.\n\n"
                f"Output: {out_dir}\n\nOpen output folder?",
                parent=self.master):
            _open_path(out_dir)
        self.destroy()


def _open_path(path: str):
    p = Path(path)
    if p.exists():
        if sys.platform == "win32":
            os.startfile(str(p))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)])


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()

    # Window icon (graceful fallback if no .ico present)
    icon_path = Path(__file__).parent / "icon.ico"
    if icon_path.exists():
        try:
            root.iconbitmap(str(icon_path))
        except Exception:
            pass

    # Apply basic dark theme to ttk widgets
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=BG, foreground=FG, font=FONT)
    style.configure("TScrollbar", background=BG2, troughcolor=BG,
                    arrowcolor=FG_DIM, bordercolor=BG)

    app = AstraForgeApp(root)

    # Centre on screen
    root.update_idletasks()
    w, h = 960, 700
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    root.mainloop()


if __name__ == "__main__":
    main()
