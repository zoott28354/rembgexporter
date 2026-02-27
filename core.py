import io
import json
import os
import re
import struct
import sys
import subprocess
import tempfile
from PIL import Image, ImageCms

# Suppress the black CMD window on Windows when launching ImageMagick
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
    "birefnet-general":      "Most precise, sharp edges — recommended",
    "birefnet-general-lite": "Fast, slightly lower quality than general",
    "isnet-general-use":     "Robust alternative for complex objects",
    "u2net":                 "Fast, ideal for large non-critical batches",
    "u2net_human_seg":       "Optimized for human subjects",
    "isnet-anime":           "For illustrations, cartoons and anime",
}


class _ProgressCapture:
    """
    Intercepts stderr during rembg/pooch model download.
    tqdm writes with \\r to update the line — we filter and show
    only updates every 10% and the completion message.
    """
    def __init__(self, log_fn):
        self._log = log_fn
        self._ultima_pct = -1
        self._buf = ""

    def write(self, text):
        self._buf += text
        parts = self._buf.replace('\r', '\n').split('\n')
        self._buf = parts[-1]
        for line in parts[:-1]:
            self._process(line.strip())

    def _process(self, line):
        if not line or '%' not in line:
            return
        m = re.search(r'(\d+)%', line)
        if not m:
            return
        pct = int(m.group(1))
        if pct == 100 or pct - self._ultima_pct >= 10:
            self._ultima_pct = pct
            # remove ASCII progress bar █▒ and redundant spaces
            clean = re.sub(r'\|[^\|]*\|', '', line).strip()
            clean = re.sub(r'\s{2,}', '  ', clean)
            self._log(f"    {clean}")

    def flush(self):
        pass

    def isatty(self):
        return False


def _path_univoco(path: str) -> str:
    """Returns path unchanged if file does not exist,
    otherwise appends (1), (2), ... until a free name is found."""
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
    """Check whether the model file has already been downloaded to ~/.u2net/"""
    cartella = _cache_dir()
    return any(modello in f for f in os.listdir(cartella)) if os.path.isdir(cartella) else False


def _pulisci_cache_corrotta(modello: str):
    """Remove partial/corrupt model files from cache."""
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
    """Remove background using rembg with the chosen model. Returns RGBA image."""
    from rembg import remove, new_session
    if not _modello_in_cache(modello):
        log_fn(f"[...] Downloading model '{modello}' (first use only, please wait...)")
    old_stderr = sys.stderr
    sys.stderr = _ProgressCapture(log_fn)
    try:
        session = new_session(modello)
    except Exception as e:
        _pulisci_cache_corrotta(modello)
        raise RuntimeError(
            f"Model download '{modello}' failed ({e}). "
            "Check your internet connection and try again."
        ) from e
    finally:
        sys.stderr = old_stderr
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    output_data = remove(buf.getvalue(), session=session)
    return Image.open(io.BytesIO(output_data)).convert('RGBA')


