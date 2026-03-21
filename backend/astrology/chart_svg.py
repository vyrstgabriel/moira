# chart_svg.py
# Generates a Hellenistic square chart as an SVG with a hand-drawn, calligraphic aesthetic.
# Layout: outer square + inner diamond (connecting outer midpoints) + corner diagonals.
# This creates 12 sections: 8 outer triangles + 4 inner diamond triangles.

from __future__ import annotations
from astrology.chart import SIGNS

PLANET_GLYPHS = {
    "Sun":     "☉",
    "Moon":    "☽",
    "Mercury": "☿",
    "Venus":   "♀",
    "Mars":    "♂",
    "Jupiter": "♃",
    "Saturn":  "♄",
}

SIGN_GLYPHS = {
    "Aries":       "♈", "Taurus":      "♉", "Gemini":      "♊",
    "Cancer":      "♋", "Leo":         "♌", "Virgo":       "♍",
    "Libra":       "♎", "Scorpio":     "♏", "Sagittarius": "♐",
    "Capricorn":   "♑", "Aquarius":    "♒", "Pisces":      "♓",
}


def _pt(x, y):
    return f"{x:.1f},{y:.1f}"


def _polygon(points, cls):
    pts = " ".join(_pt(x, y) for x, y in points)
    return f'<polygon points="{pts}" class="{cls}" />'


def _text(x, y, content, cls, anchor="middle"):
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" class="{cls}">{content}</text>'


def _centroid(points):
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    return cx, cy


