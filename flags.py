"""Drapeaux dessinés entièrement en code (aucune image externe nécessaire).

Chaque drapeau est une liste d'opérations de dessin en coordonnées
normalisées (0..1) sur un canevas 3:2. Les rayons sont exprimés en
« hauteur de drapeau ».
"""
import math
import unicodedata

from PIL import Image, ImageDraw

ASPECT = 1.5  # largeur / hauteur


# ----------------------------------------------------------------- rendu
def _star_pts(cx, cy, r, n=5, inner=None, rot=-90):
    if inner is None:
        inner = 0.382 if n == 5 else 0.5
    pts = []
    for i in range(n * 2):
        a = math.radians(rot + i * 180 / n)
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def _render(ops, w, h):
    im = Image.new("RGB", (w, h), "#FFFFFF")
    d = ImageDraw.Draw(im)

    def X(v):
        return v * w

    def Y(v):
        return v * h

    for op in ops:
        k = op[0]
        if k == "bg":
            d.rectangle([0, 0, w, h], fill=op[1])
        elif k in ("H", "V"):
            items = [(c, 1) if isinstance(c, str) else c for c in op[1]]
            tot = sum(wt for _, wt in items)
            pos = 0
            for col, wt in items:
                a, b = pos / tot, (pos + wt) / tot
                pos += wt
                if k == "H":
                    d.rectangle([0, round(Y(a)), w, round(Y(b))], fill=col)
                else:
                    d.rectangle([round(X(a)), 0, round(X(b)), h], fill=col)
        elif k == "rect":
            _, x0, y0, x1, y1, col = op
            d.rectangle([X(x0), Y(y0), X(x1), Y(y1)], fill=col)
        elif k == "circ":
            _, cx, cy, r, col = op
            px, py, rr = X(cx), Y(cy), Y(r)
            d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=col)
        elif k == "ring":
            _, cx, cy, r, t, col = op
            px, py, rr = X(cx), Y(cy), Y(r)
            d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=col,
                      width=max(1, round(Y(t))))
        elif k == "star":
            _, cx, cy, r, col, n, inner = op
            d.polygon(_star_pts(X(cx), Y(cy), Y(r), n, inner), fill=col)
        elif k == "poly":
            d.polygon([(X(x), Y(y)) for x, y in op[1]], fill=op[2])
        elif k == "pline":
            pts = [(X(x), Y(y)) for x, y in op[1]]
            d.line(pts + [pts[0]], fill=op[2], width=max(1, round(Y(op[3]))),
                   joint="curve")
        elif k == "line":
            _, x0, y0, x1, y1, wd, col = op
            d.line([X(x0), Y(y0), X(x1), Y(y1)], fill=col,
                   width=max(1, round(Y(wd))))
        elif k == "pie":
            _, cx, cy, r, a0, a1, col = op
            px, py, rr = X(cx), Y(cy), Y(r)
            d.pieslice([px - rr, py - rr, px + rr, py + rr], a0, a1, fill=col)
        elif k == "cres":
            _, cx, cy, r, col, off, sc = op
            m = Image.new("L", (w, h), 0)
            md = ImageDraw.Draw(m)
            px, py, rr = X(cx), Y(cy), Y(r)
            md.ellipse([px - rr, py - rr, px + rr, py + rr], fill=255)
            qx, qr = px + rr * off, rr * sc
            md.ellipse([qx - qr, py - qr, qx + qr, py + qr], fill=0)
            im.paste(col, (0, 0, w, h), m)
        elif k == "sub":
            _, x0, y0, x1, y1, sops = op
            sw, sh = max(1, round(X(x1 - x0))), max(1, round(Y(y1 - y0)))
            im.paste(_render(sops, sw, sh), (round(X(x0)), round(Y(y0))))
    return im


def render_flag(ops, w=360, h=240, ss=2):
    """Rend un drapeau en RGB (sur-échantillonné pour des bords lisses)."""
    big = _render(ops, w * ss, h * ss)
    return big.resize((w, h), Image.LANCZOS) if ss > 1 else big


