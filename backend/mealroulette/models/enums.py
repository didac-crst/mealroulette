import enum


class UnitDimension(str, enum.Enum):
    mass = "mass"
    volume = "volume"
    count = "count"


class SeasonalityMode(str, enum.Enum):
    all_year = "all_year"
    seasonal = "seasonal"
    avoid = "avoid"
    strict = "strict"


class SeasonalityStrength(str, enum.Enum):
    neutral = "neutral"
    low = "low"
    medium = "medium"
    strong = "strong"


class ConversionConfidence(str, enum.Enum):
    approximate = "approximate"
    measured = "measured"
