# Document Labeling Pipeline

## 🎯 Mục tiêu
Xây dựng một pipeline xử lý bằng Python để tự động tạo nhãn (ground truth) cho một tập hợp hình ảnh tài liệu. Pipeline sẽ thực thi các tác vụ trích xuất thông tin theo một luồng phụ thuộc (dependent workflow) để tối ưu hóa việc gọi API và đảm bảo tính chính xác.

## 🚀 Các tác vụ chính

### 1. Layout Analysis
Phân tích bố cục (toàn bộ ảnh) - xác định các vùng text, table, image, v.v.

### 2. Text Extraction (Detection & Recognition)
Phát hiện và nhận dạng văn bản (toàn bộ ảnh)

### 3. Table Structure Recognition
Nhận dạng cấu trúc bảng (dựa trên vùng ROI từ Layout Analysis)

## 📊 Workflow Pipeline

```
Bước 1: Gọi API (Full Image Pass)
   ↓
Bước 2: Lưu trữ kết quả thô (Raw Output Storage)
   ↓
Bước 3: Phân tích nhất quán (Pass 1 - Layout & Text)
   ↓
Bước 4: Gọi API phụ thuộc (Dependent ROI Pass - Table Structure)
   ↓
Bước 5: Phân tích nhất quán (Pass 2 - Table Structure)
   ↓
Bước 6: Tổng hợp và Lưu trữ (Final Storage)
```

## 🏗️ Cấu trúc dự án

```
/document_labeling_pipeline
├── main.py                          # Script chính để chạy pipeline
├── config.py                        # Cấu hình threshold, API URLs, ports
├── requirements.txt                 # Python dependencies
├── README.md                        # Documentation
│
├── pipeline/
│   ├── __init__.py
│   ├── api_manager.py              # Quản lý gọi API (asyncio)
│   ├── consistency_engine.py       # Logic so khớp (BBox, NED, S-TEDS)
│   └── workflow_manager.py         # Điều phối 6 bước của pipeline
│
├── metrics/
│   ├── __init__.py
│   ├── normalized_edit_distance.py # Triển khai NED
│   ├── tree_edit_distance.py       # Triển khai S-TEDS
│   └── overlap_area_ratio.py       # Triển khai IoU/overlap
│
├── input_images/                    # Thư mục chứa ảnh đầu vào
│   └── <category>/
│
└── output/                          # Thư mục kết quả
    ├── raw_labels/                  # Kết quả thô từ API
    │   └── <service_name>/
    │       └── <task_name>/
    ├── unified_labels/              # JSON tổng hợp
    └── consistent_labels_per_task/  # JSON theo từng tác vụ
        ├── layout_analysis/
        ├── text_extraction/
        └── table_structure_recognition/
```

## 📐 Core Consistency Logic

### 4.1. BBox Matching (Layout Analysis & Text Detection)
- **Metric**: IoU (Intersection over Union) hoặc overlap_area_ratio
- **Granularity Preference**: Ưu tiên BBox chi tiết hơn (lines > paragraph)

### 4.2. Text Matching (Text Recognition)
- **Metric**: Normalized Edit Distance (NED)
- **Consistency**: NED = 0 (tuyệt đối nhất quán)

### 4.3. Table Structure Matching
- **Metric**: Tree Edit Distance (S-TEDS)
- **Consistency**: S-TEDS = 0 (tuyệt đối nhất quán)

## 🔧 Installation

```bash
# Clone repository
git clone https://github.com/tungnthust/document-labeling-pipeline.git
cd document-labeling-pipeline

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 📖 Usage

### Basic Usage

```bash
# Process a single image
python main.py --input-dir input_images/sample.jpg

# Process a directory of images
python main.py --input-dir input_images/ --output-dir output/