# ------------------------------------------------------------- raccourcis
def H(*c): return ("H", list(c))
def V(*c): return ("V", list(c))
def bg(c): return ("bg", c)
def rect(x0, y0, x1, y1, c): return ("rect", x0, y0, x1, y1, c)
def circ(cx, cy, r, c): return ("circ", cx, cy, r, c)
def ring(cx, cy, r, t, c): return ("ring", cx, cy, r, t, c)
def poly(pts, c): return ("poly", pts, c)
def line(x0, y0, x1, y1, wd, c): return ("line", x0, y0, x1, y1, wd, c)
def pie(cx, cy, r, a0, a1, c): return ("pie", cx, cy, r, a0, a1, c)
def star(cx, cy, r, c, n=5, inner=None): return ("star", cx, cy, r, c, n, inner)
def cres(cx, cy, r, c, off=0.3, sc=0.8): return ("cres", cx, cy, r, c, off, sc)
def sub(x0, y0, x1, y1, ops): return ("sub", x0, y0, x1, y1, ops)


def nordic(cx, t, c):
    """Croix scandinave (épaisseur t en hauteur de drapeau)."""
    return [rect(cx - t / 3, 0, cx + t / 3, 1, c),
            rect(0, 0.5 - t / 2, 1, 0.5 + t / 2, c)]


def small_cross(cx, cy, c, s=0.07):
    return [rect(cx - s / 4, cy - s, cx + s / 4, cy + s, c),
            rect(cx - s * 0.67, cy - s / 3, cx + s * 0.67, cy + s / 3, c)]


def hexagram(cx, cy, r, c, wd):
    out = []
    for start in (-90, 90):
        pts = []
        for i in range(3):
            a = math.radians(start + i * 120)
            pts.append((cx + r * math.cos(a) / ASPECT, cy + r * math.sin(a)))
        out.append(("pline", pts, c, wd))
    return out


def union_jack():
    return ([bg("#012169"),
             line(-.05, -.05, 1.05, 1.05, .2, "#FFFFFF"),
             line(-.05, 1.05, 1.05, -.05, .2, "#FFFFFF"),
             line(-.05, -.05, 1.05, 1.05, .07, "#C8102E"),
             line(-.05, 1.05, 1.05, -.05, .07, "#C8102E")]
            + nordic(.5, .34, "#FFFFFF") + nordic(.5, .2, "#C8102E"))


def ring_of_stars(cx, cy, r, sr, c, n=5):
    out = []
    for i in range(n):
        a = math.radians(-90 + i * 360 / n)
        out.append(star(cx + r * math.cos(a) / ASPECT, cy + r * math.sin(a), sr, c))
    return out


# ------------------------------------------------------------------ données
EU, AM, AS, AF, OC = "Europe", "Amériques", "Asie & Moyen-Orient", "Afrique", "Océanie"
REGIONS = [EU, AM, AS, AF, OC]
W = "#FFFFFF"
K = "#000000"

FLAGS = []  # (région, nom, ops)


def add(region, name, *parts):
    ops = []
    for p in parts:
        if isinstance(p, list):
            ops.extend(p)
        else:
            ops.append(p)
    FLAGS.append((region, name, ops))


# ---- Europe
add(EU, "France", V("#0055A4", W, "#EF4135"))
add(EU, "Espagne", H(("#AA151B", 1), ("#F1BF00", 2), ("#AA151B", 1)))
add(EU, "Allemagne", H(K, "#DD0000", "#FFCE00"))
add(EU, "Italie", V("#009246", W, "#CE2B37"))
add(EU, "Belgique", V(K, "#FAE042", "#ED2939"))
add(EU, "Pays-Bas", H("#AE1C28", W, "#21468B"))
add(EU, "Luxembourg", H("#ED2939", W, "#00A1DE"))
add(EU, "Irlande", V("#169B62", W, "#FF883E"))
add(EU, "Roumanie", V("#002B7F", "#FCD116", "#CE1126"))
add(EU, "Pologne", H(W, "#DC143C"))
add(EU, "Ukraine", H("#0057B8", "#FFD700"))
add(EU, "Russie", H(W, "#0039A6", "#D52B1E"))
add(EU, "Autriche", H("#ED2939", W, "#ED2939"))
add(EU, "Hongrie", H("#CE2939", W, "#477050"))
add(EU, "Bulgarie", H(W, "#00966E", "#D62612"))
add(EU, "Lituanie", H("#FDB913", "#006A44", "#C1272D"))
add(EU, "Estonie", H("#0072CE", K, W))
add(EU, "Lettonie", H(("#9E3039", 2), (W, 1), ("#9E3039", 2)))
add(EU, "Portugal", V(("#006600", 2), ("#FF0000", 3)),
    ring(.4, .5, .16, .03, "#FFE000"), circ(.4, .5, .09, W))
