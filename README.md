# Convertitore Immagini → ICO

**Autore:** [zoott28354](https://github.com/zoott28354)
**Repository:** [Image-background-remover-and-ICO-converter](https://github.com/zoott28354/Image-background-remover-and-ICO-converter)

Tool con interfaccia grafica a sidebar per elaborare immagini in 4 modalità diverse:
- **Converti ICO**: Icone Windows multi-risoluzione con rimozione sfondo AI
- **Favicon Generator**: Favicon web complete con manifest.json PWA
- **App Store Icons**: Icone ottimizzate per Google Play, Apple Store, Microsoft Store
- **Format Conversion**: Conversione batch tra PNG, JPG, WebP, GIF con controllo qualità e rimozione sfondo

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

Genera un pacchetto favicon completo per siti web moderni e PWA.
Supporta opzionalmente rimozione sfondo AI e ritaglio a quadrato.

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

Genera icone con dimensioni esatte per i principali app store.
Supporta opzionalmente rimozione sfondo AI e ritaglio a quadrato.

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

> Selezionare lo store dalla dropdown menu. Le immagini vengono ridimensionate e ottimizzate automaticamente.

---

### 🎨 4. Format Conversion — Conversione batch tra formati

Converte immagini tra formati con controllo qualità.
Supporta opzionalmente **rimozione sfondo AI** e **ritaglio a quadrato** prima della conversione.

**Formati supportati:**
- PNG (lossless)
- JPG (lossy, quality 1-100) — sfondo bianco se rimozione sfondo attiva
- WebP (moderno, quality 1-100)
- GIF

**Controllo qualità:** Slider 1-100 (per JPG e WebP)

**Output generato:**
```
nomefile.png / .jpg / .webp / .gif    # Nel formato selezionato
```

> Supporta elaborazione batch: carica più file contemporaneamente.

---

## Operazioni disponibili

Le operazioni nella sezione **Operazioni** si adattano alla modalità selezionata:

| Operazione | ICO | Favicon | App Store | Format |
|---|---|---|---|---|
| 1. Rimuovi sfondo (AI) | ✅ | ✅ | ✅ | ✅ |
| 2. Ritaglia a quadrato | ✅ | ✅ | ✅ | ✅ |
| 3. Output | checkbox ICO/PNG | info fisso | info fisso | info dinamico |

> In modalità non-ICO, l'operazione 3 mostra un'etichetta informativa sull'output fisso o selezionato.

---

## Uso dell'app

### Interfaccia principale

L'interfaccia è divisa in due pannelli:

- **Sidebar sinistra** — Lista immagini: aggiungi, rimuovi singoli file o pulisci tutto
- **Pannello destro** — Tutte le opzioni: modalità, operazioni, destinazione, avvio

**Flusso di utilizzo:**
1. **Aggiungi file** con il pulsante "+ Aggiungi" (PNG, JPG, SVG, BMP, WebP, GIF)
2. **Scegli la modalità** nella sezione "Modalità"
3. **Configura le operazioni** (rimozione sfondo, modello AI, ritaglio)
4. **Scegli la destinazione** output (stessa cartella o personalizzata)
5. **Avvia** con il pulsante "PROCESSA"
6. **Monitora** l'avanzamento nella progress bar e nel log

### Tooltip

Tutti i pulsanti, checkbox e menu mostrano un **tooltip descrittivo** al passaggio del mouse (delay 500ms).

---

## Struttura del progetto

```
Image-background-remover-and-ICO-converter/
├── app.py                          # Interfaccia GUI (CustomTkinter)
├── core.py                         # Pipeline elaborazione immagini
├── build.bat                       # Build exe con PyInstaller
├── setup.bat                       # Setup venv e dipendenze
├── lancia.vbs                      # Avvio app senza finestra CMD (generato da setup)
├── version_info.txt                # Metadati Windows per l'exe (autore, versione, copyright)
├── requirements.txt                # Dipendenze Python
├── convertICO.ico                  # Icona applicazione
│
├── third-party/
│   └── imagemagick/                # ImageMagick 7.1.2 portable
│       └── magick.exe
│
├── venv/                           # Virtual environment (creato da setup.bat)
└── dist/                           # Exe portabile (generato da build.bat)
```

---

## Installazione

```bat
setup.bat
```

Crea il virtual environment, installa tutte le dipendenze e genera `lancia.vbs`.

**Requisiti:** Python 3.10+ installato nel sistema.

---

## Avvio

```bat
lancia.vbs
```

Avvia l'app **senza finestre CMD** in background. Generato automaticamente da `setup.bat`.

---

## Build exe portabile

```bat
build.bat
```

Genera `dist\ConvertICO.exe` tramite PyInstaller — singolo eseguibile, nessuna installazione necessaria.

**Incluso nella distribuzione:**
- ✅ Tutte le dipendenze Python (rembg, Pillow, customtkinter, svglib, reportlab, etc.)
- ✅ **ImageMagick 7.1.2** (per creazione ICO perfette)
- ✅ Metadati Windows (autore, copyright, URL GitHub visibili in Proprietà → Dettagli)

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

---

## Tecnologie utilizzate

| Tecnologia | Utilizzo |
|---|---|
| **Python 3.10+** | Linguaggio principale |
| **CustomTkinter** | GUI moderna con layout sidebar |
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
5. Clicca "PROCESSA"
```
**Output:** `logo_nobg.png`, `logo.ico` (7 risoluzioni: 16→256px)

### Esempio 2: Creare favicon per sito web

```
1. Aggiungi logo_quadrato.png (almeno 512×512)
2. Scegli "Favicon Generator"
3. Clicca "PROCESSA"
```
**Output:** `favicon.ico`, `favicon.png`, `favicon-192.png`, `favicon-512.png`, `manifest.json`

### Esempio 3: Preparare icone per Apple App Store

```
1. Aggiungi app_icon.png (1024×1024 minimo)
2. Scegli "App Store Icons"
3. Seleziona "Apple App Store" dal menu
4. Clicca "PROCESSA"
```
**Output:** `app_store_1024.png`, `iphone_180.png`, `ipad_pro_167.png`, `ipad_152.png`

### Esempio 4: Convertire foto a WebP con sfondo rimosso

```
1. Aggiungi foto.jpg
2. Scegli "Format Conversion"
3. Seleziona formato "WebP", qualità 80
4. ✅ Attiva rimozione sfondo
5. Clicca "PROCESSA"
```
**Output:** `foto.webp` con sfondo trasparente