def generate_chart_svg(chart, chart_data: dict) -> str:
    SIZE   = 480
    MARGIN = 30
    S      = SIZE - 2 * MARGIN   # outer square side length
    OX, OY = MARGIN, MARGIN       # outer square origin

    # Key coordinates
    TL = (OX,         OY)
    TR = (OX + S,     OY)
    BR = (OX + S,     OY + S)
    BL = (OX,         OY + S)

    # Inner diamond vertices at outer square midpoints
    T  = (OX + S/2,   OY)
    R  = (OX + S,     OY + S/2)
    B  = (OX + S/2,   OY + S)
    L  = (OX,         OY + S/2)
    C  = (OX + S/2,   OY + S/2)

    # Intersection of corner diagonals with inner diamond sides
    # TL-to-C diagonal meets T→L diamond side at (OX + S/4, OY + S/4)
    p_tl = (OX + S/4,     OY + S/4)
    p_tr = (OX + 3*S/4,   OY + S/4)
    p_br = (OX + 3*S/4,   OY + 3*S/4)
    p_bl = (OX + S/4,     OY + 3*S/4)

    # ── 12 house sections ──────────────────────────────────────────────
    # Outer 8 triangles (2 per corner), then 4 inner diamond sections.
    # Traditional layout with ASC at bottom-left corner, houses counterclockwise.
    #
    #   [ 9 ][ 10][ 11]
    #   [ 8 ][    ][ 12]
    #   [ 7 ][ 6 ][ 5 ]   ← outer ring  (but rotated: ASC=left here)
    #
    # Standard Hellenistic square (ASC = left side, MC = top):
    # House 1  = left outer triangle (upper)      L corner, above diagonal
    # House 2  = left outer triangle (lower)      L corner, below diagonal
    # House 3  = inner left diamond section       cadent
    # House 4  = bottom outer triangle (left)     BL corner upper
    # House 5  = bottom outer triangle (right)    BL corner lower  (or B corner)
    # House 6  = inner bottom diamond section
    # House 7  = right outer triangle (lower)     R corner
    # House 8  = right outer triangle (upper)
    # House 9  = inner right diamond section
    # House 10 = top outer triangle (right)       MC
    # House 11 = top outer triangle (left)
    # House 12 = inner top diamond section
    #
    # Simpler and more consistent with the image — ASC at bottom-left:
    # Going counterclockwise from bottom-left:

    house_polygons = {
        1:  [BL, L,  p_bl],          # bottom-left, left side
        2:  [BL, B,  p_bl],          # bottom-left, bottom side
        3:  [B,  BR, p_br],          # bottom-right, bottom side
        4:  [BR, R,  p_br],          # bottom-right, right side
        5:  [R,  TR, p_tr],          # top-right, right side
        6:  [TR, T,  p_tr],          # top-right, top side
        7:  [T,  TL, p_tl],          # top-left, top side
        8:  [TL, L,  p_tl],          # top-left, left side
        # inner diamond sections (cadent houses)
        9:  [p_tl, T,  C],           # inner top-left
        10: [T,  p_tr, C],           # inner top-right  (MC region)
        11: [p_tr, R,  C],           # inner right
        12: [R,  p_br, C],           # inner bottom-right
        # note: this leaves BL area split as houses 1&2, which is correct
    }

    # Reassign inner sections more evenly — 4 inner triangles for 3,6,9,12
    house_polygons[3]  = [B,  BR, p_br]
    house_polygons[6]  = [p_br, B,  C]
    house_polygons[9]  = [p_tl, T,  C]
    house_polygons[12] = [p_bl, L,  C]

    # Redo outer ring cleanly: 8 triangles for houses 1,2,4,5,7,8,10,11
    house_polygons[1]  = [BL, L,   p_bl]
    house_polygons[2]  = [B,  BL,  p_bl]
    house_polygons[4]  = [BR, B,   p_br]
    house_polygons[5]  = [R,  BR,  p_br]
    house_polygons[7]  = [TR, R,   p_tr]
    house_polygons[8]  = [T,  TR,  p_tr]
    house_polygons[10] = [TL, T,   p_tl]
    house_polygons[11] = [L,  TL,  p_tl]

    # Build planet-per-house index
    planet_houses: dict[int, list[str]] = {h: [] for h in range(1, 13)}
    for pname, p in chart_data["planets"].items():
        glyph = PLANET_GLYPHS.get(pname, pname[0])
        retro = "℞" if p["retrograde"] else ""
        planet_houses[p["house"]].append(f"{glyph}{retro}")

    # ── SVG output ─────────────────────────────────────────────────────
    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">'
    )

    out.append("""
<defs>
  <!-- Hand-drawn wobble filter -->
  <filter id="roughen" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="4"
                  seed="7" result="noise"/>
    <feDisplacementMap in="SourceGraphic" in2="noise"
                       scale="2.2" xChannelSelector="R" yChannelSelector="G"/>
  </filter>

  <!-- Ink bleed for text -->
  <filter id="inkbleed">
    <feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="3"
                  seed="3" result="noise"/>
    <feDisplacementMap in="SourceGraphic" in2="noise"
                       scale="0.8" xChannelSelector="R" yChannelSelector="G"/>
  </filter>

  <style>
    svg { background: #f5ecd7; }
    .cell    { fill: #f5ecd7; stroke: none; }
    .frame   { fill: none; stroke: #2c1a0e; stroke-width: 2.2; }
    .line    { fill: none; stroke: #2c1a0e; stroke-width: 1.1; }
    .diag    { fill: none; stroke: #2c1a0e; stroke-width: 0.9; opacity: 0.7; }
    .house-n { font: 700 9px Palatino, Georgia, serif; fill: #7a5c3a; }
    .sign-g  { font: 22px "Apple Symbols", "Segoe UI Symbol", "Noto Sans Symbols", Georgia, serif;
               fill: #2c1a0e; }
    .planet  { font: 19px "Apple Symbols", "Segoe UI Symbol", "Noto Sans Symbols", Georgia, serif;
               fill: #7a1a0a; }
    .asc-tag { font: italic bold 8px Palatino, Georgia, serif;
               fill: #7a5c3a; letter-spacing: 0.5px; }
  </style>
</defs>
""")

    # Background fill
    out.append(f'<rect x="0" y="0" width="{SIZE}" height="{SIZE}" fill="#f5ecd7"/>')

    # Draw house cells (fill only, no stroke — lines drawn separately)
    for h, pts in house_polygons.items():
        out.append(_polygon(pts, "cell"))

    # Draw all structural lines with wobble filter
    out.append('<g filter="url(#roughen)">')

    # Outer square
    out.append(
        f'<rect class="frame" x="{OX}" y="{OY}" width="{S}" height="{S}"/>'
    )

    # Inner diamond
    out.append(
        f'<polygon class="line" points="{_pt(*T)} {_pt(*R)} {_pt(*B)} {_pt(*L)}"/>'
    )

    # Corner diagonals (outer corner → centre)
    for corner in [TL, TR, BR, BL]:
        out.append(
            f'<line class="diag" x1="{corner[0]:.1f}" y1="{corner[1]:.1f}" '
            f'x2="{C[0]:.1f}" y2="{C[1]:.1f}"/>'
        )

    out.append('</g>')  # end roughen group

    # Text (ink-bleed filter for slight imperfection)
    out.append('<g filter="url(#inkbleed)">')

    for h, pts in house_polygons.items():
        cx, cy = _centroid(pts)
        house_sign = chart.houses[h - 1]
        sign_glyph = SIGN_GLYPHS[house_sign]
        planets_here = planet_houses[h]

        # House number (small, nudged toward a corner of the cell)
        out.append(_text(cx - 8, cy - 9, str(h), "house-n", anchor="end"))

        # Sign glyph
        out.append(_text(cx, cy + 3, sign_glyph, "sign-g"))

        # Planet glyphs below sign
        if planets_here:
            out.append(_text(cx, cy + 20, "  ".join(planets_here), "planet"))

        # ASC label
        if h == 1:
            out.append(_text(cx, cy + 34, "ASC", "asc-tag"))

    out.append('</g>')  # end inkbleed group

    out.append('</svg>')
    return "\n".join(out)