# Enable verbose logging
python main.py --input-dir input_images/ --verbose
```

### Running Tests

```bash
# Run component tests
python test_pipeline.py
```

### Configuration

Edit `config.py` to customize:
- API endpoints and ports
- Consistency thresholds (IoU, NED, S-TEDS)
- Minimum consensus count
- API timeout and retry settings

Example configuration:
```python
# Consistency Thresholds
IOU_THRESHOLD = 0.5                    # BBox overlap threshold
OVERLAP_AREA_RATIO_THRESHOLD = 0.7    # Overlap ratio for nested bboxes
NED_THRESHOLD = 0.0                    # Text exact match (0 = identical)
TEXT_SIMILARITY_THRESHOLD = 0.95       # Text similarity threshold
STEDS_THRESHOLD = 0.0                  # Table structure exact match
MIN_CONSENSUS_COUNT = 2                # Minimum models in agreement
```

## 📋 API Services

| Service | Port | Tasks | Endpoints |
|---------|------|-------|-----------|
| Landing AI | 9660 | Layout, Text, Table | `/extract` |
| Google Document AI | 9661 | Text Recognition | `/get-text` |
| PP-DocLayout | 9662 | Layout | `/get-layout` |
| PP-OCRv5 | 9663 | Text Recognition | `/get-text` |
| Paddle-OCR-VL | 9664 | Table Structure | `/get-table-structure` |
| PP-TableMagic | 9665 | Table Structure | `/get-table-structure` |
| DeepSeek-OCR | 9666 | Layout, Text, Table | `/get-layout`, `/get-text`, `/get-table-structure` |
| dots.ocr | 9667 | Layout, Text, Table | `/get-layout`, `/get-text`, `/get-table-structure` |
| MinerU2.5 | 9668 | Layout, Table | `/get-layout`, `/get-table-structure` |
| Surya | 9669 | Text Recognition | `/get-text` |
| LORE | 9670 | Table Structure | `/get-table-structure` |

### API Request Format

All APIs expect a JSON request body:
```json
{
  "filepath": "path/to/image.jpg",
  "polygon": [[x1, y1], [x2, y2], ...],  // Optional ROI
  "image_bytes": "base64_encoded_string"  // Optional pre-cropped image
}
```

### API Response Format

APIs should return JSON with task-specific fields:

**Layout Analysis:**
```json
{
  "layout": [
    {"polygon": [[x1, y1], ...], "type": "text"},
    {"polygon": [[x1, y1], ...], "type": "table"}
  ]
}
```

**Text Extraction:**
```json
{
  "text": [
    {"polygon": [[x1, y1], ...], "content": "Hello World"}
  ]
}
```

**Table Structure:**
```json
{
  "html": "<table>...</table>"
}
```

## 📄 License

MIT License

## 🎓 Pipeline Workflow Details

The pipeline follows a **6-step process** for each image:

### Step 1: Full Image API Pass
- Calls all layout analysis APIs (PP-DocLayout, DeepSeek-OCR, dots.ocr, MinerU2.5, Landing AI)
- Calls all text extraction APIs (Google Document AI, PP-OCRv5, DeepSeek-OCR, dots.ocr, Surya, Landing AI)
- All calls made in parallel using asyncio

### Step 2: Raw Output Storage
- Saves all raw API responses to `output/raw_labels/<service>/<task>/<image_id>.json`
- Preserves original API response format for debugging and analysis

### Step 3: Consistency Analysis (Layout & Text)
- Analyzes layout results using IoU/overlap metrics
- Groups matching bounding boxes across services
- Applies granularity preference (prefers finer-grained detections)
- Analyzes text results using spatial + textual similarity (NED)
- Requires minimum consensus from multiple services

### Step 4: Dependent ROI Pass (Tables)
- Extracts table regions from consistent layout results
- Crops table regions from original image
- Calls table structure APIs for each detected table
- Passes cropped image and ROI polygon to APIs

### Step 5: Consistency Analysis (Tables)
- Compares table HTML structures using S-TEDS metric
- Groups tables with identical structure (S-TEDS = 0)
- Selects consensus HTML when multiple services agree

### Step 6: Final Storage
- Saves unified JSON with all raw and consistent results
- Saves task-specific consistent labels separately
- Output ready for training or evaluation

## 📂 Output Structure

```
output/
├── raw_labels/                     # Raw API responses
│   ├── landing_ai/
│   │   ├── layout_analysis/
│   │   │   └── image_001.json
│   │   ├── text_extraction/
│   │   └── table_structure_recognition/
│   ├── google_docai/
│   └── ...
│
├── unified_labels/                 # Complete results per image
│   └── image_001.json
│
└── consistent_labels_per_task/     # Clean labels by task
    ├── layout_analysis/
    │   └── image_001.json
    ├── text_extraction/
    │   └── image_001.json
    └── table_structure_recognition/
        └── image_001.json
```

### Output Format Examples

**Unified Label** (`output/unified_labels/<image_id>.json`):
```json
{
  "image_path": "/path/to/image.jpg",
  "raw_annotations": {
    "layout_analysis": {
      "landing_ai": {...},
      "pp_doclayout": {...}
    },
    "text_extraction": {...},
    "table_structure_recognition": {...}
  },
  "consistent_annotations": {
    "layout_analysis": {
      "labels": [{"type": "text", "polygon": [...]}],
      "sources": ["landing_ai", "pp_doclayout"]
    },
    "text_extraction": {...},
    "table_structure_recognition": {...}
  }
}
```

**Task-Specific Label** (`output/consistent_labels_per_task/layout_analysis/<image_id>.json`):
```json
{
  "image_path": "/path/to/image.jpg",
  "labels": [
    {"type": "text", "polygon": [[x1, y1], ...]},
    {"type": "table", "polygon": [[x1, y1], ...]}
  ],
  "sources": ["landing_ai", "pp_doclayout", "deepseek_ocr"]
}
```

## 🔬 Core Algorithms

### BBox Consistency (Layout & Text Detection)
- **Metric**: IoU (Intersection over Union) and Overlap Ratio
- **Clustering**: Groups spatially overlapping bboxes from different services
- **Granularity Preference**: When a large bbox (paragraph) overlaps with multiple smaller bboxes (lines), prefers the finer-grained detections
- **Consensus**: Requires `MIN_CONSENSUS_COUNT` services to agree

### Text Consistency (Recognition)
- **Metric**: Normalized Edit Distance (NED)
- **Matching**: Combines spatial overlap + text similarity
- **Cross-Granularity**: Joins line-level texts to compare with paragraph-level texts
- **Threshold**: Configurable similarity threshold (default: 95%)

### Table Structure Consistency
- **Metric**: Simplified Tree Edit Distance (S-TEDS)
- **Implementation**: Uses APTED library for tree comparison
- **Exact Match**: Only groups tables with S-TEDS = 0 (identical structure)
- **Voting**: Selects HTML with most consensus across services

## 👥 Contributors

- [tungnthust](https://github.com/tungnthust)
