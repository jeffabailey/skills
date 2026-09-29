"""Config model: built-in defaults and the constants every layer shares."""

CONFIG_FILENAME = "fitness-config.json"

# ADR-003: a config without a `version` is version 1; any other version is a
# hard error, raised before anything is merged.
SUPPORTED_SCHEMA_VERSION = 1

DEFAULT_WEIGHTS = {
    "architecture": 14,
    "security": 14,
    "reliability": 10,
    "testing": 10,
    "performance": 10,
    "algorithms": 10,
    "data": 10,
    "accessibility": 8,
    "process": 8,
    "maintainability": 6,
}

DEFAULT_STATUS = {
    "healthy": [8, 10],
    "needsAttention": [5, 7],
    "critical": [1, 4],
}

DEFAULT_SECURITY = {"confidenceThreshold": 7}

DEFAULT_SCORING = {"goodRange": [8, 10], "badRange": [1, 3]}

# Section name -> its defaults, in canonical (written) order.
SECTION_DEFAULTS = {
    "weights": DEFAULT_WEIGHTS,
    "statusThresholds": DEFAULT_STATUS,
    "security": DEFAULT_SECURITY,
    "scoring": DEFAULT_SCORING,
}

# Absorbs float rounding in overrides when checking that weights sum to 100.
WEIGHTS_SUM_TOLERANCE = 0.01
