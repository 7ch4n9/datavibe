"""
factoids.py — Climate factoid reference for Data Vibe / hottest_years_v4

Each entry: year → (headline, body, emoji, source)

This file is for reference / documentation only.
The working FACTOIDS dict (without sources) lives in demo_v4_render.py.
"""

FACTOIDS_WITH_SOURCES = {
    1783: (
        "Laki Eruption cools the planet for two years",
        "",
        "🌋",
        "Grattan, J. & Brayshay, M. (1995). An Amazing and Portentous Summer: "
        "Environmental and Social Responses in Britain to the 1783 Eruption of an "
        "Icelandic Volcano. The Geographical Journal, 161(2), 125–134. "
        "https://doi.org/10.2307/3060016",
    ),
    1815: (
        "Mt. Tambora erupts — 1816 becomes Year Without a Summer",
        "",
        "🌋",
        "Stommel, H. & Stommel, E. (1979). The Year Without a Summer. "
        "Scientific American, 240(6), 176–186. "
        "https://doi.org/10.1038/scientificamerican0679-176",
    ),
    1859: (
        "First oil well drilled in the US",
        "",
        "🛢️",
        "Tyndall, J. (1861). On the Absorption and Radiation of Heat by Gases and "
        "Vapours. Philosophical Magazine, 22(146), 169–194. "
        "Drake Well Museum, Titusville PA records (1859). "
        "https://doi.org/10.1080/14786446108643138",
    ),
    1883: (
        "Krakatoa erupts — global temps drop for two years",
        "",
        "🌋",
        "Self, S. & Rampino, M.R. (1981). The 1883 eruption of Krakatau. "
        "Nature, 294, 699–704. "
        "https://doi.org/10.1038/294699a0",
    ),
    1912: (
        "Mt. Katmai erupts",
        "",
        "🌋",
        "Hildreth, W. & Fierstein, J. (2000). Katmai volcanic cluster and the "
        "great eruption of 1912. GSA Bulletin, 112(10), 1594–1620. "
        "https://doi.org/10.1130/0016-7606(2000)112<1594:KVCATG>2.0.CO;2",
    ),
    1939: (
        "WWII begins — industrial surge drives factory emissions.",
        "",
        "⚔️",
        "Stern, D.I. (2005). Global sulfur emissions from 1850 to 2000. "
        "Chemosphere, 58(2), 163–175. "
        "https://doi.org/10.1016/j.chemosphere.2004.08.022",
    ),
    #1958: (
    #    "Keeling Curve begins — CO₂ at 315 ppm, now 424 ppm",
    #    "",
    #    "📊",
    #    "Keeling, C.D. et al. (1958). The concentration and isotopic abundances "
    #    "of atmospheric carbon dioxide in rural areas. Geochimica et Cosmochimica "
    #    "Acta, 13(4), 322–334. NOAA/Scripps current CO₂: "
    #    "https://gml.noaa.gov/ccgg/trends/",
    #),
    1964: (
        "Mt. Agung erupts, global temperatures drop by 0.5°C for two years.",
        "",
        "🌋",
        "Self, S. & Rampino, M.R. (1988). The relationship between volcanic "
        "eruptions and climate change: still a conundrum? EOS, 69(6), 74–75. "
        "Agung 1963–64 aerosol cooling documented in Hansen, J. et al. (1992) "
        "Potential climate impact of Mount Pinatubo eruption. GRL 19(2). "
        "https://doi.org/10.1029/91GL02788",
    ),
    1976: (
        "Pacific Climate Shift — a sudden reorganization of Pacific Ocean circulation.",
        "",
        "🌊",
        "Trenberth, K.E. & Hurrell, J.W. (1994). Decadal atmosphere-ocean "
        "variations in the Pacific. Climate Dynamics, 9, 303–319. "
        "https://doi.org/10.1007/BF00204745",
    ),
    #1988: (
    #    "James Hansen tells Congress: greenhouse warming is here",
    #    "",
    #    "🎤",
    #    "Hansen, J. (1988). The Greenhouse Effect: Impacts on Current Global "
    #    "Temperature and Regional Heat Waves. Testimony before the U.S. Senate "
    #    "Committee on Energy and Natural Resources, June 23, 1988. "
    #    "https://archive.org/details/HansenSenateTestimony1988",
    #),
    1991: (
        "Mt. Pinatubo erupts, global temperatures drop by 0.6°C for two years.",
        "",
        "🌋",
        "Hansen, J. et al. (1992). Potential climate impact of Mount Pinatubo "
        "eruption. Geophysical Research Letters, 19(2), 215–218. "
        "https://doi.org/10.1029/91GL02788",
    ),
    1998: (
        "Monster El Niño — 1998 becomes the hottest year on record",
        "",
        "🔥",
        "Trenberth, K.E. (1997). The definition of El Niño. Bulletin of the "
        "American Meteorological Society, 78(12), 2771–2777. "
        "NASA GISS Surface Temperature Analysis (GISTEMP v4): "
        "https://data.giss.nasa.gov/gistemp/",
    ),
    2005: (
        "2005 breaks 1998 as the hottest year on record.",
        "",
        "📈",
        "Hansen, J. et al. (2006). Global temperature change. PNAS, 103(39), "
        "14288–14293. "
        "https://doi.org/10.1073/pnas.0606291103",
    ),
    2010: (
        "New record — Russia heat wave & Pakistan floods in same month",
        "",
        "🌡️",
        "Barriopedro, D. et al. (2011). The hot summer of 2010: redrawing the "
        "temperature record map of Europe. Science, 332(6026), 220–224. "
        "https://doi.org/10.1126/science.1201224",
    ),
    2016: (
        "2016 shattered all records, running +1.2°C above the pre-industrial average.",
        "",
        "🔥",
        "NASA GISS (2017). NASA, NOAA Data Show 2016 Warmest Year on Record "
        "Globally. Press release, January 18, 2017. "
        "https://www.nasa.gov/press-release/nasa-noaa-data-show-2016-warmest-year-on-record-globally",
    ),
    2024: (
        "2024: first full calendar year above the 1.5°C.",
        "",
        "🚨",
        "Copernicus Climate Change Service (C3S) (2025). Global Climate "
        "Highlights 2024. ECMWF. "
        "https://climate.copernicus.eu/global-climate-highlights-2024",
    ),
}
