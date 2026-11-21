"""Génération des curseurs (.cur) et application sous Windows."""
import copy
import ctypes
import json
import os
import struct
import sys
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter

from flags import FLAG_BY_NAME, _star_pts, render_flag

APP_NAME = "FlagCursors"
SIZES = [32, 48, 64, 96]
SHAPES = ["Flèche", "Main", "Drapeau", "Cercle", "Croix", "Étoile", "Losange"]
FILL_MODES = ["Uni", "Dégradé", "Rayures horizontales", "Rayures verticales", "Arc-en-ciel"]

OCR_NORMAL = 32512
OCR_HAND = 32649
SPI_SETCURSORS = 0x0057
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

DEFAULT_CUSTOM = {"mode": "Dégradé", "c1": "#7c5cff", "c2": "#22d3ee",
                  "outline": "#0c0e14", "ring": "#ffffff", "thick": 3, "ringw": 2}
FLAG_STYLE = {"outline": "#0c0e14", "ring": "#ffffff", "thick": 3, "ringw": 2}


def default_state() -> dict:
    return {
        "skin": {"type": "flag", "flag": "France", "custom": copy.deepcopy(DEFAULT_CUSTOM)},
        "shape_normal": "Flèche",
        "shape_link": "Main",
        "size": 48,
        "hand": True,
        "startup": False,
    }


# ------------------------------------------------------------------ dossiers
def data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    p = Path(base) / APP_NAME / "cursors"
    p.mkdir(parents=True, exist_ok=True)
    return p.parent


def load_state() -> dict:
    st = default_state()
    try:
        raw = json.loads((data_dir() / "settings.json").read_text(encoding="utf-8"))
    except Exception:
        return st
    # migration de l'ancienne version (flag / style)
    if "flag" in raw and "skin" not in raw:
        st["skin"]["flag"] = raw["flag"]
    for k in ("shape_normal", "shape_link", "size", "hand", "startup"):
        if k in raw:
            st[k] = raw[k]
    if isinstance(raw.get("skin"), dict):
        sk = raw["skin"]
        st["skin"]["type"] = sk.get("type", "flag")
        st["skin"]["flag"] = sk.get("flag", "France")
        st["skin"]["custom"].update(sk.get("custom", {}))
    if st["skin"]["flag"] not in FLAG_BY_NAME:
        st["skin"]["flag"] = "France"
    for k in ("shape_normal", "shape_link"):
        if st[k] not in SHAPES:
            st[k] = default_state()[k]
    return st


def save_state(s: dict) -> None:
    (data_dir() / "settings.json").write_text(
        json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


# ------------------------------------------------------------------ remplissages
RAINBOW = ["#ff3b3b", "#ff9f1c", "#ffe14d", "#3ddc84", "#3aa0ff", "#7c5cff", "#d946ef"]


def _custom_fill(c: dict) -> Image.Image:
    w, h = 360, 240
    c1, c2 = ImageColor.getrgb(c["c1"]), ImageColor.getrgb(c["c2"])
    mode = c["mode"]
    if mode == "Dégradé":
        grad = Image.linear_gradient("L").resize((w, h))
        return Image.composite(Image.new("RGB", (w, h), c2), Image.new("RGB", (w, h), c1), grad)
    if mode == "Rayures horizontales":
        return render_flag([("H", [c["c1"] if i % 2 == 0 else c["c2"] for i in range(6)])], w, h, 1)
    if mode == "Rayures verticales":
        return render_flag([("V", [c["c1"] if i % 2 == 0 else c["c2"] for i in range(6)])], w, h, 1)
    if mode == "Arc-en-ciel":
        return render_flag([("H", RAINBOW)], w, h, 1)
    return Image.new("RGB", (w, h), c1)


def _fill_and_style(skin: dict):
    if skin["type"] == "flag":
        _, ops = FLAG_BY_NAME[skin["flag"]]
        return render_flag(ops, 360, 240), FLAG_STYLE
    return _custom_fill(skin["custom"]), skin["custom"]


# ------------------------------------------------------------------ formes
ARROW = [(0, 0), (0, .82), (.19, .65), (.32, .97), (.46, .91), (.33, .6), (.58, .6)]


def _shape(shape: str, s: int):
    """Retourne (masque, zone de remplissage, hotspot relatif, compression, base)."""
    m = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(m)

    def rr(x0, y0, x1, y1, r):
        d.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=r * s, fill=255)

    hot, squeeze, fbox, base = (.03, .03), 1.0, None, None
    if shape == "Main":
        rr(.28, .03, .50, .60, .11)      # index
        rr(.50, .27, .65, .70, .07)      # doigts repliés (hauts et arrondis)
        rr(.64, .31, .79, .72, .07)
        rr(.78, .36, .93, .74, .07)
        rr(.20, .44, .93, .97, .16)      # paume
        d.polygon([(.04 * s, .50 * s), (.30 * s, .44 * s), (.30 * s, .78 * s),
                   (.12 * s, .74 * s)], fill=255)  # pouce
        hot = (.39, .04)
    elif shape == "Drapeau":
        d.rectangle([.06 * s, .02 * s, .15 * s, .98 * s], fill=255)
        fx0, fy0, fx1, fy1 = round(.14 * s), round(.04 * s), round(.96 * s), round(.58 * s)
        d.rectangle([fx0, fy0, fx1, fy1], fill=255)
        fbox, base, hot = (fx0, fy0, fx1, fy1), (205, 210, 222, 255), (.105, .03)
    elif shape == "Cercle":
        d.ellipse([.08 * s, .08 * s, .92 * s, .92 * s], fill=255)
        hot = (.5, .5)
    elif shape == "Croix":
        rr(.38, .06, .62, .94, .05)
        rr(.06, .38, .94, .62, .05)
        hot = (.5, .5)
    elif shape == "Étoile":
        d.polygon(_star_pts(.5 * s, .54 * s, .47 * s, 5, .42), fill=255)
        hot = (.5, .5)
    elif shape == "Losange":
        d.polygon([(.5 * s, .04 * s), (.96 * s, .5 * s), (.5 * s, .96 * s), (.04 * s, .5 * s)],
                  fill=255)
        hot = (.5, .5)
    else:  # Flèche
        mg = .03
        pts = [((mg + x * .93) * s, (mg + y * .93) * s) for x, y in ARROW]
        d.polygon(pts, fill=255)
        squeeze = .6
    return m, (fbox or m.getbbox()), hot, squeeze, base