add(EU, "Suède", bg("#006AA7"), nordic(.36, .2, "#FECC00"))
add(EU, "Norvège", bg("#BA0C2F"), nordic(.36, .27, W), nordic(.36, .13, "#00205B"))
add(EU, "Danemark", bg("#C8102E"), nordic(.36, .14, W))
add(EU, "Finlande", bg(W), nordic(.36, .2, "#003580"))
add(EU, "Islande", bg("#02529C"), nordic(.36, .27, W), nordic(.36, .13, "#DC1E35"))
add(EU, "Suisse", bg("#DA291C"), rect(.433, .2, .567, .8, W), rect(.3, .4, .7, .6, W))
add(EU, "Royaume-Uni", union_jack())
add(EU, "Grèce", H(*[("#0D5EAF" if i % 2 == 0 else W) for i in range(9)]),
    rect(0, 0, .37, 5 / 9, "#0D5EAF"),
    rect(.148, 0, .222, 5 / 9, W), rect(0, .2222, .37, .3333, W))
add(EU, "Tchéquie", H(W, "#D7141A"), poly([(0, 0), (.5, .5), (0, 1)], "#11457E"))
add(EU, "Slovaquie", H(W, "#0B4EA2", "#EE1C25"))
add(EU, "Slovénie", H(W, "#005DA4", "#ED1C24"))
add(EU, "Croatie", H("#FF0000", W, "#171796"))
add(EU, "Serbie", H("#C6363C", "#0C4076", W))
add(EU, "Géorgie", bg(W), nordic(.5, .2, "#FF0000"),
    small_cross(.25, .25, "#FF0000"), small_cross(.75, .25, "#FF0000"),
    small_cross(.25, .75, "#FF0000"), small_cross(.75, .75, "#FF0000"))
add(EU, "Malte", V(W, "#CF142B"), small_cross(.12, .2, "#8A8A8A"))
add(EU, "Macédoine du Nord", bg("#D20000"),
    [line(.5, .5, .5 + math.cos(math.radians(a)) * 1.2,
          .5 + math.sin(math.radians(a)) * 1.2, .06, "#F8E92E")
     for a in range(0, 360, 45)],
    circ(.5, .5, .17, "#D20000"), circ(.5, .5, .14, "#F8E92E"))

# ---- Amériques
add(AM, "Canada", V(("#D80621", 1), (W, 2), ("#D80621", 1)),
    star(.5, .5, .3, "#D80621", 11, .55))
add(AM, "États-Unis", H(*[("#B22234" if i % 2 == 0 else W) for i in range(13)]),
    rect(0, 0, .4, 7 / 13, "#3C3B6E"),
    [circ(.05 + c * .075, .06 + r * .105, .02, W) for r in range(5) for c in range(5)])
add(AM, "Mexique", V("#006847", W, "#CE1126"), circ(.5, .5, .1, "#A9743A"))
add(AM, "Brésil", bg("#009739"),
    poly([(.5, .09), (.93, .5), (.5, .91), (.07, .5)], "#FEDD00"),
    circ(.5, .5, .21, "#012169"), line(.33, .55, .67, .45, .035, W))
add(AM, "Argentine", H("#74ACDF", W, "#74ACDF"), circ(.5, .5, .07, "#F6B40E"))
add(AM, "Chili", H(W, "#D52B1E"), rect(0, 0, .333, .5, "#0039A6"),
    star(.1667, .25, .11, W))
