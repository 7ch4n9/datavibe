"""
factoids.py  –  Curated and auto-generated temperature factoids.

Usage
-----
from factoids import get_factoids_for_year, FactoidOverlay

# Pre-curated historical events keyed by year
events = get_factoids_for_year(1998)

# Auto-generate from data at render time
overlay = FactoidOverlay(df_global)
overlay.get(year=2016)
"""

from __future__ import annotations
import textwrap
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pandas as pd


# ─── Pre-curated historical climate events ───────────────────────────────────
# Each entry: (year, headline, body, emoji)
CLIMATE_EVENTS: list[tuple[int, str, str, str]] = [
    # 1800s
    (1816, "Year Without a Summer",
     "Mount Tambora's 1815 eruption blanketed the globe in ash, dropping temperatures by up to 3°C. Crop failures caused widespread famine across Europe and North America.",
     "🌋"),
    (1883, "Krakatoa Eruption",
     "The Krakatoa eruption caused global temperatures to drop ~1.2°C for two years, producing brilliant red sunsets that inspired Edvard Munch's 'The Scream'.",
     "🌅"),

    # Early 1900s
    (1910, "Grand Canyon Blizzard",
     "Unusual cold snaps hit the US Southwest. Global temperatures were among the coolest of the 20th century, partly due to low solar activity.",
     "❄️"),
    (1940, "WWII & Temperature Gaps",
     "The chaos of World War II left massive gaps in global weather records — especially over the Pacific and Atlantic where weather ships went dark.",
     "📊"),

    # Mid-20th century
    (1951, "Baseline Era Begins",
     "Scientists chose 1951–1980 as the standard baseline for temperature anomalies — the period when global coverage was good and industrialization was accelerating.",
     "📏"),
    (1963, "Mount Agung Eruption",
     "Agung's eruption injected SO₂ into the stratosphere, cooling global temperatures by ~0.5°C for two years — the last major volcanic cooling of the 20th century.",
     "🌋"),

    # Late 20th century
    (1976, "Great Pacific Climate Shift",
     "A sudden reorganization of Pacific Ocean circulation, triggering a step-change in global temperatures.",
     "🌊"),
    (1982, "El Chichón Eruption",
     "Mexico's El Chichón exploded with unusual sulfur-rich magma, causing 0.5°C of global cooling and disrupting monsoons from India to Africa.",
     "💥"),
    (1991, "Mount Pinatubo Eruption",
     "The largest eruption in 80 years blasted 20 Mt of SO₂ into the stratosphere, cooling Earth by ~0.6°C.",
     "🌋"),
    (1998, "The First Record Year",
     "A monster El Niño sent global temperatures soaring. 1998 became the hottest year ever recorded.",
     "🔥"),

    # 2000s
    (2003, "European Heat Wave",
     "Over 70,000 people died in Europe's deadliest heat wave in recorded history. France alone lost 15,000 lives. Rivers ran dry; Swiss glaciers lost 10% of their volume.",
     "☀️"),
    (2005, "Strongest Atlantic Hurricane Season",
     "Hurricane Katrina struck New Orleans. The 2005 Atlantic season produced a record 28 named storms, linking intensification to record ocean temperatures.",
     "🌀"),
    (2007, "Arctic Sea Ice Record Low",
     "Arctic summer sea ice shrank to its lowest extent ever recorded — 1 million km² below the previous record.",
     "🧊"),

    # 2010s
    (2010, "Record Heat Worldwide",
     "2010 tied 2005 as the hottest year on record at the time. A catastrophic heat wave killed 56,000 in Russia; Pakistan suffered its worst floods in history.",
     "🌡️"),
    (2012, "Sandy & Arctic Records",
     "Hurricane Sandy flooded New York's subway. Arctic sea ice hit a new record low. The U.S. had its warmest year on record with $110 billion in weather damages.",
     "🌊"),
    (2016, "The Hottest Year Ever",
     "2016 shattered all records, running +1.2°C above the pre-industrial average. It was the third consecutive record year.",
     "🔥"),
    (2017, "First $300B Year",
     "Three Category 4+ hurricanes hit the US in a single season (Harvey, Irma, Maria). Total weather-related damage exceeded $300 billion in the US alone.",
     "💸"),
    (2019, "Amazon Fires & Greenland Melt",
     "Greenland lost a record 532 billion tonnes of ice. The Amazon saw 80,000 fires.",
     "🔥"),

    # 2020s
    (2020, "Coldest La Niña Year … Still Hottest on Record",
     "Despite a La Niña cooling effect, 2020 tied 2016 as the hottest year ever.",
     "🏆"),
    (2021, "Heat Dome Hits Pacific Northwest",
     "Lytton, Canada hit 49.6°C — hotter than anywhere in Europe in history. Over 1,400 died in the heat.",
     "💀"),
    (2022, "Pakistan Floods — One-Third Underwater",
     "Record monsoon rains — boosted by heat that evaporated more water — submerged one-third of Pakistan. 1,700 died; $30 billion in damages.",
     "🌊"),
    (2023, "Hottest Year in 125,000 Years",
     "Global average temperature hit 1.48°C above pre-industrial levels. July 2023 was the hottest month in recorded history — and likely in 120,000 years.",
     "🔥"),
    (2024, "First Year Above 1.5°C",
     "For the first time, a full calendar year averaged more than 1.5°C above pre-industrial temperatures.",
     "🚨"),
]