def make_cursor_image(skin: dict, shape: str, size: int = 48, ss: int = 4):
    """Retourne (image RGBA size×size, hotspot en pixels)."""
    fill, st = _fill_and_style(skin)
    s = size * ss
    mask, bbox, hot, squeeze, base = _shape(shape, s)

    k1 = round(s * 0.0115 * int(st["thick"]))
    k2 = round(s * 0.01 * int(st["ringw"]))
    m1 = mask.filter(ImageFilter.MinFilter(2 * k1 + 1)) if k1 > 0 else mask
    m2 = m1.filter(ImageFilter.MinFilter(2 * k2 + 1)) if k2 > 0 else m1

    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(ImageColor.getrgb(st["outline"]) + (255,), (0, 0, s, s), mask)
    out.paste(ImageColor.getrgb(st["ring"]) + (255,), (0, 0, s, s), m1)

    x0, y0, x1, y1 = bbox
    fw, fh = max(1, x1 - x0), max(1, y1 - y0)
    nw = max(1, round(fw * squeeze))
    fl = fill.resize((nw, fh), Image.LANCZOS).convert("RGBA")
    layer = Image.new("RGBA", (s, s), base or (0, 0, 0, 0))
    layer.paste(fl, (x0, y0))
    if nw < fw:  # la flèche est étroite : on prolonge le bord du drapeau
        edge = fl.crop((nw - 1, 0, nw, fh)).resize((fw - nw, fh))
        layer.paste(edge, (x0 + nw, y0))
    out.paste(layer, (0, 0), m2)

    img = out.resize((size, size), Image.LANCZOS)
    hotspot = (min(size - 1, max(0, round(hot[0] * size))),
               min(size - 1, max(0, round(hot[1] * size))))
    return img, hotspot


def save_cur(img: Image.Image, hotspot, path: Path) -> None:
    """Écrit un vrai fichier .cur 32 bits (DIB + masque AND)."""
    w, h = img.size
    pixels = img.convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM).tobytes("raw", "BGRA")
    and_mask = bytes(((w + 31) // 32) * 4 * h)
    header = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0,
                         len(pixels) + len(and_mask), 0, 0, 0, 0)
    data = header + pixels + and_mask
    ico_dir = struct.pack("<HHH", 0, 2, 1)
    entry = struct.pack("<BBBBHHII", w % 256, h % 256, 0, 0,
                        hotspot[0], hotspot[1], len(data), 22)
    Path(path).write_bytes(ico_dir + entry + data)


def build_cursor_file(skin: dict, shape: str, size: int, role: str) -> Path:
    img, hs = make_cursor_image(skin, shape, size)
    path = data_dir() / "cursors" / f"{role}.cur"
    save_cur(img, hs, path)
    return path


# ------------------------------------------------------------ Windows
def is_windows() -> bool:
    return os.name == "nt"


def apply_cursors(normal: Path, link: Path | None = None) -> None:
    if not is_windows():
        raise OSError("L'application des curseurs fonctionne uniquement sous Windows.")
    u32 = ctypes.windll.user32
    u32.LoadCursorFromFileW.restype = ctypes.c_void_p
    u32.LoadCursorFromFileW.argtypes = [ctypes.c_wchar_p]
    u32.SetSystemCursor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
    todo = [(normal, OCR_NORMAL)] + ([(link, OCR_HAND)] if link else [])
    for path, cid in todo:
        handle = u32.LoadCursorFromFileW(str(path))  # SetSystemCursor détruit le handle
        if not handle:
            raise OSError("Impossible de charger le curseur.")
        if not u32.SetSystemCursor(handle, cid):
            raise OSError("Windows a refusé de changer le curseur.")


def apply_state(st: dict) -> None:
    normal = build_cursor_file(st["skin"], st["shape_normal"], st["size"], "normal")
    link = (build_cursor_file(st["skin"], st["shape_link"], st["size"], "link")
            if st["hand"] else None)
    apply_cursors(normal, link)


def restore_default() -> None:
    if not is_windows():
        raise OSError("Fonctionne uniquement sous Windows.")
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0)


def _startup_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --apply-last'
    return f'"{sys.executable}" "{Path(sys.argv[0]).resolve()}" --apply-last'


def set_startup(enabled: bool) -> None:
    if not is_windows():
        return
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if enabled:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, _startup_command())
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except FileNotFoundError:
                pass


def apply_saved() -> None:
    """Réapplique le dernier curseur choisi (utilisé au démarrage de Windows)."""
    apply_state(load_state())
