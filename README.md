# Convertitore Immagini → ICO

Tool con interfaccia grafica per preparare immagini come icone Windows (`.ico`).
Combina tre operazioni in pipeline: rimozione sfondo AI, ritaglio quadrato e conversione ICO multi-risoluzione.

---

## Funzionalità

### 1. Rimozione sfondo con AI — powered by [rembg](https://github.com/danielgatis/rembg)

Il punto di forza dell'app è la rimozione automatica dello sfondo tramite **rembg**, una libreria che utilizza modelli di deep learning (reti neurali) per segmentare il soggetto dall'immagine senza intervento manuale.

Sono disponibili **6 modelli** selezionabili dalla GUI:

| Modello | Caratteristica |
|---|---|
| `birefnet-general` | **Più preciso**, bordi netti — consigliato per icone |
| `birefnet-general-lite` | Veloce, qualità leggermente inferiore |
| `isnet-general-use` | Alternativa robusta per oggetti complessi |
| `u2net` | Veloce, ideale per batch grandi |
| `u2net_human_seg` | Ottimizzato per soggetti umani |
| `isnet-anime` | Per illustrazioni, cartoon e anime |

> I modelli vengono scaricati automaticamente al primo utilizzo nella cartella `~/.u2net/` e poi riutilizzati dalla cache locale. Non serve connessione internet agli usi successivi.

### 2. Ritaglio a quadrato

Centra l'immagine su uno sfondo trasparente quadrato, evitando distorsioni nella conversione ICO.

### 3. Conversione ICO multi-risoluzione — powered by [ImageMagick](https://imagemagick.org)

Genera un file `.ico` perfetto che contiene tutte le dimensioni standard Windows in un unico file:

`16 · 24 · 32 · 48 · 64 · 128 · 256 px`

Utilizza **ImageMagick** per creare ICO multi-frame corrette che Windows visualizza perfettamente (256×256 come dimensione primaria). Ogni frame è ottimizzato in PNG compresso.

### Output per ogni immagine elaborata

- `nomefile_nobg.png` — PNG con sfondo trasparente (se rimozione sfondo attiva)
- `nomefile.ico` — icona multi-risoluzione (se conversione ICO attiva)

---

## Struttura del progetto

```
script-per-convertire-immagini-in-ico/
├── app.py                          # Interfaccia GUI (Tkinter)
├── core.py                         # Pipeline elaborazione immagini
├── build.bat                       # Build exe con PyInstaller
├── setup.bat                       # Setup venv e dipendenze
├── lancia.bat                      # Avvio app (generato da setup)
├── requirements.txt                # Dipendenze Python
│
├── third-party/
│   └── imagemagick/                # ImageMagick 7.1.2 portable
│       └── magick.exe              # Eseguibile per creazione ICO
│
├── asset/                          # Icone e risorse GUI
├── venv/                           # Virtual environment (creato da setup.bat)
└── dist/                           # Exe portabile (generato da build.bat)
```

---

## Installazione

```bat
setup.bat
```

Crea il virtual environment, installa tutte le dipendenze e genera `lancia.bat`.

**Requisiti:** Python 3.10+ installato nel sistema.

---

## Avvio

```bat
lancia.bat
```

Generato da `setup.bat`. Avvia l'app senza finestre console.

---

## Build exe portabile

```bat
build.bat
```

Genera `dist\ConvertICO.exe` tramite PyInstaller — singolo eseguibile, nessuna installazione necessaria.

**Incluso nella distribuzione:**
- ✅ Tutte le dipendenze Python (rembg, Pillow, customtkinter, svglib, reportlab, etc.)
- ✅ **ImageMagick 7.1.2** (per creazione ICO perfette)

**Non incluso (scaricato al primo utilizzo):**
- Modelli rembg AI: verranno scaricati in `~/.u2net/` al primo utilizzo su ogni macchina

---

## Dipendenze principali

### Python (pip)

| Pacchetto | Ruolo |
|---|---|
| `rembg` | Rimozione sfondo AI |
| `Pillow` | Manipolazione immagini |
| `onnxruntime` | Esecuzione modelli AI (CPU) |
| `customtkinter` | Interfaccia grafica moderna |
| `svglib` + `reportlab` | Rendering SVG a PNG |
| `pyinstaller` | Build exe portabile |

### Esterne (incluse nella distribuzione)

| Strumento | Ruolo | Versione |
|---|---|---|
| **ImageMagick** | Creazione ICO multi-frame perfette | 7.1.2-Q16-HDRI |

> ImageMagick è incluso come folder `third-party/imagemagick/` nel build exe. Non richiede installazione separata.