def ritaglia_quadrato(img: Image.Image) -> Image.Image:
    """Center the image on a transparent square background."""
    img = img.convert('RGBA')
    w, h = img.size
    size = max(w, h)
    nuovo = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    nuovo.paste(img, ((size - w) // 2, (size - h) // 2))
    return nuovo


def _render_svg_to_png(svg_path: str) -> Image.Image:
    """Render SVG to 512×512 RGBA PNG at high quality."""
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM
    import tempfile

    drawing = svg2rlg(svg_path)
    if drawing is None:
        raise ValueError(f"Cannot load SVG: {svg_path}")

    # Render to PNG at high resolution (2× target for better quality)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp_path = tmp.name

    renderPM.drawToFile(drawing, tmp_path, fmt='PNG', width=1024, height=1024)
    img = Image.open(tmp_path).convert('RGBA')

    # Resize to 512×512 with LANCZOS
    img = img.resize((512, 512), Image.Resampling.LANCZOS)

    os.remove(tmp_path)

    return img


def _get_imagemagick_path():
    """Find the ImageMagick executable (portable or system)."""
    # 1. Try third-party/imagemagick folder in the project
    base_dir = os.path.dirname(__file__)
    portable_paths = [
        os.path.join(base_dir, 'third-party', 'imagemagick', 'magick.exe'),
        os.path.join(base_dir, '..', 'third-party', 'imagemagick', 'magick.exe'),
    ]
    for path in portable_paths:
        if os.path.exists(path):
            return path

    # 2. Try imagemagick folder in dist (PyInstaller)
    if getattr(sys, 'frozen', False):
        dist_path = os.path.join(sys._MEIPASS, 'imagemagick', 'magick.exe')
        if os.path.exists(dist_path):
            return dist_path

    # 3. Try system PATH
    try:
        subprocess.run(['magick', '--version'], capture_output=True, check=True, creationflags=_NO_WINDOW)
        return 'magick'
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    raise FileNotFoundError(
        "ImageMagick not found! Make sure to:\n"
        "1. Extract the .7z file into 'third-party/imagemagick/'\n"
        "2. Or install ImageMagick globally"
    )


def salva_ico(img: Image.Image, output_path: str):
    """Create a perfect multi-frame ICO using ImageMagick.

    Flow:
    1. Convert image to RGBA
    2. Resize to 512×512
    3. Save as temporary PNG
    4. ImageMagick creates ICO with 7 frames: 256, 128, 64, 48, 32, 24, 16
    """
    # 1. Convert to sRGB color profile to preserve original colors
    if 'icc_profile' in img.info:
        try:
            profilo_src = ImageCms.ImageCmsProfile(io.BytesIO(img.info['icc_profile']))
            profilo_srgb = ImageCms.createProfile('sRGB')
            img = ImageCms.profileToProfile(img, profilo_src, profilo_srgb, outputMode='RGBA')
        except Exception:
            img = img.convert('RGBA')
    else:
        img = img.convert('RGBA')

    # 2. Resize to 512×512 for maximum quality
    if img.size != (512, 512):
        img = img.resize((512, 512), Image.Resampling.LANCZOS)

    # 3. Save as temporary PNG
    tmp_png = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_png = tmp.name
            img.save(tmp_png, 'PNG')

        # 4. Call ImageMagick to create multi-frame ICO
        magick_path = _get_imagemagick_path()
        cmd = [
            magick_path,
            tmp_png,
            '-define', 'icon:auto-resize=256,128,64,48,32,24,16',
            output_path
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW)

    finally:
        # Clean up temporary file
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
    Full pipeline for a single file.
    - output_dir=None  → same folder as input file
    """
    nome = os.path.basename(input_path)

    if not os.path.exists(input_path):
        log_fn(f"[ERROR] File not found: {nome}")
        return

    _, ext = os.path.splitext(input_path)
    if ext.lower() not in SUPPORTED_EXT:
        log_fn(f"[SKIP] Unsupported format ({ext}): {nome}")
        return

    cartella_out = output_dir if output_dir else os.path.dirname(input_path)
    nome_base = os.path.splitext(nome)[0]

    try:
        # Render SVG to PNG if needed (before Image.open)
        if ext.lower() == '.svg':
            try:
                log_fn(f"[...] Rendering SVG: {nome}")
                img = _render_svg_to_png(input_path)
                log_fn(f"[OK] SVG rendered to PNG 512×512")
            except Exception as e:
                log_fn(f"[ERROR] SVG rendering failed: {e}")
                return
        else:
            img = Image.open(input_path)

        if rimuovi_bg:
            log_fn(f"[...] Background removal [{modello}]: {nome}")
            img = rimuovi_sfondo(img, modello, log_fn)
            png_nobg = _path_univoco(os.path.join(cartella_out, nome_base + '_nobg.png'))
            img.save(png_nobg, format='PNG')
            log_fn(f"[OK] PNG no-background: {os.path.basename(png_nobg)}")

        if quadrato:
            img = ritaglia_quadrato(img)

        if converti_ico:
            output_path = _path_univoco(os.path.join(cartella_out, nome_base + '.ico'))
            salva_ico(img, output_path)
            log_fn(f"[OK] ICO saved: {os.path.basename(output_path)}")

    except Exception as e:
        log_fn(f"[ERROR] {nome}: {e}")


# ── Additional features ────────────────────────────────────────────────────────

def converti_formato_batch(file_list: list[str], formato_dest: str, qualita: int, output_dir: str, log_fn,
                            rimuovi_bg: bool = False, modello: str = MODELLO_DEFAULT, quadrato: bool = False):
    """Batch convert files between PNG/JPG/WebP/GIF.

    Args:
        file_list: List of files to convert
        formato_dest: 'png', 'jpg', 'webp', 'gif'
        qualita: 1-100 compression quality
        output_dir: Output folder (None = same folder as input)
        log_fn: Logging function
        rimuovi_bg: If True, remove background with rembg before converting
        modello: rembg model to use
        quadrato: If True, crop to square before converting
    """
    if not file_list:
        log_fn("[!] No files in list.")
        return

    formato_dest = formato_dest.lower()
    if formato_dest not in ['png', 'jpg', 'jpeg', 'webp', 'gif']:
        log_fn(f"[ERROR] Unsupported format: {formato_dest}")
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

            log_fn(f"[...] Converting {i}/{len(file_list)}: {nome} -> {formato_dest.upper()}")

            if preprocessa:
                # Load with PIL to apply rembg and/or crop to square
                img = Image.open(input_path)

                if rimuovi_bg:
                    log_fn(f"[...] Background removal [{modello}]: {nome}")
                    img = rimuovi_sfondo(img, modello, log_fn)

                if quadrato:
                    img = ritaglia_quadrato(img)

                # For JPG: convert RGBA → RGB (JPG does not support transparency)
                if formato_dest in ('jpg', 'jpeg') and img.mode == 'RGBA':
                    sfondo = Image.new('RGB', img.size, (255, 255, 255))
                    sfondo.paste(img, mask=img.split()[3])
                    img = sfondo

                # Save to temp PNG and let ImageMagick handle quality conversion
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_png = tmp.name
                    img.save(tmp_png, 'PNG')

                cmd = [magick_path, tmp_png, '-quality', str(qualita), output_path]
            else:
                # No preprocessing: direct conversion with ImageMagick
                cmd = [magick_path, input_path, '-quality', str(qualita), output_path]

            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW)
            log_fn(f"[OK] Converted: {os.path.basename(output_path)}")

        except Exception as e:
            log_fn(f"[ERROR] {nome}: {e}")
        finally:
            if tmp_png and os.path.exists(tmp_png):
                try:
                    os.remove(tmp_png)
                except Exception:
                    pass


def genera_favicon_batch(file_list: list[str], output_dir: str, log_fn):
    """Generate complete favicon (ico + png + manifest.json) for each file.

    Generates:
    - favicon.ico (7 frames: 256, 128, 64, 48, 32, 24, 16)
    - favicon.png (32x32)
    - favicon-192.png (Android)
    - favicon-512.png (iOS)
    - manifest.json (PWA)

    Args:
        file_list: List of files to process
        output_dir: Output folder (None = same folder as input)
        log_fn: Logging function
    """
    if not file_list:
        log_fn("[!] No files in list.")
        return

    magick_path = _get_imagemagick_path()

    for i, input_path in enumerate(file_list, 1):
        nome = os.path.basename(input_path)
        nome_base = os.path.splitext(nome)[0]

        try:
            log_fn(f"[...] Favicon {i}/{len(file_list)}: {nome}")

            cartella_out = output_dir if output_dir else os.path.dirname(input_path)

            img = Image.open(input_path)
            if img.size != (512, 512):
                img = img.resize((512, 512), Image.Resampling.LANCZOS)
            img = img.convert('RGBA')

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                img.save(tmp_path, 'PNG')

            try:
                # 1. favicon.ico (7 frames)
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

                log_fn(f"[OK] Complete favicon generated")

            finally:
                os.remove(tmp_path)

        except Exception as e:
            log_fn(f"[ERROR] {nome}: {e}")


def genera_app_store_icons_batch(file_list: list[str], store: str, output_dir: str, log_fn):
    """Generate icons for app stores (Google Play, Apple, Microsoft).

    Args:
        file_list: List of files to process
        store: 'google' / 'apple' / 'microsoft'
        output_dir: Output folder
        log_fn: Logging function
    """
    if not file_list:
        log_fn("[!] No files in list.")
        return

    store = store.lower()

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
        log_fn(f"[ERROR] Unsupported store: {store}. Use: google, apple, microsoft")
        return

    magick_path = _get_imagemagick_path()
    dimensioni = store_dims[store]

    for i, input_path in enumerate(file_list, 1):
        nome = os.path.basename(input_path)
        nome_base = os.path.splitext(nome)[0]

        try:
            log_fn(f"[...] {store.upper()} Icons {i}/{len(file_list)}: {nome}")

            cartella_out = output_dir if output_dir else os.path.dirname(input_path)

            img = Image.open(input_path)
            img = img.convert('RGBA')

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                if img.size != (512, 512):
                    img = img.resize((512, 512), Image.Resampling.LANCZOS)
                img.save(tmp_path, 'PNG')

            try:
                for w, h, nome_file in dimensioni:
                    output_path = os.path.join(cartella_out, nome_file)
                    cmd = [magick_path, tmp_path, '-resize', f'{w}x{h}', output_path]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW)
                    log_fn(f"  [OK] {nome_file} ({w}x{h})")

                log_fn(f"[OK] {store.upper()} icons generated")

            finally:
                os.remove(tmp_path)

        except Exception as e:
            log_fn(f"[ERROR] {nome}: {e}")
