#!/usr/bin/env python3
"""Dark Solvik remap for the embedded modules.

  python3 scripts/solvik_dark.py remap        -> regenerates src/styles/solvik-remap.css
  python3 scripts/solvik_dark.py css FILE...  -> one-off: rewrites light colours in CSS
                                                 declarations of FILE(s) in place
  python3 scripts/solvik_dark.py accent [--from=rose|teal|violet] FILE... -> one-off, after `css`: turns rose or teal
                                                 accents into Solvik lime (status colours kept)

Both use the same property-aware rules: light backgrounds become dark glass,
dark text becomes light, light borders become faint white lines. Saturated
mid-tone fills (buttons, badges, chart colours) are kept.
Re-run `remap` after adding new Tailwind colour classes to modules.
"""
import math, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- colour maths
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def rgb_to_oklch(r, g, b):
    r, g, b = (_lin(x / 255) for x in (r, g, b))
    l = 0.4122214708*r + 0.5363325363*g + 0.0514459929*b
    m = 0.2119034982*r + 0.6806995451*g + 0.1073969566*b
    s = 0.0883024619*r + 0.2817188376*g + 0.6299787005*b
    l, m, s = (math.copysign(abs(x) ** (1/3), x) for x in (l, m, s))
    L = 0.2104542553*l + 0.7936177850*m - 0.0040720468*s
    A = 1.9779984951*l - 2.4285922050*m + 0.4505937099*s
    B = 0.0259040371*l + 0.7827717662*m - 0.8086757660*s
    C = math.hypot(A, B)
    h = math.degrees(math.atan2(B, A)) % 360
    return L, C, h

def parse_color(txt):
    """-> (L, C, h, alpha) or None"""
    t = txt.strip().lower()
    if t == "white": return (1.0, 0.0, 0.0, 1.0)
    if t == "black": return (0.0, 0.0, 0.0, 1.0)
    if t.startswith("#"):
        hx = t[1:]
        if len(hx) in (3, 4): hx = "".join(c*2 for c in hx)
        if len(hx) not in (6, 8): return None
        r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
        a = int(hx[6:8], 16) / 255 if len(hx) == 8 else 1.0
        return (*rgb_to_oklch(r, g, b), a)
    m = re.match(r"rgba?\(([^)]*)\)", t)
    if m:
        parts = [p for p in re.split(r"[\s,/]+", m.group(1).strip()) if p]
        if len(parts) < 3: return None
        try:
            r, g, b = (float(p.rstrip("%")) * (2.55 if p.endswith("%") else 1) for p in parts[:3])
            a = 1.0
            if len(parts) > 3:
                a = float(parts[3].rstrip("%")) / (100 if parts[3].endswith("%") else 1)
        except ValueError:
            return None
        return (*rgb_to_oklch(r, g, b), a)
    m = re.match(r"oklch\(\s*([\d.]+)(%?)\s+([\d.]+)\s+([\d.]+)\s*(?:/\s*([\d.]+)(%?))?\s*\)", t)
    if m:
        L = float(m.group(1)) / (100 if m.group(2) else 1)
        a = 1.0
        if m.group(5): a = float(m.group(5)) / (100 if m.group(6) else 1)
        return (L, float(m.group(3)), float(m.group(4)), a)
    return None

def fmt(L, C, h, a):
    a = round(a, 3)
    base = f"oklch({L:.3f} {C:.3f} {h:.1f}"
    return base + (")" if a >= 0.999 else f" / {a})")

SURFACE = (0.27, 0.012, 160.0, 0.8)    # opaque-ish dark glass (cards, panels, modals)

def _neutral(C, neutral):
    return C < 0.02 if neutral is None else neutral

def map_bg(L, C, h, a, neutral=None):
    if L < 0.8: return None                       # saturated / dark fills stay
    if _neutral(C, neutral):
        if L >= 0.995: return fmt(*SURFACE[:3], SURFACE[3]*a)
        w = 0.05 if L >= 0.95 else 0.09 if L >= 0.9 else 0.13
        return fmt(1, 0, 0, w*a)
    return fmt(0.74, min(max(C*3.5, 0.09), 0.17), h, (0.16 if L > 0.93 else 0.24)*a)

