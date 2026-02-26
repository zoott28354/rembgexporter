import io
import json
import os
import re
import struct
import sys
import subprocess
import tempfile
from PIL import Image, ImageCms

# Evita la finestra CMD nera su Windows quando si lancia ImageMagick
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

ICON_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
SUPPORTED_EXT = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.svg')


MODELLI_REMBG = [
    "birefnet-general",
    "birefnet-general-lite",
    "isnet-general-use",
    "u2net",
    "u2net_human_seg",
    "isnet-anime",
]
MODELLO_DEFAULT = "birefnet-general"

DESCRIZIONI_MODELLI = {
    "birefnet-general":      "Più preciso, bordi netti — consigliato per icone",
    "birefnet-general-lite": "Veloce, qualità leggermente inferiore al generale",
    "isnet-general-use":     "Alternativa robusta per oggetti complessi",
    "u2net":                 "Veloce, ideale per batch grandi non critici",
    "u2net_human_seg":       "Ottimizzato per soggetti umani",
    "isnet-anime":           "Per illustrazioni, cartoon e anime",
}


class _ProgressCapture:
    """
    Intercetta stderr durante il download di rembg/pooch.
    tqdm scrive con \\r per aggiornare la riga — filtriamo
    e mostriamo solo gli aggiornamenti ogni 10% e il completamento.
    """
    def __init__(self, log_fn):
        self._log = log_fn
        self._ultima_pct = -1
        self._buf = ""

    def write(self, testo):
        self._buf += testo
        parti = self._buf.replace('\r', '\n').split('\n')
        self._buf = parti[-1]
        for riga in parti[:-1]:
            self._processa(riga.strip())

    def _processa(self, riga):
        if not riga or '%' not in riga:
            return
        m = re.search(r'(\d+)%', riga)
        if not m:
            return
        pct = int(m.group(1))
        if pct == 100 or pct - self._ultima_pct >= 10:
            self._ultima_pct = pct
            # rimuove la barra ASCII █▒ e spazi ridondanti
            pulita = re.sub(r'\|[^\|]*\|', '', riga).strip()
            pulita = re.sub(r'\s{2,}', '  ', pulita)
            self._log(f"    {pulita}")

    def flush(self):
        pass

    def isatty(self):
        return False


