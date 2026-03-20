# reader.py
# Formats chart data and calls Claude API to generate the natal reading.

import anthropic
from prompts.system_prompt import SYSTEM_PROMPT

client = anthropic.Anthropic()

GREEK_NAMES = {
    "Sun":     "Helios",
    "Moon":    "Selene",
    "Mercury": "Hermes",
    "Venus":   "Aphrodite",
    "Mars":    "Ares",
    "Jupiter": "Zeus",
    "Saturn":  "Kronos",
}


def format_chart(data: dict) -> str:
    """Format chart data as structured plain text for the Claude prompt."""
    lines = []

    lines.append(f"Native: {data['name']}")
    lines.append(f"Place of birth: {data['place']}")
    lines.append(f"Chart type: {data['sect'].capitalize()} chart")
    lines.append("")

    asc = data["ascendant"]
    mc = data["mc"]
    lines.append(f"ASCENDANT: {asc['sign']} {asc['degree']}°  |  MIDHEAVEN: {mc['sign']} {mc['degree']}°")
    lines.append("")

    lines.append("PLANETS")
    for pname, p in data["planets"].items():
        greek = GREEK_NAMES.get(pname, pname)
        retro = "  (retrograde)" if p["retrograde"] else ""
        dignities = ", ".join(p["dignities"]) if p["dignities"] else "peregrine"
        lines.append(
            f"  {greek:<12} {p['sign']:<14} house {p['house']:<3} {p['degree']}°"
            f"  [{dignities}]{retro}"
        )
    lines.append("")

    lines.append("ASPECTS")
    if data["aspects"]:
        for asp in data["aspects"]:
            a = GREEK_NAMES.get(asp["planet_a"], asp["planet_a"])
            b = GREEK_NAMES.get(asp["planet_b"], asp["planet_b"])
            lines.append(f"  {a} {asp['aspect']} {b}  ({asp['quality']})")
    else:
        lines.append("  None")
    lines.append("")

    lines.append("LOTS")
    for lot_name, lot in data["lots"].items():
        lines.append(
            f"  {lot_name:<12} {lot['sign']:<14} house {lot['house']}  {lot['degree']}°"
        )

    return "\n".join(lines)


def get_reading(chart_data: dict) -> str:
    user_message = (
        "Please give a reading for the following nativity:\n\n"
        + format_chart(chart_data)
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        temperature=1,  # slight variation keeps readings natural; use 0 for exact determinism
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text
