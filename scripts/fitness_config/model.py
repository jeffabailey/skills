"""Config model: built-in defaults and the constants every layer shares."""

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

CONFIG_FILENAME = "fitness-config.json"

SECTION_DEFAULTS = {
    "weights": DEFAULT_WEIGHTS,
    "statusThresholds": DEFAULT_STATUS,
    "security": DEFAULT_SECURITY,
    "scoring": DEFAULT_SCORING,
}

# Acceptable absolute deviation from 100 when summing weights, to absorb
# rounding from floating-point overrides without permitting real drift.
WEIGHTS_SUM_TOLERANCE = 0.01

# Supported schema version. ADR-003: any chain config declaring a different
# version is a HARD ERROR, surfaced before any merge is attempted so the CLI
# never produces an effective config from incompatible inputs.
SUPPORTED_SCHEMA_VERSION = 1
