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
    exact = "exact"
    high = "high"
    medium = "medium"
    low = "low"
    not_recommended = "not_recommended"
    approximate = "approximate"
    measured = "measured"


class ConversionSource(str, enum.Enum):
    manual = "manual"
    seed = "seed"
    llm_suggested = "llm_suggested"


class AggregationStrategy(str, enum.Enum):
    strict_same_dimension = "strict_same_dimension"
    prefer_mass = "prefer_mass"
    prefer_volume = "prefer_volume"
    prefer_count = "prefer_count"
    allow_approximate_conversion = "allow_approximate_conversion"
    never_convert_count = "never_convert_count"


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


class MealPlanStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class MealSlot(str, enum.Enum):
    lunch = "lunch"
    dinner = "dinner"


class MealPlanItemStatus(str, enum.Enum):
    planned = "planned"
    eaten = "eaten"
    skipped = "skipped"
    ate_leftovers = "ate_leftovers"


class ShoppingListStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    completed = "completed"
    archived = "archived"
