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

from core import elabora_file, SUPPORTED_EXT, MODELLI_REMBG, MODELLO_DEFAULT, DESCRIZIONI_MODELLI

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ConvertICO.App')
        self.title("Convertitore Immagini → ICO")
        self.iconbitmap(_resource_path('convertICO.ico'))
        self.geometry("680x840")
        self.minsize(680, 780)
        self.resizable(True, True)
        self._file_list: list[str] = []
        self._build_ui()

    # ── costruzione UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # ── lista file ────────────────────────────────────────────────────────
        frm_lista = ctk.CTkFrame(self)
        frm_lista.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        frm_lista.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frm_lista, text="Immagini",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        btn_row = ctk.CTkFrame(frm_lista, fg_color="transparent")
        btn_row.grid(row=1, column=0, padx=8, pady=(0, 4), sticky="w")
        ctk.CTkButton(btn_row, text="+ Aggiungi", width=110,
                      command=self._aggiungi).pack(side="left", padx=(4, 6))
        ctk.CTkButton(btn_row, text="Pulisci tutto", width=110,
                      fg_color=("gray70", "gray30"), hover_color=("gray60", "gray25"),
                      text_color=("gray10", "gray90"),
                      command=self._pulisci).pack(side="left")

        self.scroll_files = ctk.CTkScrollableFrame(frm_lista, height=140)
        self.scroll_files.grid(row=2, column=0, padx=8, pady=(0, 10), sticky="ew")
        self.scroll_files.grid_columnconfigure(0, weight=1)

        # ── modalità ──────────────────────────────────────────────────────────
        frm_mod = ctk.CTkFrame(self)
        frm_mod.grid(row=1, column=0, padx=12, pady=6, sticky="ew")
        frm_mod.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frm_mod, text="Modalità",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.var_modalita = tk.StringVar(value="ico")

        mod_row = ctk.CTkFrame(frm_mod, fg_color="transparent")
        mod_row.grid(row=1, column=0, padx=8, pady=3, sticky="w")

        ctk.CTkRadioButton(mod_row, text="Converti ICO",
                           variable=self.var_modalita, value="ico",
                           command=self._on_modalita_change).pack(side="left", padx=(4, 14))
        ctk.CTkRadioButton(mod_row, text="Favicon Generator",
                           variable=self.var_modalita, value="favicon",
                           command=self._on_modalita_change).pack(side="left", padx=(4, 14))
        ctk.CTkRadioButton(mod_row, text="App Store Icons",
                           variable=self.var_modalita, value="appstore",
                           command=self._on_modalita_change).pack(side="left", padx=(4, 14))
        ctk.CTkRadioButton(mod_row, text="Format Conversion",
                           variable=self.var_modalita, value="format",
                           command=self._on_modalita_change).pack(side="left", padx=(4, 14))

        # ── opzioni contestuali per modalità ──────────────────────────────────
        self.frm_format_opts = ctk.CTkFrame(frm_mod, fg_color="transparent")
        self.frm_format_opts.grid(row=2, column=0, padx=8, pady=(0, 6), sticky="ew")
        self.frm_format_opts.grid_columnconfigure(1, weight=1)
        self.frm_format_opts.grid_remove()  # Nascondi inizialmente

        ctk.CTkLabel(self.frm_format_opts, text="Formato:").grid(row=0, column=0, padx=4, sticky="w")
        self.var_formato = tk.StringVar(value="png")
        self.om_formato = ctk.CTkOptionMenu(
            self.frm_format_opts, variable=self.var_formato,
            values=["PNG", "JPG", "WebP", "GIF"], width=100)
        self.om_formato.grid(row=0, column=1, padx=(4, 14), sticky="ew")

        ctk.CTkLabel(self.frm_format_opts, text="Qualità:").grid(row=0, column=2, padx=4, sticky="w")
        self.var_qualita = tk.IntVar(value=85)
        self.slider_qualita = ctk.CTkSlider(
            self.frm_format_opts, from_=1, to=100, variable=self.var_qualita,
            number_of_steps=99, width=150)
        self.slider_qualita.grid(row=0, column=3, padx=(4, 10), sticky="ew")
        self.lbl_qualita = ctk.CTkLabel(self.frm_format_opts, text="85", width=30)
        self.lbl_qualita.grid(row=0, column=4, sticky="w")
        self.slider_qualita.configure(command=lambda v: self.lbl_qualita.configure(text=str(int(float(v)))))

        # Opzioni app store
        self.frm_appstore_opts = ctk.CTkFrame(frm_mod, fg_color="transparent")
        self.frm_appstore_opts.grid(row=2, column=0, padx=8, pady=(0, 6), sticky="ew")
        self.frm_appstore_opts.grid_remove()  # Nascondi inizialmente

        ctk.CTkLabel(self.frm_appstore_opts, text="Store:").grid(row=0, column=0, padx=4, sticky="w")
        self.var_store = tk.StringVar(value="google")
        self.om_store = ctk.CTkOptionMenu(
            self.frm_appstore_opts, variable=self.var_store,
            values=["Google Play", "Apple App Store", "Microsoft Store"], width=150)
        self.om_store.grid(row=0, column=1, padx=4, sticky="ew")

        # ── operazioni (spostate) ─────────────────────────────────────────────
        frm_op = ctk.CTkFrame(self)
        frm_op.grid(row=2, column=0, padx=12, pady=6, sticky="ew")
        frm_op.grid_columnconfigure(0, weight=1)

        # ── output ────────────────────────────────────────────────────────────
        frm_out = ctk.CTkFrame(self)
        frm_out.grid(row=3, column=0, padx=12, pady=6, sticky="ew")
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

        ctk.CTkCheckBox(bg_row, text="1. Rimuovi sfondo",
                        variable=self.var_bg,
                        command=self._toggle_modello).pack(side="left", padx=(4, 14))

        ctk.CTkLabel(bg_row, text="Modello:").pack(side="left")

        self.om_modello = ctk.CTkOptionMenu(
            bg_row, variable=self.var_modello,
            values=MODELLI_REMBG, width=210,
            command=self._aggiorna_desc_modello)
        self.om_modello.pack(side="left", padx=(6, 10))

        self.lbl_desc = ctk.CTkLabel(
            bg_row, text=DESCRIZIONI_MODELLI[MODELLO_DEFAULT],
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=11))
        self.lbl_desc.pack(side="left")

        ctk.CTkCheckBox(frm_op, text="2. Ritaglia a quadrato",
                        variable=self.var_sq).grid(
            row=2, column=0, padx=12, pady=3, sticky="w")

        ctk.CTkCheckBox(frm_op, text="3. Converti in ICO  (altrimenti salva PNG)",
                        variable=self.var_ico).grid(
            row=3, column=0, padx=12, pady=(3, 10), sticky="w")

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

        # ── processa ──────────────────────────────────────────────────────────
        self.btn_processa = ctk.CTkButton(
            self, text="PROCESSA", height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._processa)
        self.btn_processa.grid(row=4, column=0, padx=12, pady=(8, 4), sticky="ew")

        self.progress = ctk.CTkProgressBar(self, mode="determinate", height=10)
        self.progress.set(0)
        self.progress.grid(row=5, column=0, padx=12, pady=(0, 6), sticky="ew")

        # ── log ───────────────────────────────────────────────────────────────
        frm_log = ctk.CTkFrame(self)
        frm_log.grid(row=6, column=0, padx=12, pady=(0, 12), sticky="nsew")
        frm_log.grid_columnconfigure(0, weight=1)
        frm_log.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(frm_log, text="Log",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(10, 4), sticky="w")

        self.log_text = ctk.CTkTextbox(
            frm_log, height=160,
            font=ctk.CTkFont(family="Consolas", size=10))
        self.log_text.grid(row=1, column=0, padx=8, pady=(0, 10), sticky="nsew")
        self.log_text.configure(state="disabled")

    # ── gestione lista file ───────────────────────────────────────────────────

    def _render_file_list(self):
        for w in self.scroll_files.winfo_children():
            w.destroy()
        for i, path in enumerate(self._file_list):
            row = ctk.CTkFrame(self.scroll_files, fg_color="transparent")
            row.grid(row=i, column=0, sticky="ew", pady=1)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=os.path.basename(path),
                         anchor="w").grid(row=0, column=0, padx=6, sticky="ew")
            ctk.CTkButton(row, text="✕", width=28, height=24,
                          fg_color="transparent",
                          hover_color=("gray80", "gray25"),
                          text_color=("gray30", "gray70"),
                          command=lambda p=path: self._rimuovi_file(p)).grid(
                row=0, column=1, padx=(0, 4))

    def _aggiungi(self):
        tipi = [("Immagini", " ".join(f"*{e}" for e in SUPPORTED_EXT)),
                ("Tutti i file", "*.*")]
        files = filedialog.askopenfilenames(title="Seleziona immagini", filetypes=tipi)
        for f in files:
            if f not in self._file_list:
                self._file_list.append(f)
        self._render_file_list()

    def _rimuovi_file(self, path: str):
        self._file_list.remove(path)
        self._render_file_list()

    def _pulisci(self):
        self._file_list.clear()
        self._render_file_list()

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

    def _on_modalita_change(self):
        """Mostra/nascondi opzioni a seconda della modalità selezionata."""
        modalita = self.var_modalita.get()

        # Nascondi tutte le opzioni
        self.frm_format_opts.grid_remove()
        self.frm_appstore_opts.grid_remove()

        # Mostra opzioni rilevanti
        if modalita == "format":
            self.frm_format_opts.grid()
        elif modalita == "appstore":
            self.frm_appstore_opts.grid()

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

        # Aggiungi parametri specifici della modalità
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

        # Importa le funzioni per le nuove modalità
        from core import converti_formato_batch, genera_favicon_batch, genera_app_store_icons_batch

        log_fn = lambda msg: self.after(0, self._log, msg)

        if modalita == "ico":
            # Modalità originale: Converti ICO
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
            # Conversione formato
            converti_formato_batch(files, formato, qualita, output_dir, log_fn)
            self.after(0, self.progress.set, 1.0)

        elif modalita == "favicon":
            # Favicon generator
            genera_favicon_batch(files, output_dir, log_fn)
            self.after(0, self.progress.set, 1.0)

        elif modalita == "appstore":
            # App store icons
            genera_app_store_icons_batch(files, store, output_dir, log_fn)
            self.after(0, self.progress.set, 1.0)

        self.after(0, self._done)

    def _done(self):
        self._log("─── Completato ───")
        self._set_ui_busy(False)


if __name__ == "__main__":
    app = App()
    app.mainloop()