def map_text(L, C, h, a, neutral=None):
    if L >= 0.8: return None
    if _neutral(C, neutral) or (L < 0.45 and C < 0.07): C, h = 0.008, 120.0   # neutral greys pick up Solvik's warm cream
    return fmt(0.98 - 0.42*L, C, h, a)

def map_border(L, C, h, a, neutral=None):
    if L < 0.8: return None
    if _neutral(C, neutral): return fmt(1, 0, 0, 0.12*a)
    return fmt(0.74, min(max(C*3, 0.08), 0.16), h, 0.35*a)

# ------------------------------------------------------------ CSS file rewrite
CAT = {}
for p in ("background", "background-color", "background-image"): CAT[p] = map_bg
for p in ("color", "fill", "stroke", "caret-color", "-webkit-text-fill-color", "text-decoration-color"): CAT[p] = map_text
COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|(?<![-\w])(?:white|black)\b")
DECL_RE = re.compile(r"(?<![-\w])([a-z-]+)(\s*:\s*)([^;{}]+?)(\s*)(;|(?=\}))")

def mapper_for(prop):
    if prop in CAT: return CAT[prop]
    if prop.startswith("border") or prop.startswith("outline") or prop == "column-rule": return map_border
    return None

def rewrite_css(text):
    def decl(m):
        prop, sep, val, ws, end = m.groups()
        fn = mapper_for(prop)
        if not fn: return m.group(0)
        def col(cm):
            c = parse_color(cm.group(0))
            if not c: return cm.group(0)
            out = fn(*c)
            return out or cm.group(0)
        return prop + sep + COLOR_RE.sub(col, val) + ws + end
    return DECL_RE.sub(decl, text)

# ------------------------------------------------------- Tailwind class remap
HUES = "slate gray zinc neutral stone red orange amber yellow lime green emerald teal cyan sky blue indigo violet purple fuchsia pink rose".split()

def tailwind_palette():
    theme = (ROOT / "node_modules/tailwindcss/theme.css").read_text()
    pal = {"white": parse_color("#fff"), "black": parse_color("#000")}
    for m in re.finditer(r"--color-([a-z]+-\d+):\s*([^;]+);", theme):
        pal[m.group(1)] = parse_color(m.group(2))
    return pal

def academic_palette():
    """Academic re-themes indigo/violet; under Solvik both follow the lime ramp."""
    pal = tailwind_palette()
    return {f"{hue}-{n}": pal[f"lime-{n}"] for hue in ("indigo", "violet")
            for n in (50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950)}

ACCENT_COLOR_RE = re.compile(r"oklch\([^)]*\)|#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)")
SEMANTIC = re.compile(r"cancel|danger|error|overdue|reject|absent|missed|delete|destructive", re.I)
LIME_H = 124.0

ACCENT_HUES = {"rose": lambda C, h: C > 0.015 and (h >= 335 or h <= 20),
               "teal": lambda C, h: C > 0.03 and 165 <= h <= 215,
               "violet": lambda C, h: C > 0.04 and 250 <= h <= 300}

def accent_css(text, hue="rose"):
    _rose = ACCENT_HUES[hue]
    def rule(m):
        sel, body = m.group(1), m.group(2)
        if SEMANTIC.search(sel): return m.group(0)
        out = []
        for decl in body.split(";"):
            prop = decl.split(":", 1)[0].strip()
            if SEMANTIC.search(prop) or ":" not in decl:
                out.append(decl); continue
            def swap(cm):
                c = parse_color(cm.group(0))
                if not c or not _rose(c[1], c[2]): return cm.group(0)
                L, C, h, a = c
                return fmt(max(L, 0.62) if L < 0.5 else L, min(C * 1.5, 0.19), LIME_H, a)
            out.append(ACCENT_COLOR_RE.sub(swap, decl))
        return sel + "{" + ";".join(out) + "}"
    return re.sub(r"([^{}]+)\{([^{}]*)\}", rule, text)

