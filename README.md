# Moira

Hellenistic astrology readings powered by the Tetrabiblos and the Claude API.

Cast your nativity and receive a reading as it would have been given in second-century Alexandria — grounded in the doctrines of Claudius Ptolemy, the Greek Lots, and the seven planetary gods.

## Overview

Moira calculates a natal chart using the Swiss Ephemeris and generates a reading via Claude, instructed to reason within the Hellenistic astrological framework as described in Ptolemy's *Tetrabiblos* and Chris Brennan's *Hellenistic Astrology*.

**Astrological features:**
- Whole sign houses
- Essential dignities (domicile, exaltation, triplicity, Egyptian bounds, face/decan)
- Sect (diurnal/nocturnal)
- Greek Lots (Fortune, Spirit, Eros, Necessity, Courage, Victory, Nemesis)
- Whole-sign aspects
- Planetary deity associations

## Stack

- **Backend:** Python, FastAPI, pyswisseph
- **AI:** Anthropic Claude API (`claude-sonnet-4-6`)
- **Frontend:** Vanilla HTML/CSS

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your Anthropic API key to .env

# Run
cd backend
uvicorn main:app --reload
```

## Sources

- Ptolemy, *Tetrabiblos* (c. 150 CE)
- Chris Brennan, *Hellenistic Astrology: The Study of Fate and Fortune* (2017)