# ─── Dataclass for a single factoid ─────────────────────────────────────────
@dataclass
class Factoid:
    year: int
    headline: str
    body: str
    emoji: str = "🌡️"
    source: str = ""
    # render state (set at draw time)
    alpha: float = 0.0
    visible: bool = False

    def wrapped_body(self, width: int = 55) -> str:
        """Return body text wrapped to `width` chars per line."""
        return "\n".join(textwrap.wrap(self.body, width))


# ─── Lookup helpers ──────────────────────────────────────────────────────────
def get_factoids_for_year(year: int) -> list[Factoid]:
    """Return all pre-curated Factoid objects for a given year."""
    return [
        Factoid(y, h, b, e)
        for (y, h, b, e) in CLIMATE_EVENTS
        if y == year
    ]


def get_all_factoid_years() -> list[int]:
    return sorted({y for (y, *_) in CLIMATE_EVENTS})


# ─── Auto-generated factoids from data ───────────────────────────────────────
class FactoidOverlay:
    """
    Generates contextual factoids during animation by scanning temperature data.

    Parameters
    ----------
    df_global : pd.DataFrame
        DataFrame with columns ['year', 'anomaly'] — global mean annual anomaly.
    df_cities : pd.DataFrame, optional
        DataFrame with columns ['year', 'city', 'anomaly'] — city-level data.
    """

    def __init__(self,
                 df_global: pd.DataFrame,
                 df_cities: Optional[pd.DataFrame] = None):
        self._global = df_global.sort_values("year").reset_index(drop=True)
        self._cities = df_cities
        self._cache: dict[int, list[Factoid]] = {}
        self._precompute()

    def _precompute(self) -> None:
        """Build factoid list for every year in the dataset."""
        years = self._global["year"].tolist()
        anomalies = self._global["anomaly"].tolist()

        running_max = -99.0

        for i, (yr, anom) in enumerate(zip(years, anomalies)):
            facts: list[Factoid] = []

            # 1. Pre-curated events
            facts.extend(get_factoids_for_year(yr))

            # 2. Running record hot year
            if anom > running_max + 0.02:
                running_max = anom
                if i > 10:   # skip the noisy early data
                    prev_records = [y for y, a in zip(years[:i], anomalies[:i])
                                    if a > anomalies[i-1]]
                    facts.append(Factoid(
                        year=yr,
                        headline=f"🏆 {yr} is now the hottest year on record",
                        body=(f"At +{anom:+.2f}°C above the 1951–1980 average, "
                              f"{yr} beats the previous record "
                              f"by {anom - max(anomalies[:i], default=anom):.2f}°C."),
                        emoji="🏆",
                    ))

            # 3. Decade milestones
            if yr % 10 == 0 and i >= 10:
                decade_anom = np.mean(anomalies[max(0, i-10):i])
                baseline_anom = np.mean(anomalies[:min(30, i)])
                facts.append(Factoid(
                    year=yr,
                    headline=f"The {yr}s — a decade in review",
                    body=(f"The past 10 years averaged {decade_anom:+.2f}°C above the "
                          f"1951–1980 baseline. That's "
                          f"{decade_anom - baseline_anom:+.2f}°C warmer than the "
                          f"first decade of records."),
                    emoji="📅",
                ))

            self._cache[yr] = facts

    def get(self, year: int) -> list[Factoid]:
        return self._cache.get(year, [])

    def all_years_with_factoids(self) -> list[int]:
        return [y for y, fs in self._cache.items() if fs]
