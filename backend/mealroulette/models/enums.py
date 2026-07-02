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


class DishCourse(str, enum.Enum):
    starter = "starter"
    main = "main"
    dessert = "dessert"


class DishStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class VegetableLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    vegetable_main = "vegetable_main"


class ServingTemperature(str, enum.Enum):
    hot = "hot"
    cold = "cold"
    room = "room"
    either = "either"


class RecipeType(str, enum.Enum):
    standard = "standard"
    thermomix = "thermomix"
    other_appliance = "other_appliance"


class DifficultyLevel(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
