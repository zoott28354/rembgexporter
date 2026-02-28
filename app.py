import ctypes
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

# ── i18n ──────────────────────────────────────────────────────────────────────
_lang = "en"

STRINGS = {
    "en": {
        "images_label":          "Images",
        "add_btn":               "+ Add",
        "clear_btn":             "Clear all",
        "add_tooltip":           "Select images to process\n(PNG, JPG, SVG)",
        "clear_tooltip":         "Remove all files from the list",
        "mode_label":            "Mode",
        "mode_format":           "Format Conversion",
        "mode_ico":              "Convert ICO",
        "mode_favicon":          "Favicon Generator",
        "mode_appstore":         "App Store Icons",
        "mode_format_tooltip":   "Batch convert between formats\n(PNG, JPG, WebP, GIF)",
        "mode_ico_tooltip":      "Multi-resolution Windows icons\nwith AI background removal",
        "mode_favicon_tooltip":  "Complete web favicon\n(ICO + PNG + manifest.json)",
        "mode_appstore_tooltip": "Icons for Google Play,\nApple Store, Microsoft Store",
        "format_label":          "Format:",
        "quality_label":         "Quality:",
        "quality_tooltip":       "1 = fast/large\n100 = slow/small",
        "format_tooltip":        "Output format for conversion",
        "store_label":           "Store:",
        "store_tooltip":         "Choose store for icon sizes",
        "ops_label":             "Operations",
        "remove_bg":             "1. Remove background",
        "remove_bg_tooltip":     "Use AI (rembg) to remove background",
        "model_label":           "Model:",
        "model_tooltip":         "Choose AI model for background removal",
        "crop_square":           "2. Crop to square",
        "crop_square_tooltip":   "Center image on transparent square background",
        "convert_ico":           "3. Convert to ICO  (otherwise save PNG)",
        "convert_ico_tooltip":   "Convert to multi-frame ICO\n(If no, save PNG only)",
        "output_dest_label":     "Output destination",
        "dest_same":             "Same folder as source file",
        "dest_custom":           "Custom folder:",
        "choose_btn":            "Choose...",
        "choose_tooltip":        "Select output folder",
        "process_btn":           "PROCESS",
        "process_tooltip":       "Start processing selected files",
        "log_label":             "Log",
        "preview_label":         "Preview",
        "preview_orig":          "Original",
        "preview_result":        "Result",
        "preview_select":        "← Select\na file",
        "output_fixed_favicon":  "3.  Fixed output: ICO + PNG + manifest.json",
        "output_fixed_appstore": "3.  Fixed output: PNG at store dimensions",
        "transparency_yes":      "transparency ✓",
        "transparency_no":       "no transparency",
        "distorted_info":        "⚠ distorted → 512×512",
        "bg_removed_preview":    "— bg removal not in preview",
        "no_files_log":          "[!] No files in list.",
        "invalid_dir_log":       "[ERROR] Invalid output folder.",
        "done_log":              "─── Done ───",
        "open_images_title":     "Select images",
        "choose_dir_title":      "Choose output folder",
        "images_types_label":    "Images",
        # Model descriptions
        "desc_birefnet-general":      "Most precise, sharp edges — recommended",
        "desc_birefnet-general-lite": "Fast, slightly lower quality than general",
        "desc_isnet-general-use":     "Robust alternative for complex objects",
        "desc_u2net":                 "Fast, ideal for large non-critical batches",
        "desc_u2net_human_seg":       "Optimized for human subjects",
        "desc_isnet-anime":           "For illustrations, cartoons and anime",
    },
    "it": {
        "images_label":          "Immagini",
        "add_btn":               "+ Aggiungi",
        "clear_btn":             "Pulisci tutto",
        "add_tooltip":           "Seleziona immagini da elaborare\n(PNG, JPG, SVG)",
        "clear_tooltip":         "Rimuovi tutti i file dalla lista",
        "mode_label":            "Modalità",
        "mode_format":           "Format Conversion",
        "mode_ico":              "Converti ICO",
        "mode_favicon":          "Favicon Generator",
        "mode_appstore":         "App Store Icons",
        "mode_format_tooltip":   "Converte batch tra formati\n(PNG, JPG, WebP, GIF)",
        "mode_ico_tooltip":      "Icone Windows multi-risoluzione\ncon rimozione sfondo AI",
        "mode_favicon_tooltip":  "Favicon web complete\n(ICO + PNG + manifest.json)",
        "mode_appstore_tooltip": "Icone per Google Play,\nApple Store, Microsoft Store",
        "format_label":          "Formato:",
        "quality_label":         "Qualità:",
        "quality_tooltip":       "1 = veloce/pesante\n100 = lento/leggero",
        "format_tooltip":        "Formato di output per la conversione",
        "store_label":           "Store:",
        "store_tooltip":         "Scegli lo store per le dimensioni icone",
        "ops_label":             "Operazioni",
        "remove_bg":             "1. Rimuovi sfondo",
        "remove_bg_tooltip":     "Usa AI (rembg) per rimuovere lo sfondo",
        "model_label":           "Modello:",
        "model_tooltip":         "Scegli il modello AI per rimozione sfondo",
        "crop_square":           "2. Ritaglia a quadrato",
        "crop_square_tooltip":   "Centra l'immagine su sfondo trasparente quadrato",
        "convert_ico":           "3. Converti in ICO  (altrimenti salva PNG)",
        "convert_ico_tooltip":   "Converti in ICO multi-frame\n(Se no, salva solo PNG)",
        "output_dest_label":     "Destinazione output",
        "dest_same":             "Stessa cartella del file",
        "dest_custom":           "Cartella personalizzata:",
        "choose_btn":            "Scegli...",
        "choose_tooltip":        "Seleziona la cartella di output",
        "process_btn":           "PROCESSA",
        "process_tooltip":       "Avvia l'elaborazione dei file selezionati",
        "log_label":             "Log",
        "preview_label":         "Preview",
        "preview_orig":          "Originale",
        "preview_result":        "Risultato",
        "preview_select":        "← Seleziona\nun file",
        "output_fixed_favicon":  "3.  Output fisso: ICO + PNG + manifest.json",
        "output_fixed_appstore": "3.  Output fisso: PNG nelle dimensioni store",
        "transparency_yes":      "trasparenza ✓",
        "transparency_no":       "no trasparenza",
        "distorted_info":        "⚠ distorta → 512×512",
        "bg_removed_preview":    "— sfondo rimosso non in preview",
        "no_files_log":          "[!] Nessun file in lista.",
        "invalid_dir_log":       "[ERRORE] Cartella di output non valida.",
        "done_log":              "─── Completato ───",
        "open_images_title":     "Seleziona immagini",
        "choose_dir_title":      "Scegli cartella di output",
        "images_types_label":    "Immagini",
        # Descrizioni modelli
        "desc_birefnet-general":      "Più preciso, bordi netti — consigliato",
        "desc_birefnet-general-lite": "Veloce, qualità leggermente inferiore al generale",
        "desc_isnet-general-use":     "Alternativa robusta per oggetti complessi",
        "desc_u2net":                 "Veloce, ideale per batch grandi non critici",
        "desc_u2net_human_seg":       "Ottimizzato per soggetti umani",
        "desc_isnet-anime":           "Per illustrazioni, cartoon e anime",
    },
}