add(AM, "Colombie", H(("#FCD116", 2), ("#003893", 1), ("#CE1126", 1)))
add(AM, "Pérou", V("#D91023", W, "#D91023"))
add(AM, "Venezuela", H("#FFCC00", "#00247D", "#CF142B"),
    [star(.5 + .2 * math.cos(math.radians(a)), .72 + .2 * math.sin(math.radians(a)),
          .03, W) for a in range(200, 341, 20)])
add(AM, "Équateur", H(("#FFDD00", 2), ("#034EA2", 1), ("#ED1C24", 1)))
add(AM, "Bolivie", H("#D52B1E", "#F9E300", "#007934"))
add(AM, "Paraguay", H("#D52B1E", W, "#0038A8"))
add(AM, "Uruguay", H(*[(W if i % 2 == 0 else "#0038A8") for i in range(9)]),
    rect(0, 0, .296, .444, W), circ(.148, .222, .09, "#FCD116"))
add(AM, "Cuba", H(*[("#002A8F" if i % 2 == 0 else W) for i in range(5)]),
    poly([(0, 0), (.4, .5), (0, 1)], "#CF142B"), star(.13, .5, .11, W))
add(AM, "Costa Rica", H(("#002B7F", 1), (W, 1), ("#CE1126", 2), (W, 1), ("#002B7F", 1)))
add(AM, "Honduras", H("#0073CF", W, "#0073CF"),
    [star(x, y, .045, "#0073CF") for x, y in
     [(.5, .5), (.42, .44), (.42, .56), (.58, .44), (.58, .56)]])
add(AM, "Salvador", H("#0F47AF", W, "#0F47AF"), circ(.5, .5, .1, "#6CC24A"))
add(AM, "Nicaragua", H("#0067C6", W, "#0067C6"),
    poly([(.5, .38), (.56, .6), (.44, .6)], "#F2C300"))
add(AM, "Panama", rect(.5, 0, 1, .5, "#D21034"), rect(0, .5, .5, 1, "#005293"),
    star(.25, .25, .1, "#005293"), star(.75, .75, .1, "#D21034"))
add(AM, "Haïti", H("#00209F", "#D21034"), rect(.4, .35, .6, .65, W))
add(AM, "République dominicaine", rect(0, 0, .5, .5, "#002D62"),
    rect(.5, 0, 1, .5, "#CE1126"), rect(0, .5, .5, 1, "#CE1126"),
    rect(.5, .5, 1, 1, "#002D62"), nordic(.5, .12, W))
add(AM, "Jamaïque", poly([(0, 0), (1, 0), (.5, .5)], "#009B3A"),
    poly([(0, 1), (1, 1), (.5, .5)], "#009B3A"),
    poly([(0, 0), (0, 1), (.5, .5)], K), poly([(1, 0), (1, 1), (.5, .5)], K),
    line(-.05, -.05, 1.05, 1.05, .13, "#FED100"),
    line(-.05, 1.05, 1.05, -.05, .13, "#FED100"))
add(AM, "Bahamas", H("#00ABC9", "#FFC72C", "#00ABC9"),
    poly([(0, 0), (.43, .5), (0, 1)], K))
add(AM, "Trinité-et-Tobago", bg("#CE1126"),
    line(-.05, -.05, 1.05, 1.05, .34, W), line(-.05, -.05, 1.05, 1.05, .22, K))

# ---- Asie & Moyen-Orient
add(AS, "Japon", bg(W), circ(.5, .5, .3, "#BC002D"))
add(AS, "Chine", bg("#DE2910"), star(.17, .27, .15, "#FFDE00"),
    [star(x, y, .05, "#FFDE00") for x, y in [(.33, .1), (.4, .19), (.4, .33), (.33, .42)]])
add(AS, "Corée du Sud", bg(W), pie(.5, .5, .25, 180, 360, "#CD2E3A"),
    pie(.5, .5, .25, 0, 180, "#0047A0"),
    line(.12, .17, .2, .27, .05, K), line(.88, .17, .8, .27, .05, K),
    line(.12, .83, .2, .73, .05, K), line(.88, .83, .8, .73, .05, K))
