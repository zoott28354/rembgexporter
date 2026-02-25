import io
import os
import re
import struct
import sys
import subprocess
import tempfile
from PIL import Image, ImageCms

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
        subprocess.run(['magick', '--version'], capture_output=True, check=True)
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

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