UTIL = {
    "bg": ("background-color", map_bg), "text": ("color", map_text),
    "border": ("border-color", map_border), "border-t": ("border-top-color", map_border),
    "border-b": ("border-bottom-color", map_border), "border-l": ("border-left-color", map_border),
    "border-r": ("border-right-color", map_border), "border-x": ("border-inline-color", map_border),
    "border-y": ("border-block-color", map_border), "ring": ("--tw-ring-color", map_border),
    "outline": ("outline-color", map_border), "divide": ("border-color", map_border),
    "from": ("--tw-gradient-from", map_bg), "via": ("--tw-gradient-via", map_bg),
    "to": ("--tw-gradient-to", map_bg), "fill": ("fill", map_text), "stroke": ("stroke", map_text),
}
VARIANTS = {"": "{s}", "hover": "{s}:hover", "focus": "{s}:focus", "focus-visible": "{s}:focus-visible",
            "focus-within": "{s}:focus-within", "active": "{s}:active", "disabled": "{s}:disabled",
            "group-hover": ".group:hover {s}", "placeholder": "{s}::placeholder"}

CLASS_RE = re.compile(
    r"(?<![\w:/-])(?:(" + "|".join(sorted(VARIANTS.keys() - {""}, key=len, reverse=True)) + r"):)?"
    r"(" + "|".join(sorted(UTIL, key=len, reverse=True)) + r")-"
    r"(?:(white|black|(?:" + "|".join(HUES) + r")-\d{2,3})|\[(#[0-9a-fA-F]{3,8})\])"
    r"(?:/(\d{1,3}))?(?![\w-])")

def esc(cls):
    return re.sub(r"([:/\[\]#.%])", r"\\\1", cls)

def gen_remap():
    pal, acad = tailwind_palette(), academic_palette()
    found = set()
    for f in (ROOT / "src").rglob("*.ts*"):
        if "routeTree" in f.name: continue
        for m in CLASS_RE.finditer(f.read_text(errors="ignore")):
            found.add((m.group(0), m.group(1) or "", m.group(2), m.group(3), m.group(4), m.group(5)))
    rules = []
    NEUTRAL = {"white", "black", "slate", "gray", "zinc", "neutral", "stone"}
    def rule(scope, cls, variant, util, color, op, neutral=None):
        prop, fn = UTIL[util]
        if not color: return
        L, C, h, a = color
        if op: a *= int(op) / 100
        out = fn(L, C, h, a, neutral)
        if not out: return
        sel = VARIANTS[variant].format(s="." + esc(cls))
        if util == "divide": sel += " > :not(:last-child)"
        rules.append(f"{scope} {sel} {{ {prop}: {out}; }}")
    for cls, variant, util, name, hexv, op in sorted(found):
        color = parse_color(hexv) if hexv else pal.get(name)
        neutral = (name.split("-")[0] in NEUTRAL) if name else None
        rule(":where(.solvik)", cls, variant, util, color, op, neutral)
        if name and name in acad:
            rule(":where(.solvik .academic-module)", cls, variant, util, acad[name], op, False)
    out = ROOT / "src/styles/solvik-remap.css"
    out.write_text(
        "/* GENERATED by scripts/solvik_dark.py remap: do not edit by hand.\n"
        " * Re-maps light Tailwind colour classes used by the embedded modules onto the\n"
        " * dark Solvik glass theme. :where() keeps specificity low so state variants win. */\n"
        + "\n".join(rules) + "\n")
    print(f"{len(rules)} rules -> {out.relative_to(ROOT)}")

if __name__ == "__main__":
    if sys.argv[1:2] == ["remap"]:
        gen_remap()
    elif sys.argv[1:2] == ["css"]:
        for f in sys.argv[2:]:
            p = pathlib.Path(f); t = p.read_text(); n = rewrite_css(t)
            p.write_text(n); print(f, "changed" if n != t else "unchanged")
    elif sys.argv[1:2] == ["accent"]:
        args = sys.argv[2:]; hue = "rose"
        if args and args[0].startswith("--from="): hue = args.pop(0).split("=", 1)[1]
        for f in args:
            p = pathlib.Path(f); t = p.read_text(); n = accent_css(t, hue)
            p.write_text(n); print(f, "changed" if n != t else "unchanged")
    else:
        print(__doc__)