add(AS, "Inde", H("#FF9933", W, "#138808"), ring(.5, .5, .09, .012, "#000080"))
add(AS, "Indonésie", H("#FF0000", W))
add(AS, "Thaïlande", H(("#A51931", 1), ("#F4F5F8", 1), ("#2D2A4A", 2),
                       ("#F4F5F8", 1), ("#A51931", 1)))
add(AS, "Vietnam", bg("#DA251D"), star(.5, .5, .28, "#FFFF00"))
add(AS, "Philippines", H("#0038A8", "#CE1126"), poly([(0, 0), (.5, .5), (0, 1)], W),
    circ(.1, .5, .05, "#FCD116"))
add(AS, "Singapour", H("#EF3340", W), cres(.2, .25, .15, W),
    ring_of_stars(.345, .24, .1, .028, W))
add(AS, "Taïwan", bg("#FE0000"), rect(0, 0, .5, .5, "#000095"),
    circ(.25, .25, .11, W), circ(.25, .25, .085, "#000095"), circ(.25, .25, .07, W))
add(AS, "Laos", H(("#CE1126", 1), ("#002868", 2), ("#CE1126", 1)), circ(.5, .5, .17, W))
add(AS, "Myanmar", H("#FECB00", "#34B233", "#EA2839"), star(.5, .5, .3, W))
add(AS, "Bangladesh", bg("#006A4E"), circ(.45, .5, .3, "#F42A41"))
add(AS, "Pakistan", bg("#01411C"), rect(0, 0, .25, 1, W), cres(.62, .5, .22, W),
    star(.71, .37, .07, W))
add(AS, "Mongolie", V("#C4272F", "#015197", "#C4272F"), circ(.165, .32, .05, "#FFD900"),
    rect(.14, .45, .19, .75, "#FFD900"))
add(AS, "Kazakhstan", bg("#00AFCA"), circ(.5, .5, .19, "#FEC50C"))
add(AS, "Turquie", bg("#E30A17"), cres(.38, .5, .25, W), star(.57, .5, .08, W))
add(AS, "Iran", H("#239F40", W, "#DA0000"), circ(.5, .5, .06, "#DA0000"))
add(AS, "Irak", H("#CE1126", W, K))
add(AS, "Jordanie", H(K, W, "#007A3D"), poly([(0, 0), (.5, .5), (0, 1)], "#CE1126"),
    star(.1, .5, .05, W, 7))
add(AS, "Liban", H(("#ED1C24", 1), (W, 2), ("#ED1C24", 1)),
    poly([(.5, .2), (.62, .65), (.38, .65)], "#00A651"))
add(AS, "Koweït", H("#007A3D", W, "#CE1126"),
    poly([(0, 0), (.25, .333), (.25, .667), (0, 1)], K))
add(AS, "Émirats arabes unis", H("#00732F", W, K), rect(0, 0, .25, 1, "#FF0000"))
add(AS, "Qatar", bg("#8A1538"),
    poly([(0, 0)] + [((.2 if i % 2 else .3), i / 9) for i in range(10)] + [(0, 1)], W))
add(AS, "Arabie saoudite", bg("#006C35"), rect(.3, .62, .7, .66, W),
    rect(.36, .34, .64, .44, W))
add(AS, "Israël", bg(W), rect(0, .09, 1, .2, "#0038B8"), rect(0, .8, 1, .91, "#0038B8"),
    hexagram(.5, .5, .17, "#0038B8", .02))
add(AS, "Azerbaïdjan", H("#00B5E2", "#EF3340", "#509E2F"), cres(.46, .5, .1, W),
    star(.56, .5, .04, W, 8))
add(AS, "Arménie", H("#D90012", "#0033A0", "#F2A800"))
add(AS, "Yémen", H("#CE1126", W, K))

# ---- Afrique
add(AF, "Maroc", bg("#C1272D"), star(.5, .5, .2, "#006233"), star(.5, .5, .14, "#C1272D"))
add(AF, "Algérie", V("#006233", W), cres(.5, .5, .2, "#D21034"), star(.54, .5, .07, "#D21034"))
add(AF, "Tunisie", bg("#E70013"), circ(.5, .5, .25, W), cres(.48, .5, .17, "#E70013"),
    star(.53, .5, .07, "#E70013"))
