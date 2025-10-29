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

# Install dependencies
pip install -r requirements.txt
```

## 📖 Usage

```bash
# Run the pipeline
python main.py --input-dir input_images/ --output-dir output/
```

## 📋 API Services

| Service | Port | Tasks |
|---------|------|-------|
| Landing AI | 9660 | Layout, Text, Table |
| Google Document AI | 9661 | Text Recognition |
| PP-DocLayout | 9662 | Layout |
| PP-OCRv5 | 9663 | Text Recognition |
| Paddle-OCR-VL | 9664 | Table Structure |
| PP-TableMagic | 9665 | Table Structure |
| DeekSeek-OCR | 9666 | Layout, Text, Table |
| dots.ocr | 9667 | Layout, Text, Table |
| MinerU2.5 | 9668 | Layout, Table |
| Surya | 9669 | Text Recognition |
| LORE | 9670 | Table Structure |

## 📄 License

MIT License

## 👥 Contributors

- [tungnthust](https://github.com/tungnthust)
