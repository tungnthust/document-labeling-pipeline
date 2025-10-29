"""
Configuration file for Document Labeling Pipeline
Contains API endpoints, thresholds, and other settings
"""

from typing import Dict, List
import os

# ============================================================================
# API Configuration
# ============================================================================

BASE_HOST = "localhost"

# API Endpoints with their ports and supported tasks
API_SERVICES = {
    "landing_ai": {
        "host": BASE_HOST,
        "port": 9660,
        "endpoints": {
            "extract": "/extract"  # Layout, Text, Table
        },
        "tasks": ["layout_analysis", "text_extraction", "table_structure_recognition"]
    },
    "google_docai": {
        "host": BASE_HOST,
        "port": 9661,
        "endpoints": {
            "get_text": "/get-text"
        },
        "tasks": ["text_extraction"]
    },
    "pp_doclayout": {
        "host": BASE_HOST,
        "port": 9662,
        "endpoints": {
            "get_layout": "/get-layout"
        },
        "tasks": ["layout_analysis"]
    },
    "pp_ocrv5": {
        "host": BASE_HOST,
        "port": 9663,
        "endpoints": {
            "get_text": "/get-text"
        },
        "tasks": ["text_extraction"]
    },
    "paddle_ocr_vl": {
        "host": BASE_HOST,
        "port": 9664,
        "endpoints": {
            "get_table_structure": "/get-table-structure"
        },
        "tasks": ["table_structure_recognition"]
    },
    "pp_tablemagic": {
        "host": BASE_HOST,
        "port": 9665,
        "endpoints": {
            "get_table_structure": "/get-table-structure"
        },
        "tasks": ["table_structure_recognition"]
    },
    "deepseek_ocr": {
        "host": BASE_HOST,
        "port": 9666,
        "endpoints": {
            "get_layout": "/get-layout",
            "get_text": "/get-text",
            "get_table_structure": "/get-table-structure"
        },
        "tasks": ["layout_analysis", "text_extraction", "table_structure_recognition"]
    },
    "dots_ocr": {
        "host": BASE_HOST,
        "port": 9667,
        "endpoints": {
            "get_layout": "/get-layout",
            "get_text": "/get-text",
            "get_table_structure": "/get-table-structure"
        },
        "tasks": ["layout_analysis", "text_extraction", "table_structure_recognition"]
    },
    "mineru_2_5": {
        "host": BASE_HOST,
        "port": 9668,
        "endpoints": {
            "get_layout": "/get-layout",
            "get_table_structure": "/get-table-structure"
        },
        "tasks": ["layout_analysis", "table_structure_recognition"]
    },
    "surya": {
        "host": BASE_HOST,
        "port": 9669,
        "endpoints": {
            "get_text": "/get-text"
        },
        "tasks": ["text_extraction"]
    },
    "lore": {
        "host": BASE_HOST,
        "port": 9670,
        "endpoints": {
            "get_table_structure": "/get-table-structure"
        },
        "tasks": ["table_structure_recognition"]
    }
}

# Consistency Thresholds
IOU_THRESHOLD = 0.5
OVERLAP_AREA_RATIO_THRESHOLD = 0.7
NED_THRESHOLD = 0.0
TEXT_SIMILARITY_THRESHOLD = 0.95
STEDS_THRESHOLD = 0.0
MIN_CONSENSUS_COUNT = 2

# Directory Structure
INPUT_DIR = "input_images"
OUTPUT_DIR = "output"
RAW_LABELS_DIR = os.path.join(OUTPUT_DIR, "raw_labels")
UNIFIED_LABELS_DIR = os.path.join(OUTPUT_DIR, "unified_labels")
CONSISTENT_LABELS_DIR = os.path.join(OUTPUT_DIR, "consistent_labels_per_task")

# API Request Configuration
API_TIMEOUT = 30
API_MAX_RETRIES = 3
API_RETRY_DELAY = 1
MAX_CONCURRENT_REQUESTS = 10

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
LOG_FILE = "pipeline.log"

def get_api_url(service_name: str, endpoint_key: str) -> str:
    service = API_SERVICES.get(service_name)
    if not service:
        raise ValueError(f"Unknown service: {service_name}")
    endpoint = service["endpoints"].get(endpoint_key)
    if not endpoint:
        raise ValueError(f"Unknown endpoint '{endpoint_key}' for service '{service_name}'")
    return f"http://{service['host']}:{service['port']}{endpoint}"

def get_services_for_task(task_name: str) -> List[str]:
    services = []
    for service_name, service_config in API_SERVICES.items():
        if task_name in service_config["tasks"]:
            services.append(service_name)
    return services
