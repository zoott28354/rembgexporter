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

### 3. Conversione ICO multi-risoluzione

Genera un file `.ico` che contiene tutte le dimensioni standard Windows in un unico file:

`16 · 24 · 32 · 48 · 64 · 128 · 256 · 512 px`

I frame fino a 256 px sono in formato BMP; il 512 px viene salvato come PNG compresso nel container ICO (Windows Vista+).

### Output per ogni immagine elaborata

- `nomefile_nobg.png` — PNG con sfondo trasparente (se rimozione sfondo attiva)
- `nomefile.ico` — icona multi-risoluzione (se conversione ICO attiva)

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

> L'exe non include i modelli rembg: verranno scaricati in `~/.u2net/` al primo utilizzo su ogni macchina.

---

## Dipendenze principali

| Pacchetto | Ruolo |
|---|---|
| `rembg` | Rimozione sfondo AI |
| `Pillow` | Manipolazione immagini e salvataggio ICO |
| `onnxruntime` | Esecuzione modelli AI (CPU) |
| `customtkinter` | Interfaccia grafica moderna |
| `pyinstaller` | Build exe portabile |