def _t(key: str) -> str:
    """Returns the translation for key in the current language."""
    return STRINGS.get(_lang, STRINGS["en"]).get(key, key)


def _resource_path(name: str) -> str:
    """Resolves resource path both in script mode and inside PyInstaller exe."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


class Tooltip:
    """Creates a popup tooltip on mouse hover with delay."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self._tooltip_timer = None
        self._showing = False
        self.widget.bind("<Enter>", self._show_tooltip)
        self.widget.bind("<Leave>", self._hide_tooltip)

    def _show_tooltip(self, event):
        """Schedule tooltip display with 500ms delay."""
        if self._showing or self._tooltip_timer:
            return
        self._tooltip_timer = self.widget.after(500, self._show_tooltip_delayed)

    def _show_tooltip_delayed(self):
        """Show the tooltip (called after delay)."""
        if self.tooltip:
            return
        try:
            self.tooltip = tk.Toplevel(self.widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.attributes("-topmost", True)
            label = tk.Label(
                self.tooltip, text=self.text,
                background="#1a1a1a", foreground="#e0e0e0",
                relief="solid", borderwidth=1,
                font=("Arial", 10), padx=8, pady=4
            )
            label.pack()
            self.tooltip.wm_geometry(f"+{self.widget.winfo_rootx()}+{self.widget.winfo_rooty() - 40}")
            self._showing = True
        except Exception:
            pass
        finally:
            self._tooltip_timer = None

    def _hide_tooltip(self, event):
        """Hide the tooltip and cancel any pending timer."""
        if self._tooltip_timer:
            self.widget.after_cancel(self._tooltip_timer)
            self._tooltip_timer = None
        if self.tooltip:
            try:
                self.tooltip.destroy()
            except Exception:
                pass
            self.tooltip = None
        self._showing = False


from core import elabora_file, SUPPORTED_EXT, MODELLI_REMBG, MODELLO_DEFAULT

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('RembgExporter.App')
        self.title("RembgExporter")
        self.iconbitmap(_resource_path(os.path.join('src', 'assets', 'RembgExporter.ico')))
        self.geometry("1250x700")
        self.minsize(1100, 650)
        self.resizable(True, True)
        self._file_list: list[str] = []
        self._selected_file: str | None = None
        self._preview_orig_photo = None
        self._preview_result_photo = None
        self._img_orig_pil = None
        self._img_result_pil = None
        self._tooltips: list[tuple[Tooltip, str]] = []
        self._lang_btns: dict[str, ctk.CTkButton] = {}
        self._build_ui()

    def _tt(self, widget, key: str) -> Tooltip:
        """Create a tooltip and register it for language updates."""
        t = Tooltip(widget, _t(key))
        self._tooltips.append((t, key))
        return t

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # 3-column layout: left sidebar | content | right preview sidebar
        self.grid_columnconfigure(0, weight=0, minsize=180)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=220)

        _tb_colors = ctk.ThemeManager.theme["CTkTextbox"]["fg_color"]
        _is_dark = ctk.get_appearance_mode() == "Dark"
        self._canvas_bg = _tb_colors[1] if _is_dark else _tb_colors[0]

        # ── file list (left sidebar) ───────────────────────────────────────────
        frm_lista = ctk.CTkFrame(self)
        frm_lista.grid(row=0, column=0, rowspan=100, padx=12, pady=(6, 12), sticky="nsew")
        frm_lista.grid_columnconfigure(0, weight=1)
        frm_lista.grid_rowconfigure(2, weight=1)

        # Header row: "Images" label + IT/EN switcher
        hdr_row = ctk.CTkFrame(frm_lista, fg_color="transparent")
        hdr_row.grid(row=0, column=0, padx=8, pady=(10, 4), sticky="ew")
        hdr_row.grid_columnconfigure(0, weight=1)

        self.lbl_images = ctk.CTkLabel(hdr_row, text="",
                         font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_images.grid(row=0, column=0, sticky="w")

        lang_frame = ctk.CTkFrame(hdr_row, fg_color="transparent")
        lang_frame.grid(row=0, column=1, sticky="e")

        for lang in ["IT", "EN"]:
            btn = ctk.CTkButton(
                lang_frame, text=lang, width=28, height=22,
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                hover_color=("gray70", "gray40"),
                text_color=("gray50", "gray60"),
                command=lambda l=lang.lower(): self._switch_lang(l)
            )
            btn.pack(side="left", padx=1)
            self._lang_btns[lang.lower()] = btn

        btn_row = ctk.CTkFrame(frm_lista, fg_color="transparent")
        btn_row.grid(row=1, column=0, padx=8, pady=(0, 4), sticky="w")

        self.btn_aggiungi = ctk.CTkButton(btn_row, text="", width=110,
                                           command=self._aggiungi)
        self.btn_aggiungi.pack(side="left", padx=(4, 6))
        self._tt(self.btn_aggiungi, "add_tooltip")

        self.btn_pulisci = ctk.CTkButton(btn_row, text="", width=110,
                                          fg_color=("gray70", "gray30"), hover_color=("gray60", "gray25"),
                                          text_color=("gray10", "gray90"),
                                          command=self._pulisci)
        self.btn_pulisci.pack(side="left")
        self._tt(self.btn_pulisci, "clear_tooltip")

        frm_files_box = ctk.CTkFrame(
            frm_lista,
            fg_color=_tb_colors,
            corner_radius=ctk.ThemeManager.theme["CTkTextbox"]["corner_radius"])
        frm_files_box.grid(row=2, column=0, padx=8, pady=(0, 10), sticky="nsew")
        frm_files_box.grid_columnconfigure(0, weight=1)
        frm_files_box.grid_rowconfigure(0, weight=1)

        self._canvas_files = tk.Canvas(
            frm_files_box, bg=self._canvas_bg, highlightthickness=0)
        self._canvas_files.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")

        self.scroll_files = tk.Frame(self._canvas_files, bg=self._canvas_bg)
        self._cw = self._canvas_files.create_window(0, 0, window=self.scroll_files, anchor="nw")

        self.scroll_files.bind("<Configure>", lambda e: self._canvas_files.config(
            scrollregion=self._canvas_files.bbox("all")))
        self._canvas_files.bind("<Configure>", lambda e: self._canvas_files.itemconfig(
            self._cw, width=e.width))

        self._canvas_files.bind("<MouseWheel>", lambda e: self._canvas_files.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))
        self.scroll_files.bind("<MouseWheel>", lambda e: self._canvas_files.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

        # ── mode (main content center) ─────────────────────────────────────────
        frm_mod = ctk.CTkFrame(self)
        frm_mod.grid(row=0, column=1, padx=12, pady=6, sticky="ew")
        frm_mod.grid_columnconfigure(0, weight=1)

        self.lbl_modalita = ctk.CTkLabel(frm_mod, text="",
                     font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_modalita.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.var_modalita = tk.StringVar(value="format")

        mod_row = ctk.CTkFrame(frm_mod, fg_color="transparent")
        mod_row.grid(row=1, column=0, padx=8, pady=3, sticky="w")

        self.rad_format = ctk.CTkRadioButton(mod_row, text="",
                                              variable=self.var_modalita, value="format",
                                              command=self._on_modalita_change)
        self.rad_format.pack(side="left", padx=(4, 14))
        self._tt(self.rad_format, "mode_format_tooltip")

        self.rad_ico = ctk.CTkRadioButton(mod_row, text="",
                                           variable=self.var_modalita, value="ico",
                                           command=self._on_modalita_change)
        self.rad_ico.pack(side="left", padx=(4, 14))
        self._tt(self.rad_ico, "mode_ico_tooltip")

        self.rad_favicon = ctk.CTkRadioButton(mod_row, text="",
                                               variable=self.var_modalita, value="favicon",
                                               command=self._on_modalita_change)
        self.rad_favicon.pack(side="left", padx=(4, 14))
        self._tt(self.rad_favicon, "mode_favicon_tooltip")

        self.rad_appstore = ctk.CTkRadioButton(mod_row, text="",
                                                variable=self.var_modalita, value="appstore",
                                                command=self._on_modalita_change)
        self.rad_appstore.pack(side="left", padx=(4, 14))
        self._tt(self.rad_appstore, "mode_appstore_tooltip")

        # ── format options ─────────────────────────────────────────────────────
        self.frm_format_opts = ctk.CTkFrame(frm_mod, fg_color="transparent")
        self.frm_format_opts.grid(row=2, column=0, padx=8, pady=(0, 6), sticky="ew")
        self.frm_format_opts.grid_columnconfigure(1, weight=1)
        self.frm_format_opts.grid_remove()

        self.lbl_formato_label = ctk.CTkLabel(self.frm_format_opts, text="")
        self.lbl_formato_label.grid(row=0, column=0, padx=4, sticky="w")
        self.var_formato = tk.StringVar(value="png")
        self.om_formato = ctk.CTkOptionMenu(
            self.frm_format_opts, variable=self.var_formato,
            values=["PNG", "JPG", "WebP", "GIF"], width=100,
            command=lambda _: (self._aggiorna_lbl_output(), self._aggiorna_preview()))
        self.om_formato.grid(row=0, column=1, padx=(4, 14), sticky="ew")
        self._tt(self.om_formato, "format_tooltip")

        self.lbl_qualita_label = ctk.CTkLabel(self.frm_format_opts, text="")
        self.lbl_qualita_label.grid(row=0, column=2, padx=4, sticky="w")
        self.var_qualita = tk.IntVar(value=85)
        self.slider_qualita = ctk.CTkSlider(
            self.frm_format_opts, from_=1, to=100, variable=self.var_qualita,
            number_of_steps=99, width=150)
        self.slider_qualita.grid(row=0, column=3, padx=(4, 10), sticky="ew")
        self._tt(self.slider_qualita, "quality_tooltip")
        self.lbl_qualita = ctk.CTkLabel(self.frm_format_opts, text="85", width=30)
        self.lbl_qualita.grid(row=0, column=4, sticky="w")
        self.slider_qualita.configure(command=lambda v: self.lbl_qualita.configure(text=str(int(float(v)))))

        # ── app store options ──────────────────────────────────────────────────
        self.frm_appstore_opts = ctk.CTkFrame(frm_mod, fg_color="transparent")
        self.frm_appstore_opts.grid(row=2, column=0, padx=8, pady=(0, 6), sticky="ew")
        self.frm_appstore_opts.grid_remove()

        self.lbl_store_label = ctk.CTkLabel(self.frm_appstore_opts, text="")
        self.lbl_store_label.grid(row=0, column=0, padx=4, sticky="w")
        self.var_store = tk.StringVar(value="google")
        self.om_store = ctk.CTkOptionMenu(
            self.frm_appstore_opts, variable=self.var_store,
            values=["Google Play", "Apple App Store", "Microsoft Store"], width=150,
            command=lambda _: self._aggiorna_preview())
        self.om_store.grid(row=0, column=1, padx=4, sticky="ew")
        self._tt(self.om_store, "store_tooltip")

        # ── operations ────────────────────────────────────────────────────────
        frm_op = ctk.CTkFrame(self)
        frm_op.grid(row=1, column=1, padx=12, pady=6, sticky="ew")
        frm_op.grid_columnconfigure(0, weight=1)

        # ── output destination ─────────────────────────────────────────────────
        frm_out = ctk.CTkFrame(self)
        frm_out.grid(row=2, column=1, padx=12, pady=6, sticky="ew")
        frm_out.grid_columnconfigure(1, weight=1)

        self.lbl_ops = ctk.CTkLabel(frm_op, text="",
                     font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_ops.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.var_bg  = tk.BooleanVar(value=True)
        self.var_sq  = tk.BooleanVar(value=True)
        self.var_ico = tk.BooleanVar(value=True)
        self.var_modello = tk.StringVar(value=MODELLO_DEFAULT)

        bg_row = ctk.CTkFrame(frm_op, fg_color="transparent")
        bg_row.grid(row=1, column=0, padx=8, pady=3, sticky="w")

        self.chk_bg = ctk.CTkCheckBox(bg_row, text="",
                                       variable=self.var_bg,
                                       command=lambda: (self._toggle_modello(), self._aggiorna_preview()))
        self.chk_bg.pack(side="left", padx=(4, 14))
        self._tt(self.chk_bg, "remove_bg_tooltip")

        self.lbl_modello_label = ctk.CTkLabel(bg_row, text="")
        self.lbl_modello_label.pack(side="left")

        self.om_modello = ctk.CTkOptionMenu(
            bg_row, variable=self.var_modello,
            values=MODELLI_REMBG, width=210,
            command=self._aggiorna_desc_modello)
        self.om_modello.pack(side="left", padx=(6, 10))
        self._tt(self.om_modello, "model_tooltip")

        self.lbl_desc = ctk.CTkLabel(
            bg_row, text="",
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=11))
        self.lbl_desc.pack(side="left")

        self.chk_sq = ctk.CTkCheckBox(frm_op, text="",
                                       variable=self.var_sq,
                                       command=self._aggiorna_preview)
        self.chk_sq.grid(row=2, column=0, padx=12, pady=3, sticky="w")
        self._tt(self.chk_sq, "crop_square_tooltip")

        self.chk_ico = ctk.CTkCheckBox(frm_op, text="",
                                        variable=self.var_ico)
        self.chk_ico.grid(row=3, column=0, padx=12, pady=(3, 10), sticky="w")
        self._tt(self.chk_ico, "convert_ico_tooltip")

        self.lbl_output_info = ctk.CTkLabel(
            frm_op, text="",
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=12))
        self.lbl_output_info.grid(row=3, column=0, padx=12, pady=(3, 10), sticky="w")
        self.lbl_output_info.grid_remove()

        self.lbl_output_dest = ctk.CTkLabel(frm_out, text="",
                     font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_output_dest.grid(row=0, column=0, columnspan=3, padx=12, pady=(10, 4), sticky="w")

        self.var_dest = tk.StringVar(value="stessa")
        self.rad_dest_same = ctk.CTkRadioButton(frm_out, text="",
                           variable=self.var_dest, value="stessa",
                           command=self._toggle_dest)
        self.rad_dest_same.grid(row=1, column=0, padx=12, pady=3, sticky="w")

        dest_row = ctk.CTkFrame(frm_out, fg_color="transparent")
        dest_row.grid(row=2, column=0, columnspan=3, padx=8, pady=(0, 10), sticky="ew")
        dest_row.grid_columnconfigure(1, weight=1)

        self.rad_dest_custom = ctk.CTkRadioButton(dest_row, text="",
                           variable=self.var_dest, value="custom",
                           command=self._toggle_dest)
        self.rad_dest_custom.grid(row=0, column=0, padx=4, sticky="w")

        self.entry_dest = ctk.CTkEntry(dest_row, state="disabled", width=300)
        self.entry_dest.grid(row=0, column=1, padx=(8, 6), sticky="ew")

        self.btn_scegli = ctk.CTkButton(dest_row, text="",
                                         state="disabled", width=90,
                                         command=self._scegli_dest)
        self.btn_scegli.grid(row=0, column=2, padx=(0, 4))
        self._tt(self.btn_scegli, "choose_tooltip")

        # ── process button ─────────────────────────────────────────────────────
        self.btn_processa = ctk.CTkButton(
            self, text="", height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._processa)
        self.btn_processa.grid(row=3, column=1, padx=12, pady=(8, 4), sticky="ew")
        self._tt(self.btn_processa, "process_tooltip")

        self.progress = ctk.CTkProgressBar(self, mode="determinate", height=10)
        self.progress.set(0)
        self.progress.grid(row=4, column=1, padx=12, pady=(0, 6), sticky="ew")

        # ── log ───────────────────────────────────────────────────────────────
        frm_log = ctk.CTkFrame(self)
        frm_log.grid(row=5, column=1, padx=12, pady=(0, 12), sticky="nsew")
        frm_log.grid_columnconfigure(0, weight=1)
        frm_log.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(5, weight=1)

        self.lbl_log = ctk.CTkLabel(frm_log, text="",
                     font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_log.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.log_text = ctk.CTkTextbox(
            frm_log, height=160,
            font=ctk.CTkFont(family="Consolas", size=10))
        self.log_text.grid(row=1, column=0, padx=8, pady=(0, 10), sticky="nsew")
        self.log_text.configure(state="disabled")

        # ── preview (right sidebar) ────────────────────────────────────────────
        frm_preview = ctk.CTkFrame(self)
        frm_preview.grid(row=0, column=2, rowspan=100, padx=(0, 12), pady=(6, 12), sticky="nsew")
        frm_preview.grid_columnconfigure(0, weight=1)
        frm_preview.grid_rowconfigure(2, weight=1)
        frm_preview.grid_rowconfigure(4, weight=1)

        self.lbl_preview_header = ctk.CTkLabel(frm_preview, text="",
                     font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_preview_header.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.lbl_preview_orig_label = ctk.CTkLabel(frm_preview, text="",
                     text_color=("gray40", "gray60"),
                     font=ctk.CTkFont(size=11))
        self.lbl_preview_orig_label.grid(row=1, column=0, padx=12, pady=(0, 2), sticky="w")

        self._canvas_orig = tk.Canvas(
            frm_preview, bg=self._canvas_bg, highlightthickness=0, height=130)
        self._canvas_orig.grid(row=2, column=0, padx=8, pady=(0, 4), sticky="nsew")

        self.lbl_preview_result_label = ctk.CTkLabel(frm_preview, text="",
                     text_color=("gray40", "gray60"),
                     font=ctk.CTkFont(size=11))
        self.lbl_preview_result_label.grid(row=3, column=0, padx=12, pady=(6, 2), sticky="w")

        self._canvas_result = tk.Canvas(
            frm_preview, bg=self._canvas_bg, highlightthickness=0, height=130)
        self._canvas_result.grid(row=4, column=0, padx=8, pady=(0, 4), sticky="nsew")

        self.lbl_preview_info = ctk.CTkLabel(
            frm_preview, text="",
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=11),
            justify="left")
        self.lbl_preview_info.grid(row=5, column=0, padx=12, pady=(2, 10), sticky="w")

        self._canvas_orig.bind("<Configure>", lambda e: self._redraw_canvas(
            self._canvas_orig, self._img_orig_pil, '_preview_orig_photo'))
        self._canvas_result.bind("<Configure>", lambda e: self._redraw_canvas(
            self._canvas_result, self._img_result_pil, '_preview_result_photo'))

        # Apply initial texts and mode state
        self._set_texts()
        self._on_modalita_change()

    # ── language switch ────────────────────────────────────────────────────────

    def _switch_lang(self, lang: str):
        global _lang
        _lang = lang
        self._set_texts()

    def _set_texts(self):
        """Update all UI widget text to the current language."""
        # Sidebar
        self.lbl_images.configure(text=_t("images_label"))
        self.btn_aggiungi.configure(text=_t("add_btn"))
        self.btn_pulisci.configure(text=_t("clear_btn"))
        # Mode
        self.lbl_modalita.configure(text=_t("mode_label"))
        self.rad_format.configure(text=_t("mode_format"))
        self.rad_ico.configure(text=_t("mode_ico"))
        self.rad_favicon.configure(text=_t("mode_favicon"))
        self.rad_appstore.configure(text=_t("mode_appstore"))
        # Format opts
        self.lbl_formato_label.configure(text=_t("format_label"))
        self.lbl_qualita_label.configure(text=_t("quality_label"))
        # Store opts
        self.lbl_store_label.configure(text=_t("store_label"))
        # Operations
        self.lbl_ops.configure(text=_t("ops_label"))
        self.chk_bg.configure(text=_t("remove_bg"))
        self.lbl_modello_label.configure(text=_t("model_label"))
        self.chk_sq.configure(text=_t("crop_square"))
        self.chk_ico.configure(text=_t("convert_ico"))
        # Output destination
        self.lbl_output_dest.configure(text=_t("output_dest_label"))
        self.rad_dest_same.configure(text=_t("dest_same"))
        self.rad_dest_custom.configure(text=_t("dest_custom"))
        self.btn_scegli.configure(text=_t("choose_btn"))
        # Process / Log / Preview
        self.btn_processa.configure(text=_t("process_btn"))
        self.lbl_log.configure(text=_t("log_label"))
        self.lbl_preview_header.configure(text=_t("preview_label"))
        self.lbl_preview_orig_label.configure(text=_t("preview_orig"))
        self.lbl_preview_result_label.configure(text=_t("preview_result"))
        # Model description
        self.lbl_desc.configure(text=_t(f"desc_{self.var_modello.get()}"))
        # Tooltips
        for tooltip, key in self._tooltips:
            tooltip.text = _t(key)
        # Language button highlight
        for lang, btn in self._lang_btns.items():
            if lang == _lang:
                btn.configure(fg_color=("gray50", "gray50"), text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray50", "gray60"))
        # Refresh dynamic labels
        self._aggiorna_lbl_output()
        self._aggiorna_preview()

    # ── file list management ───────────────────────────────────────────────────

    def _render_file_list(self):
        for w in self.scroll_files.winfo_children():
            w.destroy()
        for i, path in enumerate(self._file_list):
            is_sel = (path == self._selected_file)
            row_bg = ("gray75", "gray30") if is_sel else "transparent"
            row = ctk.CTkFrame(self.scroll_files, fg_color=row_bg, corner_radius=4)
            row.grid(row=i, column=0, sticky="ew", pady=1)
            row.grid_columnconfigure(0, weight=1)
            lbl = ctk.CTkLabel(row, text=os.path.basename(path), anchor="w")
            lbl.grid(row=0, column=0, padx=6, sticky="ew")
            btn = ctk.CTkButton(row, text="✕", width=28, height=24,
                          fg_color="transparent",
                          hover_color=("gray80", "gray25"),
                          text_color=("gray30", "gray70"),
                          command=lambda p=path: self._rimuovi_file(p))
            btn.grid(row=0, column=1, padx=(0, 4))
            for widget in (row, lbl):
                widget.bind("<Button-1>", lambda e, p=path: self._on_file_select(p))
            for widget in (row, lbl, btn):
                widget.bind("<MouseWheel>", lambda e: self._canvas_files.yview_scroll(
                    int(-1 * (e.delta / 120)), "units"))

    def _aggiungi(self):
        tipi = [(_t("images_types_label"), " ".join(f"*{e}" for e in SUPPORTED_EXT)),
                ("All files", "*.*")]
        files = filedialog.askopenfilenames(title=_t("open_images_title"), filetypes=tipi)
        for f in files:
            if f not in self._file_list:
                self._file_list.append(f)
        if files and self._selected_file is None and self._file_list:
            self._selected_file = self._file_list[0]
            self._aggiorna_preview()
        self._render_file_list()

    def _rimuovi_file(self, path: str):
        self._file_list.remove(path)
        if self._selected_file == path:
            self._selected_file = self._file_list[0] if self._file_list else None
            self._aggiorna_preview()
        self._render_file_list()

    def _pulisci(self):
        self._file_list.clear()
        self._selected_file = None
        self._aggiorna_preview()
        self._render_file_list()

    # ── preview ───────────────────────────────────────────────────────────────

    def _on_file_select(self, path: str):
        self._selected_file = path
        self._render_file_list()
        self._aggiorna_preview()

    def _make_checkerboard(self, size, tile=8):
        """Create checkerboard background to visualize transparency."""
        from PIL import Image, ImageDraw
        w, h = size
        bg = Image.new('RGB', (w, h), (200, 200, 200))
        draw = ImageDraw.Draw(bg)
        for y in range(0, h, tile):
            for x in range(0, w, tile):
                if ((x // tile) + (y // tile)) % 2:
                    draw.rectangle([x, y, x + tile - 1, y + tile - 1], fill=(160, 160, 160))
        return bg

    def _redraw_canvas(self, canvas, img_pil, photo_attr: str):
        """Redraw PIL image fitted to current canvas dimensions."""
        from PIL import Image, ImageTk
        canvas.delete("all")
        if img_pil is None:
            return
        canvas.update_idletasks()
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw < 2 or ch < 2:
            cw, ch = 200, 150
        pad = 6
        max_w = max(cw - 2 * pad, 1)
        max_h = max(ch - 2 * pad, 1)

        thumb = img_pil.copy()
        thumb.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        tw, th = thumb.size
        bg = self._make_checkerboard((tw, th))
        bg.paste(thumb, mask=thumb.split()[3])
        photo = ImageTk.PhotoImage(bg)
        setattr(self, photo_attr, photo)
        canvas.create_image(cw // 2, ch // 2, anchor="center", image=photo)

    def _aggiorna_preview(self):
        """Update the preview for the selected file with current settings."""
        from PIL import Image, ImageDraw

        self._canvas_orig.delete("all")
        self._canvas_result.delete("all")
        self._img_orig_pil = None
        self._img_result_pil = None

        if not self._selected_file:
            self.lbl_preview_orig_label.configure(text=_t("preview_orig"))
            self.lbl_preview_info.configure(text=_t("preview_select"))
            return

        path = self._selected_file
        ext = os.path.splitext(path)[1].lower()

        try:
            if ext == '.svg':
                sz = 200
                img_orig = Image.new('RGBA', (sz, sz), (70, 70, 70, 255))
                draw = ImageDraw.Draw(img_orig)
                draw.text((sz // 2 - 14, sz // 2 - 8), "SVG", fill=(180, 180, 180, 255))
                w_orig, h_orig = sz, sz
                self.lbl_preview_orig_label.configure(text=_t("preview_orig"))
            else:
                img_orig = Image.open(path).convert('RGBA')
                w_orig, h_orig = img_orig.size
                self.lbl_preview_orig_label.configure(
                    text=f'{_t("preview_orig")} ({w_orig}×{h_orig})')

            modalita = self.var_modalita.get()
            non_quadrata = (w_orig != h_orig)
            forza_quadrato = (modalita in ("ico", "favicon", "appstore"))
            ha_sq = (modalita != "format")

            if ha_sq and self.var_sq.get() and non_quadrata:
                size = max(w_orig, h_orig)
                img_result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                img_result.paste(img_orig, ((size - w_orig) // 2, (size - h_orig) // 2))
                risultato_tag = "padding"
            elif ha_sq and not self.var_sq.get() and non_quadrata and forza_quadrato:
                img_result = img_orig.resize((512, 512), Image.Resampling.LANCZOS)
                risultato_tag = "distorta"
            else:
                img_result = img_orig.copy()
                risultato_tag = "ok"

            self._img_orig_pil = img_orig
            self._img_result_pil = img_result

            self._redraw_canvas(self._canvas_orig, self._img_orig_pil, '_preview_orig_photo')
            self._redraw_canvas(self._canvas_result, self._img_result_pil, '_preview_result_photo')

            if modalita == "ico":
                info = f"{w_orig}×{h_orig}\n→ ICO  16–256px"
            elif modalita == "favicon":
                info = f"{w_orig}×{h_orig}\n→ ICO + PNG\n   32 / 192 / 512px"
            elif modalita == "appstore":
                store = self.var_store.get().replace(" App Store", "").replace(" Store", "")
                info = f"{w_orig}×{h_orig}\n→ {store} icons"
            else:
                fmt = self.var_formato.get().upper()
                info = f"{w_orig}×{h_orig}\n→ {fmt}"

            if risultato_tag == "padding":
                sq = max(w_orig, h_orig)
                info += f"\npadding → {sq}×{sq}"
            elif risultato_tag == "distorta":
                info += "\n" + _t("distorted_info")

            if self.var_bg.get():
                info += "\n" + _t("bg_removed_preview")

            self.lbl_preview_info.configure(text=info)

        except Exception as e:
            self.lbl_preview_orig_label.configure(text=_t("preview_orig"))
            self.lbl_preview_info.configure(text=f"Preview N/A\n{str(e)[:35]}")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _toggle_modello(self):
        stato = "normal" if self.var_bg.get() else "disabled"
        self.om_modello.configure(state=stato)
        colore = ("gray40", "gray60") if self.var_bg.get() else ("gray70", "gray40")
        self.lbl_desc.configure(text_color=colore)

    def _aggiorna_desc_modello(self, modello: str):
        self.lbl_desc.configure(text=_t(f"desc_{modello}"))

    def _toggle_dest(self):
        custom = self.var_dest.get() == "custom"
        stato = "normal" if custom else "disabled"
        self.entry_dest.configure(state=stato)
        self.btn_scegli.configure(state=stato)

    def _scegli_dest(self):
        d = filedialog.askdirectory(title=_t("choose_dir_title"))
        if d:
            self.entry_dest.configure(state="normal")
            self.entry_dest.delete(0, "end")
            self.entry_dest.insert(0, d)

    def _log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _aggiorna_lbl_output(self):
        """Update output info label text based on current mode."""
        modalita = self.var_modalita.get()
        if modalita == "favicon":
            testo = _t("output_fixed_favicon")
        elif modalita == "appstore":
            testo = _t("output_fixed_appstore")
        elif modalita == "format":
            fmt = self.var_formato.get().upper()
            trasparenza = fmt in ("PNG", "WEBP", "GIF")
            nota = _t("transparency_yes") if trasparenza else _t("transparency_no")
            testo = f"3.  Output: {fmt}  ({nota})"
        else:
            testo = ""
        self.lbl_output_info.configure(text=testo)

    def _on_modalita_change(self):
        """Show/hide options depending on the selected mode."""
        modalita = self.var_modalita.get()

        self.frm_format_opts.grid_remove()
        self.frm_appstore_opts.grid_remove()

        if modalita == "format":
            self.frm_format_opts.grid()
        elif modalita == "appstore":
            self.frm_appstore_opts.grid()

        if modalita == "format":
            self.chk_sq.grid_remove()
        else:
            self.chk_sq.grid()

        if modalita == "ico":
            self.chk_ico.grid()
            self.lbl_output_info.grid_remove()
        else:
            self.chk_ico.grid_remove()
            self.lbl_output_info.grid()
            self._aggiorna_lbl_output()

        self._aggiorna_preview()

    def _set_ui_busy(self, busy: bool):
        stato = "disabled" if busy else "normal"
        self.btn_processa.configure(state=stato)

    # ── processing ────────────────────────────────────────────────────────────

    def _processa(self):
        if not self._file_list:
            self._log(_t("no_files_log"))
            return

        output_dir = None
        if self.var_dest.get() == "custom":
            output_dir = self.entry_dest.get().strip() or None
            if not output_dir or not os.path.isdir(output_dir):
                self._log(_t("invalid_dir_log"))
                return

        self._set_ui_busy(True)
        self.progress.set(0)

        modalita = self.var_modalita.get()
        kwargs = {
            'modalita': modalita,
            'output_dir': output_dir,
        }

        if modalita == "format":
            kwargs['formato'] = self.var_formato.get().lower()
            kwargs['qualita'] = self.var_qualita.get()
        elif modalita == "appstore":
            store_map = {"Google Play": "google", "Apple App Store": "apple", "Microsoft Store": "microsoft"}
            kwargs['store'] = store_map.get(self.var_store.get(), "google")

        threading.Thread(
            target=self._worker,
            args=(list(self._file_list),),
            kwargs=kwargs,
            daemon=True).start()

    def _worker(self, files: list[str], modalita: str, output_dir: str,
                formato: str = None, qualita: int = 85, store: str = None):
        totale = len(files)

        from core import converti_formato_batch, genera_favicon_batch, genera_app_store_icons_batch

        log_fn = lambda msg: self.after(0, self._log, msg)

        if modalita == "ico":
            rimuovi_bg = self.var_bg.get()
            quadrato   = self.var_sq.get()
            ico        = self.var_ico.get()
            modello    = self.var_modello.get()

            for i, path in enumerate(files, 1):
                elabora_file(
                    input_path=path,
                    output_dir=output_dir,
                    rimuovi_bg=rimuovi_bg,
                    quadrato=quadrato,
                    converti_ico=ico,
                    modello=modello,
                    log_fn=log_fn,
                )
                self.after(0, self.progress.set, i / totale)

        elif modalita == "format":
            converti_formato_batch(
                files, formato, qualita, output_dir, log_fn,
                rimuovi_bg=self.var_bg.get(),
                modello=self.var_modello.get(),
                quadrato=self.var_sq.get(),
            )
            self.after(0, self.progress.set, 1.0)

        elif modalita == "favicon":
            genera_favicon_batch(files, output_dir, log_fn)
            self.after(0, self.progress.set, 1.0)

        elif modalita == "appstore":
            genera_app_store_icons_batch(files, store, output_dir, log_fn)
            self.after(0, self.progress.set, 1.0)

        self.after(0, self._done)

    def _done(self):
        self._log(_t("done_log"))
        self._set_ui_busy(False)


if __name__ == "__main__":
    app = App()
    app.mainloop()
