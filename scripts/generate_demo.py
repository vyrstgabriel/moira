"""Regenerate the checked-in Augustus demo (one Claude request)."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from main import DEMO_READING_PATH, augustus_demo_data  # noqa: E402
from reader import get_reading  # noqa: E402


def main() -> None:
    _, chart_data = augustus_demo_data()
    reading = get_reading(chart_data)
    DEMO_READING_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEMO_READING_PATH.write_text(reading.strip() + "\n", encoding="utf-8")
    print(f"Saved pre-generated demo to {DEMO_READING_PATH}")


if __name__ == "__main__":
    main()