def _path_univoco(path: str) -> str:
    """Restituisce path invariato se il file non esiste,
    altrimenti aggiunge (1), (2), ... fino a trovare un nome libero."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    n = 1
    while True:
        candidato = f"{base}({n}){ext}"
        if not os.path.exists(candidato):
            return candidato
        n += 1


def _cache_dir() -> str:
    return os.path.expanduser(
        os.environ.get("U2NET_HOME", os.path.join("~", ".u2net"))
    )


def _modello_in_cache(modello: str) -> bool:
    """Controlla se il file del modello è già stato scaricato in ~/.u2net/"""
    cartella = _cache_dir()
    return any(modello in f for f in os.listdir(cartella)) if os.path.isdir(cartella) else False


def _pulisci_cache_corrotta(modello: str):
    """Rimuove file parziali/corrotti del modello dalla cache."""
    cartella = _cache_dir()
    if not os.path.isdir(cartella):
        return
    for f in os.listdir(cartella):
        if modello in f:
            try:
                os.remove(os.path.join(cartella, f))
            except OSError:
                pass


def rimuovi_sfondo(img: Image.Image, modello: str = MODELLO_DEFAULT, log_fn=print) -> Image.Image:
    """Rimuove lo sfondo usando rembg con il modello scelto. Restituisce immagine RGBA."""
    from rembg import remove, new_session
    if not _modello_in_cache(modello):
        log_fn(f"[...] Download modello '{modello}' (solo al primo utilizzo, attendere...)")
    old_stderr = sys.stderr
    sys.stderr = _ProgressCapture(log_fn)
    try:
        session = new_session(modello)
    except Exception as e:
        _pulisci_cache_corrotta(modello)
        raise RuntimeError(
            f"Download del modello '{modello}' fallito ({e}). "
            "Controlla la connessione e riprova."
        ) from e
    finally:
        sys.stderr = old_stderr
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    output_data = remove(buf.getvalue(), session=session)
    return Image.open(io.BytesIO(output_data)).convert('RGBA')


def ritaglia_quadrato(img: Image.Image) -> Image.Image:
    """Centra l'immagine su uno sfondo trasparente quadrato."""
    img = img.convert('RGBA')
    w, h = img.size
    size = max(w, h)
    nuovo = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    nuovo.paste(img, ((size - w) // 2, (size - h) // 2))
    return nuovo


def _render_svg_to_png(svg_path: str) -> Image.Image:
    """Renderizza SVG a PNG 512×512 RGBA ad alta qualità."""
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    import tempfile

    # Carica SVG con svglib
    drawing = svg2rlg(svg_path)
    if drawing is None:
        raise ValueError(f"Impossibile caricare SVG: {svg_path}")

    # Renderizza a PNG ad alta risoluzione (2× target per qualità maggiore)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_path = tmp.name

    renderPM.drawToFile(drawing, tmp_path, fmt='PNG', width=1024, height=1024)
    img = Image.open(tmp_path).convert('RGBA')

    # Ridimensiona a 512×512 con LANCZOS
    img = img.resize((512, 512), Image.Resampling.LANCZOS)

    # Cleanup
    os.remove(tmp_path)

    return img


def _get_imagemagick_path():
    """Trova il percorso dell'eseguibile ImageMagick (portable o system)."""
    # 1. Prova cartella third-party/imagemagick nel progetto
    base_dir = os.path.dirname(__file__)
    portable_paths = [
        os.path.join(base_dir, 'third-party', 'imagemagick', 'magick.exe'),
        os.path.join(base_dir, '..', 'third-party', 'imagemagick', 'magick.exe'),
    ]
    for path in portable_paths:
        if os.path.exists(path):
            return path

    # 2. Prova cartella imagemagick nel dist (PyInstaller)
    if getattr(sys, 'frozen', False):  # Se eseguito via PyInstaller
        dist_path = os.path.join(sys._MEIPASS, 'imagemagick', 'magick.exe')
        if os.path.exists(dist_path):
            return dist_path

    # 3. Prova system PATH
    try:
        subprocess.run(['magick', '--version'], capture_output=True, check=True, creationflags=_NO_WINDOW)
        return 'magick'
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    raise FileNotFoundError(
        "ImageMagick non trovato! Assicurati di:\n"
        "1. Estrarre il file .7z in 'third-party/imagemagick/'\n"
        "2. O installare ImageMagick globalmente"
    )


def salva_ico(img: Image.Image, output_path: str):
    """Crea ICO multi-frame perfetta usando ImageMagick.

    Flusso:
    1. Converti immagine a RGBA
    2. Ridimensiona a 512×512
    3. Salva come PNG temporaneo
    4. ImageMagick crea ICO con 7 frame: 256, 128, 64, 48, 32, 24, 16
    """
    # 1. Converti al profilo colore sRGB per preservare i colori originali
    if 'icc_profile' in img.info:
        try:
            profilo_src = ImageCms.ImageCmsProfile(io.BytesIO(img.info['icc_profile']))
            profilo_srgb = ImageCms.createProfile('sRGB')
            img = ImageCms.profileToProfile(img, profilo_src, profilo_srgb, outputMode='RGBA')
        except Exception:
            img = img.convert('RGBA')
    else:
        img = img.convert('RGBA')

    # 2. Ridimensiona a 512×512 per qualità massima
    if img.size != (512, 512):
        img = img.resize((512, 512), Image.Resampling.LANCZOS)

    # 3. Salva come PNG temporaneo
    tmp_png = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_png = tmp.name
            img.save(tmp_png, 'PNG')

        # 4. Chiama ImageMagick per creare ICO multi-frame
        magick_path = _get_imagemagick_path()
        cmd = [
            magick_path,
            tmp_png,
            '-define', 'icon:auto-resize=256,128,64,48,32,24,16',
            output_path
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW)

    finally:
        # Pulisci file temporaneo
        if tmp_png and os.path.exists(tmp_png):
            try:
                os.remove(tmp_png)
            except Exception:
                pass


def elabora_file(
    input_path: str,
    output_dir: str | None,
    rimuovi_bg: bool,
    quadrato: bool,
    converti_ico: bool,
    modello: str = MODELLO_DEFAULT,
    log_fn=print,
):
    """
    Pipeline completa per un singolo file.
    - output_dir=None  → stessa cartella del file di input
    """
    nome = os.path.basename(input_path)

    if not os.path.exists(input_path):
        log_fn(f"[ERRORE] File non trovato: {nome}")
        return

    _, ext = os.path.splitext(input_path)
    if ext.lower() not in SUPPORTED_EXT:
        log_fn(f"[SALTATO] Formato non supportato ({ext}): {nome}")
        return

    cartella_out = output_dir if output_dir else os.path.dirname(input_path)
    nome_base = os.path.splitext(nome)[0]

    try:
        # Renderizza SVG a PNG se necessario (prima di Image.open)
        if ext.lower() == '.svg':
            try:
                log_fn(f"[...] Rendering SVG: {nome}")
                img = _render_svg_to_png(input_path)
                log_fn(f"[OK] SVG renderizzato a PNG 512×512")
            except Exception as e:
                log_fn(f"[ERRORE] Rendering SVG fallito: {e}")
                return
        else:
            img = Image.open(input_path)

        if rimuovi_bg:
            log_fn(f"[...] Rimozione sfondo [{modello}]: {nome}")
            img = rimuovi_sfondo(img, modello, log_fn)
            png_nobg = _path_univoco(os.path.join(cartella_out, nome_base + '_nobg.png'))
            img.save(png_nobg, format='PNG')
            log_fn(f"[OK] PNG sfondo rimosso: {os.path.basename(png_nobg)}")

        if quadrato:
            img = ritaglia_quadrato(img)

        if converti_ico:
            output_path = _path_univoco(os.path.join(cartella_out, nome_base + '.ico'))
            salva_ico(img, output_path)
            log_fn(f"[OK] ICO salvata: {os.path.basename(output_path)}")

    except Exception as e:
        log_fn(f"[ERRORE] {nome}: {e}")


# ── NUOVE FEATURE ─────────────────────────────────────────────────────────

def converti_formato_batch(file_list: list[str], formato_dest: str, qualita: int, output_dir: str, log_fn,
                            rimuovi_bg: bool = False, modello: str = MODELLO_DEFAULT, quadrato: bool = False):
    """Converte batch di file tra PNG/JPG/WebP/GIF.

    Args:
        file_list: Lista di file da convertire
        formato_dest: 'png', 'jpg', 'webp', 'gif'
        qualita: 1-100 per qualità compressione
        output_dir: Cartella output (None = stessa cartella di input)
        log_fn: Funzione per logging
        rimuovi_bg: Se True, rimuove sfondo con rembg prima di convertire
        modello: Modello rembg da usare
        quadrato: Se True, ritaglia a quadrato prima di convertire
    """
    if not file_list:
        log_fn("[!] Nessun file in lista.")
        return

    formato_dest = formato_dest.lower()
    if formato_dest not in ['png', 'jpg', 'jpeg', 'webp', 'gif']:
        log_fn(f"[ERRORE] Formato non supportato: {formato_dest}")
        return

    magick_path = _get_imagemagick_path()
    preprocessa = rimuovi_bg or quadrato

    for i, input_path in enumerate(file_list, 1):
        nome = os.path.basename(input_path)
        nome_base = os.path.splitext(nome)[0]
        tmp_png = None

        try:
            cartella_out = output_dir if output_dir else os.path.dirname(input_path)
            ext_output = '.jpg' if formato_dest == 'jpeg' else f'.{formato_dest}'
            output_path = _path_univoco(os.path.join(cartella_out, nome_base + ext_output))

            log_fn(f"[...] Conversione {i}/{len(file_list)}: {nome} -> {formato_dest.upper()}")

            if preprocessa:
                # Carica con PIL per applicare rembg e/o ritaglia
                img = Image.open(input_path)

                if rimuovi_bg:
                    log_fn(f"[...] Rimozione sfondo [{modello}]: {nome}")
                    img = rimuovi_sfondo(img, modello, log_fn)

                if quadrato:
                    img = ritaglia_quadrato(img)

                # Per JPG: converti RGBA → RGB (JPG non supporta trasparenza)
                if formato_dest in ('jpg', 'jpeg') and img.mode == 'RGBA':
                    sfondo = Image.new('RGB', img.size, (255, 255, 255))
                    sfondo.paste(img, mask=img.split()[3])
                    img = sfondo

                # Salva su temp PNG e lascia convertire a ImageMagick per qualità
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_png = tmp.name
                    img.save(tmp_png, 'PNG')

                cmd = [magick_path, tmp_png, '-quality', str(qualita), output_path]
            else:
                # Nessun preprocessing: conversione diretta con ImageMagick
                cmd = [magick_path, input_path, '-quality', str(qualita), output_path]

            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW)
            log_fn(f"[OK] Convertito: {os.path.basename(output_path)}")

        except Exception as e:
            log_fn(f"[ERRORE] {nome}: {e}")
        finally:
            if tmp_png and os.path.exists(tmp_png):
                try:
                    os.remove(tmp_png)
                except Exception:
                    pass


def genera_favicon_batch(file_list: list[str], output_dir: str, log_fn):
    """Genera favicon completa (ico + png + manifest.json) per ogni file.

    Genera:
    - favicon.ico (7 frame: 256, 128, 64, 48, 32, 24, 16)
    - favicon.png (32x32)
    - favicon-192.png (Android)
    - favicon-512.png (iOS)
    - manifest.json (PWA)

    Args:
        file_list: Lista di file da elaborare
        output_dir: Cartella output (None = stessa cartella di input)
        log_fn: Funzione per logging
    """
    if not file_list:
        log_fn("[!] Nessun file in lista.")
        return

    magick_path = _get_imagemagick_path()

    for i, input_path in enumerate(file_list, 1):
        nome = os.path.basename(input_path)
        nome_base = os.path.splitext(nome)[0]

        try:
            log_fn(f"[...] Favicon {i}/{len(file_list)}: {nome}")

            # Determina cartella output
            cartella_out = output_dir if output_dir else os.path.dirname(input_path)

            # Carica immagine
            img = Image.open(input_path)
            if img.size != (512, 512):
                img = img.resize((512, 512), Image.Resampling.LANCZOS)
            img = img.convert('RGBA')

            # Salva come PNG temporaneo
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                img.save(tmp_path, 'PNG')

            try:
                # 1. favicon.ico (7 frame)
                ico_path = os.path.join(cartella_out, 'favicon.ico')
                cmd = [magick_path, tmp_path, '-define', 'icon:auto-resize=256,128,64,48,32,24,16', ico_path]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW)
                log_fn(f"  [OK] favicon.ico")

                # 2. favicon.png (32x32)
                png32_path = os.path.join(cartella_out, 'favicon.png')
                cmd = [magick_path, tmp_path, '-resize', '32x32', png32_path]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW)
                log_fn(f"  [OK] favicon.png (32x32)")

                # 3. favicon-192.png (Android)
                png192_path = os.path.join(cartella_out, 'favicon-192.png')
                cmd = [magick_path, tmp_path, '-resize', '192x192', png192_path]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW)
                log_fn(f"  [OK] favicon-192.png (Android)")

                # 4. favicon-512.png (iOS)
                png512_path = os.path.join(cartella_out, 'favicon-512.png')
                cmd = [magick_path, tmp_path, '-resize', '512x512', png512_path]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW)
                log_fn(f"  [OK] favicon-512.png (iOS)")

                # 5. manifest.json (PWA)
                manifest = {
                    "name": nome_base,
                    "short_name": nome_base[:12],
                    "icons": [
                        {"src": "favicon-192.png", "sizes": "192x192", "type": "image/png"},
                        {"src": "favicon-512.png", "sizes": "512x512", "type": "image/png"}
                    ],
                    "theme_color": "#ffffff",
                    "background_color": "#ffffff",
                    "display": "standalone"
                }
                manifest_path = os.path.join(cartella_out, 'manifest.json')
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)
                log_fn(f"  [OK] manifest.json (PWA)")

                log_fn(f"[OK] Favicon completa generata")

            finally:
                os.remove(tmp_path)

        except Exception as e:
            log_fn(f"[ERRORE] {nome}: {e}")


