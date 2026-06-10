# chart_svg.py
# Generates a Hellenistic square chart as an SVG with a hand-drawn, calligraphic aesthetic.
# Layout: outer square + inner diamond (connecting outer midpoints) + corner diagonals.
# This creates 12 sections: 8 outer triangles + 4 inner diamond triangles.

from __future__ import annotations

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

    # Outer 8 triangles plus 4 inner diamond sections, with ASC at bottom-left.
    house_polygons = {
        1:  [BL, L,   p_bl],
        2:  [B,  BL,  p_bl],
        3:  [B,  BR,  p_br],
        4:  [BR, B,   p_br],
        5:  [R,  BR,  p_br],
        6:  [p_br, B, C],
        7:  [TR, R,   p_tr],
        8:  [T,  TR,  p_tr],
        9:  [p_tl, T, C],
        10: [TL, T,   p_tl],
        11: [L,  TL,  p_tl],
        12: [p_bl, L, C],
    }

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
