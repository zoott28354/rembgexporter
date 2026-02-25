# Convertitore Immagini → ICO

Tool con interfaccia grafica multipiano per elaborare immagini in 4 modalità diverse:
- **Converti ICO**: Icone Windows multi-risoluzione con rimozione sfondo AI
- **Favicon Generator**: Favicon web complete con manifest.json PWA
- **App Store Icons**: Icone ottimizzate per Google Play, Apple Store, Microsoft Store
- **Format Conversion**: Conversione batch tra PNG, JPG, WebP, GIF con controllo qualità

---

## Modalità di Elaborazione

### 🔧 1. Converti ICO — Pipeline completa per icone Windows

Combina tre operazioni in pipeline:
1. **Rimozione sfondo con AI** — powered by [rembg](https://github.com/danielgatis/rembg)
2. **Ritaglio a quadrato** — Centra l'immagine su sfondo trasparente
3. **Conversione ICO multi-risoluzione** — powered by [ImageMagick](https://imagemagick.org)

**Modelli AI disponibili** (selezionabili dalla GUI):

| Modello | Caratteristica |
|---|---|
| `birefnet-general` | **Più preciso**, bordi netti — consigliato per icone |
| `birefnet-general-lite` | Veloce, qualità leggermente inferiore |
| `isnet-general-use` | Alternativa robusta per oggetti complessi |
| `u2net` | Veloce, ideale per batch grandi |
| `u2net_human_seg` | Ottimizzato per soggetti umani |
| `isnet-anime` | Per illustrazioni, cartoon e anime |

> I modelli vengono scaricati automaticamente al primo utilizzo nella cartella `~/.u2net/` e poi riutilizzati dalla cache locale. Non serve connessione internet agli usi successivi.

**Output generato:**
```
nomefile_nobg.png        # PNG con sfondo trasparente (se rimozione sfondo attiva)
nomefile.ico             # Icona multi-risoluzione 16 · 24 · 32 · 48 · 64 · 128 · 256 px
```

---

### 🌐 2. Favicon Generator — Favicon completa per siti web

Genera un pacchetto favicon completo per siti web moderni e PWA:

**File generati:**
```
favicon.ico              # Icona multi-frame (7 risoluzioni)
favicon.png              # 32×32 per browser moderni
favicon-192.png          # 192×192 per Android
favicon-512.png          # 512×512 per iOS
manifest.json            # Manifest PWA con riferimenti icone
```

**Uso:** Copia i file nella root del sito web e aggiungi al `<head>`:
```html
<link rel="icon" href="/favicon.ico">
<link rel="manifest" href="/manifest.json">
```

> Supporta immagini PNG, JPG e SVG. SVG viene renderizzato automaticamente a 512×512.

---

### 📱 3. App Store Icons — Icone ottimizzate per store applicativi

Genera icone con dimensioni esatte per i principali app store:

**Google Play Store:**
```
play_store_512.png       # 512×512 icon principale
```

**Apple App Store:**
```
app_store_1024.png       # 1024×1024 icon principale
iphone_180.png           # 180×180 iPhone
ipad_pro_167.png         # 167×167 iPad Pro
ipad_152.png             # 152×152 iPad standard
```

**Microsoft Store:**
```
tile_150.png             # 150×150 tile standard
tile_70.png              # 70×70 tile small
```

> Selezionare lo store dalla dropdown menu. Le immagini vengono ridimensionate e ottimizzate automaticamente mantenendo l'aspect ratio.

---

### 🎨 4. Format Conversion — Conversione batch tra formati

Converte immagini tra formati con controllo qualità:

**Formati supportati:**
- PNG (lossless)
- JPG (lossy, quality 1-100)
- WebP (moderno, quality 1-100)
- GIF (animato se supportato)

**Controllo qualità:** Slider 1-100 (per JPG e WebP)
- Valori alti = migliore qualità, file più grande
- Valori bassi = qualità inferiore, file più piccolo

**Output generato:**
```
nomefile.png             # Se convertito a PNG
nomefile.jpg             # Se convertito a JPG
nomefile.webp            # Se convertito a WebP
nomefile.gif             # Se convertito a GIF
```

> Supporta elaborazione batch: carica più file contemporaneamente, tutti verranno convertiti nello stesso formato con la stessa qualità.

---

## Elaborazione Batch

Tutte le 4 modalità supportano l'elaborazione simultanea di **più file**:

1. **Seleziona file multipli** nella lista (Ctrl+Click)
2. **Scegli la modalità** desiderata (ICO / Favicon / App Store / Format)
3. **Configura le opzioni** specifiche (AI model, store, formato, qualità)
4. **Avvia elaborazione** — La progress bar mostra avanzamento file per file

Ogni file viene elaborato sequenzialmente con output salvato in cartelle separate.

---

## Uso dell'app

### Interfaccia principale

1. **Selezione file**: Drag & drop o browse button per aggiungere immagini (PNG, JPG, SVG)
2. **Scelta modalità**: Radio buttons nella sezione "Modalità"
   - **Converti ICO**: Opzioni per AI model e crop square
   - **Favicon Generator**: Nessuna opzione aggiuntiva
   - **App Store Icons**: Dropdown per scegliere lo store (Google Play, Apple, Microsoft)
   - **Format Conversion**: Dropdown formato + slider qualità
3. **Output directory**: Scegli dove salvare i file elaborati
4. **Avvia elaborazione**: Pulsante "Processa" avvia il worker thread
5. **Progress bar**: Mostra avanzamento in tempo reale

### Opzioni speciali per modalità

**Converti ICO:**
- ✅ Rimozione sfondo: Attiva/disattiva rembg
- 🎯 Modello AI: 6 opzioni disponibili
- ⬜ Ritaglio quadrato: Centra su sfondo trasparente

**Format Conversion:**
- 📋 Formato: PNG / JPG / WebP / GIF
- 🎚️ Qualità: 1 (minima, veloce) → 100 (massima, pesante)

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
| **ImageMagick** | Creazione ICO multi-frame, favicon, app store icons, format conversion | 7.1.2-Q16-HDRI |

> ImageMagick è incluso come folder `third-party/imagemagick/` nel build exe. Non richiede installazione separata.

---

## Tecnologie utilizzate

| Tecnologia | Utilizzo |
|---|---|
| **Python 3.10+** | Linguaggio principale |
| **CustomTkinter** | GUI moderna e responsiva |
| **rembg** | Rimozione sfondo con AI (reti neurali profonde) |
| **Pillow (PIL)** | Manipolazione immagini e profili colore |
| **ImageMagick CLI** | Elaborazione batch, creazione ICO multi-frame, conversione formati |
| **svglib + reportlab** | Rendering SVG → PNG |
| **ONNX Runtime** | Esecuzione accelerata modelli AI (CPU) |
| **PyInstaller** | Packaging exe portabile |

---

## Esempi d'uso

### Esempio 1: Creare un'icona Windows da logo PNG

```
1. Aggiungi logo.png
2. Scegli "Converti ICO"
3. Seleziona modello AI (birefnet-general consigliato)
4. ✅ Attiva rimozione sfondo e ritaglio quadrato
5. Clicca "Processa"
```
**Output:** `logo_nobg.png`, `logo.ico` (256×256 primaria)

### Esempio 2: Creare favicon per sito web

```
1. Aggiungi logo_quadrato.png (almeno 512×512)
2. Scegli "Favicon Generator"
3. Clicca "Processa"
```
**Output:** `favicon.ico`, `favicon.png`, `favicon-192.png`, `favicon-512.png`, `manifest.json`

### Esempio 3: Preparare icone per Apple App Store

```
1. Aggiungi app_icon.png (1024×1024 minimo)
2. Scegli "App Store Icons"
3. Seleziona "Apple App Store" dal menu
4. Clicca "Processa"
```
**Output:** `app_store_1024.png`, `iphone_180.png`, `ipad_pro_167.png`, `ipad_152.png`

### Esempio 4: Convertire batch di foto a WebP (ottimizzate web)

```
1. Aggiungi 10 foto JPG
2. Scegli "Format Conversion"
3. Seleziona formato "WebP"
4. Imposta qualità a 80
5. Clicca "Processa"
```
**Output:** 10 file `.webp` ottimizzati (qualità web/mobile)