def genera_app_store_icons_batch(file_list: list[str], store: str, output_dir: str, log_fn):
    """Genera icone specifiche per app store (Google Play, Apple, Microsoft).

    Args:
        file_list: Lista di file da elaborare
        store: 'google' / 'apple' / 'microsoft'
        output_dir: Cartella output
        log_fn: Funzione per logging
    """
    if not file_list:
        log_fn("[!] Nessun file in lista.")
        return

    store = store.lower()

    # Dimensioni per store
    store_dims = {
        'google': [
            (512, 512, 'play_store_512.png'),
        ],
        'apple': [
            (1024, 1024, 'app_store_1024.png'),
            (180, 180, 'iphone_180.png'),
            (167, 167, 'ipad_pro_167.png'),
            (152, 152, 'ipad_152.png'),
        ],
        'microsoft': [
            (150, 150, 'tile_150.png'),
            (70, 70, 'tile_70.png'),
        ]
    }

    if store not in store_dims:
        log_fn(f"[ERRORE] Store non supportato: {store}. Usa: google, apple, microsoft")
        return

    magick_path = _get_imagemagick_path()
    dimensioni = store_dims[store]

    for i, input_path in enumerate(file_list, 1):
        nome = os.path.basename(input_path)
        nome_base = os.path.splitext(nome)[0]

        try:
            log_fn(f"[...] {store.upper()} Icons {i}/{len(file_list)}: {nome}")

            cartella_out = output_dir if output_dir else os.path.dirname(input_path)

            # Carica immagine
            img = Image.open(input_path)
            img = img.convert('RGBA')

            # Salva temporaneo
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                if img.size != (512, 512):
                    img = img.resize((512, 512), Image.Resampling.LANCZOS)
                img.save(tmp_path, 'PNG')

            try:
                # Genera ogni dimensione
                for w, h, nome_file in dimensioni:
                    output_path = os.path.join(cartella_out, nome_file)
                    cmd = [magick_path, tmp_path, '-resize', f'{w}x{h}', output_path]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW)
                    log_fn(f"  [OK] {nome_file} ({w}x{h})")

                log_fn(f"[OK] {store.upper()} icons generated")

            finally:
                os.remove(tmp_path)

        except Exception as e:
            log_fn(f"[ERRORE] {nome}: {e}")