add(AF, "Libye", H(("#E70013", 1), (K, 2), ("#239E46", 1)), cres(.5, .5, .13, W),
    star(.57, .5, .04, W))
add(AF, "Égypte", H("#CE1126", W, K), circ(.5, .5, .06, "#C09300"))
add(AF, "Sénégal", V("#00853F", "#FDEF42", "#E31B23"), star(.5, .5, .14, "#00853F"))
add(AF, "Mali", V("#14B53A", "#FCD116", "#CE1126"))
add(AF, "Guinée", V("#CE1126", "#FCD116", "#009460"))
add(AF, "Côte d'Ivoire", V("#F77F00", W, "#009E60"))
add(AF, "Cameroun", V("#007A5E", "#CE1126", "#FCD116"), star(.5, .5, .12, "#FCD116"))
add(AF, "Nigeria", V("#008751", W, "#008751"))
add(AF, "Ghana", H("#CE1126", "#FCD116", "#006B3F"), star(.5, .5, .14, K))
add(AF, "Gabon", H("#009E60", "#FCD116", "#3A75C4"))
add(AF, "Tchad", V("#002664", "#FECB00", "#C60C30"))
add(AF, "Niger", H("#E05206", W, "#0DB02B"), circ(.5, .5, .09, "#E05206"))
add(AF, "Burkina Faso", H("#EF2B2D", "#009E49"), star(.5, .5, .2, "#FCD116"))
add(AF, "Bénin", rect(0, 0, .4, 1, "#008751"), rect(.4, 0, 1, .5, "#FCD116"),
    rect(.4, .5, 1, 1, "#E8112D"))
add(AF, "Éthiopie", H("#078930", "#FCDD09", "#DA121A"), circ(.5, .5, .17, "#0F47AF"),
    star(.5, .5, .12, "#FCDD09"))
add(AF, "Angola", H("#CC092F", K), circ(.5, .5, .12, "#FFCB00"))
add(AF, "Madagascar", rect(0, 0, .33, 1, W), rect(.33, 0, 1, .5, "#FC3D32"),
    rect(.33, .5, 1, 1, "#007E3A"))
add(AF, "Kenya", H((K, 6), (W, 1), ("#BB0000", 6), (W, 1), ("#006600", 6)),
    circ(.5, .5, .13, "#BB0000"), ring(.5, .5, .13, .015, W))
add(AF, "Malawi", H(K, "#CE1126", "#339E35"), pie(.5, .333, .2, 180, 360, "#CE1126"))
add(AF, "Soudan", H("#D21034", W, K), poly([(0, 0), (.3, .5), (0, 1)], "#007229"))
add(AF, "Rwanda", H(("#00A1DE", 2), ("#FAD201", 1), ("#20603D", 1)),
    circ(.82, .25, .1, "#FAD201"))

# ---- Océanie
_stars_au = [star(.75, .13, .06, W, 7, .45), star(.62, .42, .06, W, 7, .45),
             star(.88, .4, .06, W, 7, .45), star(.75, .82, .06, W, 7, .45),
             star(.8, .55, .03, W, 5)]
add(OC, "Australie", bg("#012169"), sub(0, 0, .5, .5, union_jack()),
    star(.25, .75, .13, W, 7, .45), _stars_au)
add(OC, "Nouvelle-Zélande", bg("#012169"), sub(0, 0, .5, .5, union_jack()),
    [s for (x, y) in [(.78, .17), (.65, .45), (.9, .42), (.77, .8)]
     for s in (star(x, y, .07, W), star(x, y, .05, "#CC142B"))])
add(OC, "Fidji", bg("#68BFE5"), sub(0, 0, .5, .5, union_jack()))


# ------------------------------------------------------------------ utilitaires
def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return "".join(c.lower() if c.isalnum() else "_" for c in s).strip("_")


def sort_key(name):
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()


FLAGS.sort(key=lambda f: sort_key(f[1]))
FLAG_BY_NAME = {name: (region, ops) for region, name, ops in FLAGS}
