"""
Example Configuration File for Different Scenarios
Copy sections to config.py to customize the pipeline
"""

# =============================================================================
# SCENARIO 1: High Precision (Strict Consensus)
# Use when you need high-quality labels with strong agreement
# =============================================================================

# Strict thresholds requiring strong spatial overlap
IOU_THRESHOLD = 0.7
OVERLAP_AREA_RATIO_THRESHOLD = 0.8

# Require exact text matches
NED_THRESHOLD = 0.0
TEXT_SIMILARITY_THRESHOLD = 1.0  # 100% match required

# Exact table structure match
STEDS_THRESHOLD = 0.0

# Require more services to agree
MIN_CONSENSUS_COUNT = 3

# =============================================================================
# SCENARIO 2: High Recall (Relaxed Consensus)
# Use when you want to capture as many annotations as possible
# =============================================================================

# Relaxed thresholds allowing more overlap tolerance
IOU_THRESHOLD = 0.3
OVERLAP_AREA_RATIO_THRESHOLD = 0.5

# Allow some text variation
NED_THRESHOLD = 0.0
TEXT_SIMILARITY_THRESHOLD = 0.85  # 85% similarity

# Allow slight table structure differences
STEDS_THRESHOLD = 0.1

# Require fewer services to agree
MIN_CONSENSUS_COUNT = 2

# =============================================================================
# SCENARIO 3: Balanced (Default)
# Good balance between precision and recall
# =============================================================================

# Moderate thresholds
IOU_THRESHOLD = 0.5
OVERLAP_AREA_RATIO_THRESHOLD = 0.7

# High text similarity but not exact
NED_THRESHOLD = 0.0
TEXT_SIMILARITY_THRESHOLD = 0.95

# Exact table structure
STEDS_THRESHOLD = 0.0

# Standard consensus requirement
MIN_CONSENSUS_COUNT = 2

# =============================================================================
# SCENARIO 4: Fast Processing (Fewer API Calls)
# Use when you have limited API resources or need faster processing
# =============================================================================

# Disable some services by removing them from API_SERVICES
API_SERVICES_FAST = {
    "landing_ai": {
        "host": "localhost",
        "port": 9660,
        "endpoints": {"extract": "/extract"},
        "tasks": ["layout_analysis", "text_extraction", "table_structure_recognition"]
    },
    "pp_doclayout": {
        "host": "localhost",
        "port": 9662,
        "endpoints": {"get_layout": "/get-layout"},
        "tasks": ["layout_analysis"]
    },
    "google_docai": {
        "host": "localhost",
        "port": 9661,
        "endpoints": {"get_text": "/get-text"},
        "tasks": ["text_extraction"]
    },
    "paddle_ocr_vl": {
        "host": "localhost",
        "port": 9664,
        "endpoints": {"get_table_structure": "/get-table-structure"},
        "tasks": ["table_structure_recognition"]
    }
}

# Lower minimum consensus since fewer services
MIN_CONSENSUS_COUNT = 1

# Increase concurrent requests for faster processing
MAX_CONCURRENT_REQUESTS = 20

# =============================================================================
# SCENARIO 5: Development/Testing (Mock Services)
# Use for testing without actual API services
# =============================================================================

# Point all services to a mock server
BASE_HOST = "localhost"
MOCK_SERVER_PORT = 8888

# Reduce timeouts for faster failure
API_TIMEOUT = 5
API_MAX_RETRIES = 1

# Minimal consensus for testing
MIN_CONSENSUS_COUNT = 1

# =============================================================================
# Performance Tuning Parameters
# =============================================================================

# For high-throughput scenarios
MAX_CONCURRENT_REQUESTS = 50  # Increase for better parallelism
API_TIMEOUT = 60              # Increase for slower services
API_MAX_RETRIES = 5           # Increase for unreliable networks

# For resource-constrained scenarios
MAX_CONCURRENT_REQUESTS = 5   # Decrease to reduce memory usage
API_TIMEOUT = 15              # Decrease to fail fast
API_MAX_RETRIES = 2           # Decrease to save time

# =============================================================================
# Logging Configuration Examples
# =============================================================================

# Development logging (verbose)
LOG_LEVEL = "DEBUG"
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# Production logging (concise)
LOG_LEVEL = "INFO"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"

# JSON logging (for structured logs)
LOG_FORMAT = "{message}"
# Note: Would need custom logger setup for JSON

# =============================================================================
# Custom Service Configuration
# Example: Adding a new service
# =============================================================================

CUSTOM_SERVICE_EXAMPLE = {
    "my_custom_ocr": {
        "host": "api.myservice.com",  # Can be external hostname
        "port": 443,                   # HTTPS port
        "endpoints": {
            "get_text": "/api/v1/ocr",
            "get_layout": "/api/v1/layout"
        },
        "tasks": ["layout_analysis", "text_extraction"]
    }
}

# To use, add to API_SERVICES in config.py:
# API_SERVICES["my_custom_ocr"] = CUSTOM_SERVICE_EXAMPLE["my_custom_ocr"]
