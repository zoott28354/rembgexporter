import ctypes
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk


def _resource_path(nome: str) -> str:
    """Risolve il percorso di una risorsa sia in modalità script che dentro l'exe PyInstaller."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nome)


class Tooltip:
    """Crea un tooltip (etichetta popup) al passaggio del mouse con delay."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self._tooltip_timer = None
        self._showing = False
        self.widget.bind("<Enter>", self._show_tooltip)
        self.widget.bind("<Leave>", self._hide_tooltip)

    def _show_tooltip(self, event):
        """Schedula la visualizzazione del tooltip con delay di 500ms."""
        if self._showing or self._tooltip_timer:
            return
        self._tooltip_timer = self.widget.after(500, self._show_tooltip_delayed)

    def _show_tooltip_delayed(self):
        """Mostra il tooltip (chiamato dopo delay)."""
        if self.tooltip:
            return

        try:
            self.tooltip = tk.Toplevel(self.widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.attributes("-topmost", True)

            # Crea label con il testo
            label = tk.Label(
                self.tooltip, text=self.text,
                background="#1a1a1a", foreground="#e0e0e0",
                relief="solid", borderwidth=1,
                font=("Arial", 10), padx=8, pady=4
            )
            label.pack()

            # Posiziona il tooltip sopra il widget (approssimato)
            self.tooltip.wm_geometry(f"+{self.widget.winfo_rootx()}+{self.widget.winfo_rooty() - 40}")
            self._showing = True
        except Exception:
            pass
        finally:
            self._tooltip_timer = None

    def _hide_tooltip(self, event):
        """Nasconde il tooltip e cancella timer pending."""
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


from core import elabora_file, SUPPORTED_EXT, MODELLI_REMBG, MODELLO_DEFAULT, DESCRIZIONI_MODELLI

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ConvertICO.App')
        self.title("Convertitore Immagini → ICO")
        self.iconbitmap(_resource_path('convertICO.ico'))
        self.geometry("1250x700")
        self.minsize(1100, 650)
        self.resizable(True, True)
        self._file_list: list[str] = []
        self._selected_file: str | None = None
        self._preview_orig_photo = None
        self._preview_result_photo = None
        self._img_orig_pil = None    # PIL RGBA, usata per ridisegno dinamico
        self._img_result_pil = None  # PIL RGBA, usata per ridisegno dinamico
        self._build_ui()

    # ── costruzione UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        # Layout a 3 colonne: sidebar sx | contenuto | sidebar dx preview
        self.grid_columnconfigure(0, weight=0, minsize=180)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=220)

        # Colori canvas condivisi da lista file e canvases preview
        _tb_colors = ctk.ThemeManager.theme["CTkTextbox"]["fg_color"]
        _is_dark = ctk.get_appearance_mode() == "Dark"
        self._canvas_bg = _tb_colors[1] if _is_dark else _tb_colors[0]

        # ── lista file (SIDEBAR sinistra) ─────────────────────────────────────
        frm_lista = ctk.CTkFrame(self)
        frm_lista.grid(row=0, column=0, rowspan=100, padx=12, pady=(6, 12), sticky="nsew")
        frm_lista.grid_columnconfigure(0, weight=1)
        frm_lista.grid_rowconfigure(2, weight=1)  # Canvas cresce verticalmente

        ctk.CTkLabel(frm_lista, text="Immagini",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        btn_row = ctk.CTkFrame(frm_lista, fg_color="transparent")
        btn_row.grid(row=1, column=0, padx=8, pady=(0, 4), sticky="w")
        self.btn_aggiungi = ctk.CTkButton(btn_row, text="+ Aggiungi", width=110,
                                           command=self._aggiungi)
        self.btn_aggiungi.pack(side="left", padx=(4, 6))
        Tooltip(self.btn_aggiungi, "Seleziona immagini da elaborare\n(PNG, JPG, SVG)")

        self.btn_pulisci = ctk.CTkButton(btn_row, text="Pulisci tutto", width=110,
                                          fg_color=("gray70", "gray30"), hover_color=("gray60", "gray25"),
                                          text_color=("gray10", "gray90"),
                                          command=self._pulisci)
        self.btn_pulisci.pack(side="left")
        Tooltip(self.btn_pulisci, "Rimuovi tutti i file dalla lista")

        # Area file con stile identico al log (nessuna scrollbar visibile)
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

        # Mousewheel scrolling senza scrollbar visibile
        self._canvas_files.bind("<MouseWheel>", lambda e: self._canvas_files.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))
        self.scroll_files.bind("<MouseWheel>", lambda e: self._canvas_files.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

        # ── modalità (MAIN CONTENT centro) ────────────────────────────────────
        frm_mod = ctk.CTkFrame(self)
        frm_mod.grid(row=0, column=1, padx=12, pady=6, sticky="ew")
        frm_mod.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frm_mod, text="Modalità",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.var_modalita = tk.StringVar(value="ico")

        mod_row = ctk.CTkFrame(frm_mod, fg_color="transparent")
        mod_row.grid(row=1, column=0, padx=8, pady=3, sticky="w")

        self.rad_ico = ctk.CTkRadioButton(mod_row, text="Converti ICO",
                                           variable=self.var_modalita, value="ico",
                                           command=self._on_modalita_change)
        self.rad_ico.pack(side="left", padx=(4, 14))
        Tooltip(self.rad_ico, "Icone Windows multi-risoluzione\ncon rimozione sfondo AI")

        self.rad_favicon = ctk.CTkRadioButton(mod_row, text="Favicon Generator",
                                               variable=self.var_modalita, value="favicon",
                                               command=self._on_modalita_change)
        self.rad_favicon.pack(side="left", padx=(4, 14))
        Tooltip(self.rad_favicon, "Favicon web complete\n(ICO + PNG + manifest.json)")

        self.rad_appstore = ctk.CTkRadioButton(mod_row, text="App Store Icons",
                                                variable=self.var_modalita, value="appstore",
                                                command=self._on_modalita_change)
        self.rad_appstore.pack(side="left", padx=(4, 14))
        Tooltip(self.rad_appstore, "Icone per Google Play,\nApple Store, Microsoft Store")

        self.rad_format = ctk.CTkRadioButton(mod_row, text="Format Conversion",
                                              variable=self.var_modalita, value="format",
                                              command=self._on_modalita_change)
        self.rad_format.pack(side="left", padx=(4, 14))
        Tooltip(self.rad_format, "Converte batch tra formati\n(PNG, JPG, WebP, GIF)")

        # ── opzioni contestuali per modalità ──────────────────────────────────
        self.frm_format_opts = ctk.CTkFrame(frm_mod, fg_color="transparent")
        self.frm_format_opts.grid(row=2, column=0, padx=8, pady=(0, 6), sticky="ew")
        self.frm_format_opts.grid_columnconfigure(1, weight=1)
        self.frm_format_opts.grid_remove()

        ctk.CTkLabel(self.frm_format_opts, text="Formato:").grid(row=0, column=0, padx=4, sticky="w")
        self.var_formato = tk.StringVar(value="png")
        self.om_formato = ctk.CTkOptionMenu(
            self.frm_format_opts, variable=self.var_formato,
            values=["PNG", "JPG", "WebP", "GIF"], width=100,
            command=lambda _: (self._aggiorna_lbl_output(), self._aggiorna_preview()))
        self.om_formato.grid(row=0, column=1, padx=(4, 14), sticky="ew")
        Tooltip(self.om_formato, "Formato di output per la conversione")

        ctk.CTkLabel(self.frm_format_opts, text="Qualità:").grid(row=0, column=2, padx=4, sticky="w")
        self.var_qualita = tk.IntVar(value=85)
        self.slider_qualita = ctk.CTkSlider(
            self.frm_format_opts, from_=1, to=100, variable=self.var_qualita,
            number_of_steps=99, width=150)
        self.slider_qualita.grid(row=0, column=3, padx=(4, 10), sticky="ew")
        Tooltip(self.slider_qualita, "1 = veloce/pesante\n100 = lento/leggero")
        self.lbl_qualita = ctk.CTkLabel(self.frm_format_opts, text="85", width=30)
        self.lbl_qualita.grid(row=0, column=4, sticky="w")
        self.slider_qualita.configure(command=lambda v: self.lbl_qualita.configure(text=str(int(float(v)))))

        # Opzioni app store
        self.frm_appstore_opts = ctk.CTkFrame(frm_mod, fg_color="transparent")
        self.frm_appstore_opts.grid(row=2, column=0, padx=8, pady=(0, 6), sticky="ew")
        self.frm_appstore_opts.grid_remove()

        ctk.CTkLabel(self.frm_appstore_opts, text="Store:").grid(row=0, column=0, padx=4, sticky="w")
        self.var_store = tk.StringVar(value="google")
        self.om_store = ctk.CTkOptionMenu(
            self.frm_appstore_opts, variable=self.var_store,
            values=["Google Play", "Apple App Store", "Microsoft Store"], width=150,
            command=lambda _: self._aggiorna_preview())
        self.om_store.grid(row=0, column=1, padx=4, sticky="ew")
        Tooltip(self.om_store, "Scegli lo store per le dimensioni icone")

        # ── operazioni ────────────────────────────────────────────────────────
        frm_op = ctk.CTkFrame(self)
        frm_op.grid(row=1, column=1, padx=12, pady=6, sticky="ew")
        frm_op.grid_columnconfigure(0, weight=1)

        # ── output ────────────────────────────────────────────────────────────
        frm_out = ctk.CTkFrame(self)
        frm_out.grid(row=2, column=1, padx=12, pady=6, sticky="ew")
        frm_out.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frm_op, text="Operazioni",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.var_bg  = tk.BooleanVar(value=True)
        self.var_sq  = tk.BooleanVar(value=True)
        self.var_ico = tk.BooleanVar(value=True)
        self.var_modello = tk.StringVar(value=MODELLO_DEFAULT)

        # Riga rimuovi sfondo
        bg_row = ctk.CTkFrame(frm_op, fg_color="transparent")
        bg_row.grid(row=1, column=0, padx=8, pady=3, sticky="w")

        self.chk_bg = ctk.CTkCheckBox(bg_row, text="1. Rimuovi sfondo",
                                       variable=self.var_bg,
                                       command=lambda: (self._toggle_modello(), self._aggiorna_preview()))
        self.chk_bg.pack(side="left", padx=(4, 14))
        Tooltip(self.chk_bg, "Usa AI (rembg) per rimuovere lo sfondo")

        ctk.CTkLabel(bg_row, text="Modello:").pack(side="left")

        self.om_modello = ctk.CTkOptionMenu(
            bg_row, variable=self.var_modello,
            values=MODELLI_REMBG, width=210,
            command=self._aggiorna_desc_modello)
        self.om_modello.pack(side="left", padx=(6, 10))
        Tooltip(self.om_modello, "Scegli il modello AI per rimozione sfondo")

        self.lbl_desc = ctk.CTkLabel(
            bg_row, text=DESCRIZIONI_MODELLI[MODELLO_DEFAULT],
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=11))
        self.lbl_desc.pack(side="left")

        self.chk_sq = ctk.CTkCheckBox(frm_op, text="2. Ritaglia a quadrato",
                                       variable=self.var_sq,
                                       command=self._aggiorna_preview)
        self.chk_sq.grid(row=2, column=0, padx=12, pady=3, sticky="w")
        Tooltip(self.chk_sq, "Centra l'immagine su sfondo trasparente quadrato")

        self.chk_ico = ctk.CTkCheckBox(frm_op, text="3. Converti in ICO  (altrimenti salva PNG)",
                                        variable=self.var_ico)
        self.chk_ico.grid(row=3, column=0, padx=12, pady=(3, 10), sticky="w")
        Tooltip(self.chk_ico, "Converti in ICO multi-frame\n(Se no, salva solo PNG)")

        # Label informativa per modalità non-ICO (alternativa a chk_ico)
        self.lbl_output_info = ctk.CTkLabel(
            frm_op, text="",
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=12))
        self.lbl_output_info.grid(row=3, column=0, padx=12, pady=(3, 10), sticky="w")
        self.lbl_output_info.grid_remove()

        ctk.CTkLabel(frm_out, text="Destinazione output",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=12, pady=(10, 4), sticky="w")

        self.var_dest = tk.StringVar(value="stessa")
        ctk.CTkRadioButton(frm_out, text="Stessa cartella del file",
                           variable=self.var_dest, value="stessa",
                           command=self._toggle_dest).grid(
            row=1, column=0, padx=12, pady=3, sticky="w")

        dest_row = ctk.CTkFrame(frm_out, fg_color="transparent")
        dest_row.grid(row=2, column=0, columnspan=3, padx=8, pady=(0, 10), sticky="ew")
        dest_row.grid_columnconfigure(1, weight=1)

        ctk.CTkRadioButton(dest_row, text="Cartella personalizzata:",
                           variable=self.var_dest, value="custom",
                           command=self._toggle_dest).grid(
            row=0, column=0, padx=4, sticky="w")

        self.entry_dest = ctk.CTkEntry(dest_row, state="disabled", width=300)
        self.entry_dest.grid(row=0, column=1, padx=(8, 6), sticky="ew")

        self.btn_scegli = ctk.CTkButton(dest_row, text="Scegli...",
                                         state="disabled", width=90,
                                         command=self._scegli_dest)
        self.btn_scegli.grid(row=0, column=2, padx=(0, 4))
        Tooltip(self.btn_scegli, "Seleziona la cartella di output")

        # ── processa ──────────────────────────────────────────────────────────
        self.btn_processa = ctk.CTkButton(
            self, text="PROCESSA", height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._processa)
        self.btn_processa.grid(row=3, column=1, padx=12, pady=(8, 4), sticky="ew")
        Tooltip(self.btn_processa, "Avvia l'elaborazione dei file selezionati")

        self.progress = ctk.CTkProgressBar(self, mode="determinate", height=10)
        self.progress.set(0)
        self.progress.grid(row=4, column=1, padx=12, pady=(0, 6), sticky="ew")

        # ── log ───────────────────────────────────────────────────────────────
        frm_log = ctk.CTkFrame(self)
        frm_log.grid(row=5, column=1, padx=12, pady=(0, 12), sticky="nsew")
        frm_log.grid_columnconfigure(0, weight=1)
        frm_log.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(frm_log, text="Log",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.log_text = ctk.CTkTextbox(
            frm_log, height=160,
            font=ctk.CTkFont(family="Consolas", size=10))
        self.log_text.grid(row=1, column=0, padx=8, pady=(0, 10), sticky="nsew")
        self.log_text.configure(state="disabled")

        # ── PREVIEW (SIDEBAR destra) ──────────────────────────────────────────
        frm_preview = ctk.CTkFrame(self)
        frm_preview.grid(row=0, column=2, rowspan=100, padx=(0, 12), pady=(6, 12), sticky="nsew")
        frm_preview.grid_columnconfigure(0, weight=1)
        frm_preview.grid_rowconfigure(2, weight=1)  # canvas orig
        frm_preview.grid_rowconfigure(4, weight=1)  # canvas result

        ctk.CTkLabel(frm_preview, text="Preview",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        ctk.CTkLabel(frm_preview, text="Originale",
                     text_color=("gray40", "gray60"),
                     font=ctk.CTkFont(size=11)).grid(
            row=1, column=0, padx=12, pady=(0, 2), sticky="w")

        self._canvas_orig = tk.Canvas(
            frm_preview, bg=self._canvas_bg, highlightthickness=0, height=130)
        self._canvas_orig.grid(row=2, column=0, padx=8, pady=(0, 4), sticky="nsew")

        ctk.CTkLabel(frm_preview, text="Risultato",
                     text_color=("gray40", "gray60"),
                     font=ctk.CTkFont(size=11)).grid(
            row=3, column=0, padx=12, pady=(6, 2), sticky="w")

        self._canvas_result = tk.Canvas(
            frm_preview, bg=self._canvas_bg, highlightthickness=0, height=130)
        self._canvas_result.grid(row=4, column=0, padx=8, pady=(0, 4), sticky="nsew")

        self.lbl_preview_info = ctk.CTkLabel(
            frm_preview, text="← Seleziona\nun file",
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=11),
            justify="left")
        self.lbl_preview_info.grid(row=5, column=0, padx=12, pady=(2, 10), sticky="w")

        # Ridisegna adattato se il canvas viene ridimensionato
        self._canvas_orig.bind("<Configure>", lambda e: self._redraw_canvas(
            self._canvas_orig, self._img_orig_pil, '_preview_orig_photo'))
        self._canvas_result.bind("<Configure>", lambda e: self._redraw_canvas(
            self._canvas_result, self._img_result_pil, '_preview_result_photo'))

    # ── gestione lista file ───────────────────────────────────────────────────

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
            # Click per selezionare il file (preview)
            for widget in (row, lbl):
                widget.bind("<Button-1>", lambda e, p=path: self._on_file_select(p))
            # Propaga mousewheel al canvas padre
            for widget in (row, lbl, btn):
                widget.bind("<MouseWheel>", lambda e: self._canvas_files.yview_scroll(
                    int(-1 * (e.delta / 120)), "units"))

    def _aggiungi(self):
        tipi = [("Immagini", " ".join(f"*{e}" for e in SUPPORTED_EXT)),
                ("Tutti i file", "*.*")]
        files = filedialog.askopenfilenames(title="Seleziona immagini", filetypes=tipi)
        for f in files:
            if f not in self._file_list:
                self._file_list.append(f)
        # Auto-seleziona il primo file aggiunto se nessuno è già selezionato
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
        """Seleziona un file per la preview."""
        self._selected_file = path
        self._render_file_list()
        self._aggiorna_preview()

    def _make_checkerboard(self, size, tile=8):
        """Crea sfondo a scacchiera per visualizzare la trasparenza."""
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
        """Ridisegna l'immagine PIL adattata alle dimensioni correnti del canvas."""
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
        setattr(self, photo_attr, photo)  # mantieni riferimento (evita GC)
        canvas.create_image(cw // 2, ch // 2, anchor="center", image=photo)

    def _aggiorna_preview(self):
        """Aggiorna la preview del file selezionato con le impostazioni correnti."""
        from PIL import Image, ImageDraw

        self._canvas_orig.delete("all")
        self._canvas_result.delete("all")
        self._img_orig_pil = None
        self._img_result_pil = None

        if not self._selected_file:
            self.lbl_preview_info.configure(text="← Seleziona\nun file")
            return

        path = self._selected_file
        ext = os.path.splitext(path)[1].lower()

        try:
            if ext == '.svg':
                # Placeholder per SVG (svglib troppo lento per preview live)
                sz = 200
                img_orig = Image.new('RGBA', (sz, sz), (70, 70, 70, 255))
                draw = ImageDraw.Draw(img_orig)
                draw.text((sz // 2 - 14, sz // 2 - 8), "SVG", fill=(180, 180, 180, 255))
                w_orig, h_orig = sz, sz
            else:
                img_orig = Image.open(path).convert('RGBA')
                w_orig, h_orig = img_orig.size

            # Immagine risultato in base alle impostazioni e modalità
            modalita = self.var_modalita.get()
            non_quadrata = (w_orig != h_orig)
            forza_quadrato = (modalita in ("ico", "favicon", "appstore"))

            if self.var_sq.get() and non_quadrata:
                # Padding a quadrato: centra su canvas trasparente
                size = max(w_orig, h_orig)
                img_result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                img_result.paste(img_orig, ((size - w_orig) // 2, (size - h_orig) // 2))
                risultato_tag = "padding"
            elif not self.var_sq.get() and non_quadrata and forza_quadrato:
                # Nessun padding ma pipeline forza 512×512 → schiacciata/distorta
                img_result = img_orig.resize((512, 512), Image.Resampling.LANCZOS)
                risultato_tag = "distorta"
            else:
                img_result = img_orig.copy()
                risultato_tag = "ok"

            # Salva i PIL image per ridisegno dinamico al resize
            self._img_orig_pil = img_orig
            self._img_result_pil = img_result

            # Disegna adattati al canvas corrente
            self._redraw_canvas(self._canvas_orig, self._img_orig_pil, '_preview_orig_photo')
            self._redraw_canvas(self._canvas_result, self._img_result_pil, '_preview_result_photo')

            # Info output
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
                info += "\n⚠ distorta → 512×512"

            if self.var_bg.get():
                info += "\n— sfondo rimosso non in preview"

            self.lbl_preview_info.configure(text=info)

        except Exception as e:
            self.lbl_preview_info.configure(text=f"Preview N/D\n{str(e)[:35]}")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _toggle_modello(self):
        stato = "normal" if self.var_bg.get() else "disabled"
        self.om_modello.configure(state=stato)
        colore = ("gray40", "gray60") if self.var_bg.get() else ("gray70", "gray40")
        self.lbl_desc.configure(text_color=colore)

    def _aggiorna_desc_modello(self, modello: str):
        self.lbl_desc.configure(text=DESCRIZIONI_MODELLI.get(modello, ""))

    def _toggle_dest(self):
        custom = self.var_dest.get() == "custom"
        stato = "normal" if custom else "disabled"
        self.entry_dest.configure(state=stato)
        self.btn_scegli.configure(state=stato)

    def _scegli_dest(self):
        d = filedialog.askdirectory(title="Scegli cartella di output")
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
        """Aggiorna il testo della label informativa output in base alla modalità."""
        modalita = self.var_modalita.get()
        if modalita == "favicon":
            testo = "3.  Output fisso: ICO + PNG + manifest.json"
        elif modalita == "appstore":
            testo = "3.  Output fisso: PNG nelle dimensioni store"
        elif modalita == "format":
            fmt = self.var_formato.get().upper()
            testo = f"3.  Output: {fmt}"
        else:
            testo = ""
        self.lbl_output_info.configure(text=testo)

    def _on_modalita_change(self):
        """Mostra/nascondi opzioni a seconda della modalità selezionata."""
        modalita = self.var_modalita.get()

        self.frm_format_opts.grid_remove()
        self.frm_appstore_opts.grid_remove()

        if modalita == "format":
            self.frm_format_opts.grid()
        elif modalita == "appstore":
            self.frm_appstore_opts.grid()

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

    # ── elaborazione ──────────────────────────────────────────────────────────

    def _processa(self):
        if not self._file_list:
            self._log("[!] Nessun file in lista.")
            return

        output_dir = None
        if self.var_dest.get() == "custom":
            output_dir = self.entry_dest.get().strip() or None
            if not output_dir or not os.path.isdir(output_dir):
                self._log("[ERRORE] Cartella di output non valida.")
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
        self._log("─── Completato ───")
        self._set_ui_busy(False)


if __name__ == "__main__":
    app = App()
    app.mainloop()
