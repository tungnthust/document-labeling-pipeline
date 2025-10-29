"""
Workflow Manager for Document Labeling Pipeline
Orchestrates the 6-step pipeline workflow
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger

from pipeline.api_manager import APIManager
from pipeline.consistency_engine import ConsistencyEngine
from config import (
    OUTPUT_DIR, RAW_LABELS_DIR, UNIFIED_LABELS_DIR,
    CONSISTENT_LABELS_DIR
)


class WorkflowManager:
    """Manages the 6-step pipeline workflow for document labeling"""
    
    def __init__(self):
        self.api_manager = APIManager()
        self.consistency_engine = ConsistencyEngine()
    
    async def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process a single image through the complete 6-step pipeline
        
        Args:
            image_path: Path to the input image
            
        Returns:
            Dictionary containing all results (raw and consistent)
        """
        image_path = Path(image_path)
        image_id = self._get_image_id(image_path)
        
        logger.info(f"Processing image: {image_path.name}")
        
        # Initialize result structure
        pipeline_results = {
            "image_path": str(image_path),
            "image_id": image_id,
            "raw_annotations": {
                "layout_analysis": {},
                "text_extraction": {},
                "table_structure_recognition": {}
            },
            "consistent_annotations": {
                "layout_analysis": {},
                "text_extraction": {},
                "table_structure_recognition": {}
            }
        }
        
        # ===================================================================
        # STEP 1: Call API (Full Image Pass)
        # ===================================================================
        logger.info(f"[Step 1] Calling APIs for full image: {image_path.name}")
        
        layout_results, text_results = await asyncio.gather(
            self.api_manager.call_layout_analysis(str(image_path)),
            self.api_manager.call_text_extraction(str(image_path))
        )
        
        pipeline_results["raw_annotations"]["layout_analysis"] = layout_results
        pipeline_results["raw_annotations"]["text_extraction"] = text_results
        
        # ===================================================================
        # STEP 2: Save Raw Results
        # ===================================================================
        logger.info(f"[Step 2] Saving raw results for: {image_path.name}")
        
        self._save_raw_results(
            layout_results, 
            "layout_analysis", 
            image_id
        )
        self._save_raw_results(
            text_results, 
            "text_extraction", 
            image_id
        )
        
        # ===================================================================
        # STEP 3: Consistency Analysis (Pass 1 - Layout & Text)
        # ===================================================================
        logger.info(f"[Step 3] Analyzing consistency for layout and text: {image_path.name}")
        
        consistent_layout = self.consistency_engine.find_consistent_layout(
            layout_results
        )
        consistent_text = self.consistency_engine.find_consistent_text(
            text_results
        )
        
        pipeline_results["consistent_annotations"]["layout_analysis"] = consistent_layout
        pipeline_results["consistent_annotations"]["text_extraction"] = consistent_text
        
        # ===================================================================
        # STEP 4: Call Dependent API (Table Structure - ROI Pass)
        # ===================================================================
        logger.info(f"[Step 4] Processing table structures: {image_path.name}")
        
        table_results_dict = {}
        table_bboxes = self._extract_table_bboxes(consistent_layout)
        
        logger.info(f"Found {len(table_bboxes)} tables to process")
        
        for table_bbox in table_bboxes:
            table_polygon = table_bbox["polygon"]
            
            # Crop image for this table
            cropped_bytes = self.api_manager.crop_image_from_polygon(
                str(image_path), 
                table_polygon
            )
            
            # Call table structure APIs
            table_results = await self.api_manager.call_table_structure_recognition(
                str(image_path),
                table_polygon,
                cropped_bytes
            )
            
            # Store with polygon as key (serialized)
            polygon_key = self._serialize_polygon(table_polygon)
            table_results_dict[polygon_key] = table_results
        
        pipeline_results["raw_annotations"]["table_structure_recognition"] = table_results_dict
        
        # Save raw table results
        for polygon_key, table_results in table_results_dict.items():
            self._save_raw_table_results(
                table_results,
                image_id,
                polygon_key
            )
        
        # ===================================================================
        # STEP 5: Consistency Analysis (Pass 2 - Table Structure)
        # ===================================================================
        logger.info(f"[Step 5] Analyzing consistency for table structures: {image_path.name}")
        
        consistent_tables = []
        for table_bbox in table_bboxes:
            table_polygon = table_bbox["polygon"]
            polygon_key = self._serialize_polygon(table_polygon)
            
            if polygon_key in table_results_dict:
                table_results = table_results_dict[polygon_key]
                
                consistent_table = self.consistency_engine.find_consistent_table_structure(
                    table_results,
                    table_polygon
                )
                
                if consistent_table:
                    consistent_tables.append(consistent_table)
        
        pipeline_results["consistent_annotations"]["table_structure_recognition"] = {
            "labels": consistent_tables
        }
        
        # ===================================================================
        # STEP 6: Final Storage
        # ===================================================================
        logger.info(f"[Step 6] Saving final results: {image_path.name}")
        
        # Save unified JSON
        self._save_unified_json(pipeline_results, image_id)
        
        # Save consistent labels per task
        self._save_consistent_labels_per_task(pipeline_results, image_id)
        
        logger.success(f"Completed processing: {image_path.name}")
        
        return pipeline_results
    
    async def process_directory(self, input_dir: str) -> List[Dict[str, Any]]:
        """
        Process all images in a directory
        
        Args:
            input_dir: Path to directory containing images
            
        Returns:
            List of results for all processed images
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp'}
        image_files = [
            f for f in input_path.rglob('*') 
            if f.suffix.lower() in image_extensions
        ]
        
        logger.info(f"Found {len(image_files)} images to process in {input_dir}")
        
        # Process each image
        results = []
        for image_file in image_files:
            try:
                result = await self.process_image(str(image_file))
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {image_file}: {e}")
                continue
        
        logger.success(f"Completed processing {len(results)}/{len(image_files)} images")
        
        return results
    
    def _get_image_id(self, image_path: Path) -> str:
        """Generate image ID from path (category_filename_pageId format)"""
        # For now, use filename without extension
        # Can be enhanced to include category and page ID
        return image_path.stem
    
    def _extract_table_bboxes(self, consistent_layout: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract table bboxes from consistent layout results"""
        table_bboxes = []
        
        labels = consistent_layout.get("labels", [])
        for label in labels:
            if label.get("type") == "table":
                table_bboxes.append(label)
        
        return table_bboxes
    
    def _serialize_polygon(self, polygon: List[List[float]]) -> str:
        """Serialize polygon to string for use as dictionary key"""
        return json.dumps(polygon)
    
    def _save_raw_results(
        self, 
        results: Dict[str, Dict[str, Any]], 
        task_name: str, 
        image_id: str
    ):
        """Save raw API results to disk"""
        for service_name, result in results.items():
            output_dir = Path(RAW_LABELS_DIR) / service_name / task_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{image_id}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
    
    def _save_raw_table_results(
        self,
        results: Dict[str, Dict[str, Any]],
        image_id: str,
        polygon_key: str
    ):
        """Save raw table API results to disk"""
        # Create a safe filename from polygon_key
        safe_key = polygon_key.replace('[', '').replace(']', '').replace(',', '_')[:50]
        
        for service_name, result in results.items():
            output_dir = Path(RAW_LABELS_DIR) / service_name / "table_structure_recognition"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{image_id}_{safe_key}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
    
    def _save_unified_json(self, pipeline_results: Dict[str, Any], image_id: str):
        """Save unified JSON containing all results"""
        output_dir = Path(UNIFIED_LABELS_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{image_id}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(pipeline_results, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved unified JSON: {output_file}")
    
    def _save_consistent_labels_per_task(
        self, 
        pipeline_results: Dict[str, Any], 
        image_id: str
    ):
        """Save consistent labels split by task"""
        consistent_annotations = pipeline_results["consistent_annotations"]
        image_path = pipeline_results["image_path"]
        
        # Layout Analysis
        layout_output = {
            "image_path": image_path,
            "labels": consistent_annotations["layout_analysis"].get("labels", []),
            "sources": consistent_annotations["layout_analysis"].get("sources", [])
        }
        
        layout_dir = Path(CONSISTENT_LABELS_DIR) / "layout_analysis"
        layout_dir.mkdir(parents=True, exist_ok=True)
        
        with open(layout_dir / f"{image_id}.json", 'w', encoding='utf-8') as f:
            json.dump(layout_output, f, indent=2, ensure_ascii=False)
        
        # Text Extraction
        text_output = {
            "image_path": image_path,
            "labels": consistent_annotations["text_extraction"].get("labels", []),
            "sources": consistent_annotations["text_extraction"].get("sources", [])
        }
        
        text_dir = Path(CONSISTENT_LABELS_DIR) / "text_extraction"
        text_dir.mkdir(parents=True, exist_ok=True)
        
        with open(text_dir / f"{image_id}.json", 'w', encoding='utf-8') as f:
            json.dump(text_output, f, indent=2, ensure_ascii=False)
        
        # Table Structure Recognition
        table_output = {
            "image_path": image_path,
            "labels": consistent_annotations["table_structure_recognition"].get("labels", [])
        }
        
        table_dir = Path(CONSISTENT_LABELS_DIR) / "table_structure_recognition"
        table_dir.mkdir(parents=True, exist_ok=True)
        
        with open(table_dir / f"{image_id}.json", 'w', encoding='utf-8') as f:
            json.dump(table_output, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved consistent labels per task for: {image_id}")
