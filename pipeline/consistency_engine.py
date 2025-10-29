"""
Consistency Engine for Document Labeling Pipeline
Implements logic for finding consistent labels across multiple models
"""

from typing import Dict, List, Any, Tuple, Optional, Set
from collections import defaultdict
from loguru import logger
import numpy as np

from metrics import (
    calculate_iou, calculate_overlap_ratio, 
    calculate_ned, normalize_text,
    calculate_steds
)
from config import (
    IOU_THRESHOLD, OVERLAP_AREA_RATIO_THRESHOLD,
    NED_THRESHOLD, TEXT_SIMILARITY_THRESHOLD,
    STEDS_THRESHOLD, MIN_CONSENSUS_COUNT
)


class BBoxCluster:
    """Represents a cluster of matching bounding boxes from different sources"""
    
    def __init__(self, initial_bbox: Dict[str, Any], source: str):
        self.bboxes = [initial_bbox]
        self.sources = [source]
        self.polygon = initial_bbox.get("polygon", [])
        self.bbox_type = initial_bbox.get("type", "unknown")
        self.content = initial_bbox.get("content", "")
    
    def add_bbox(self, bbox: Dict[str, Any], source: str):
        """Add a matching bbox to this cluster"""
        self.bboxes.append(bbox)
        self.sources.append(source)
    
    def get_consensus_bbox(self) -> Dict[str, Any]:
        """Get the consensus bounding box (average or most common)"""
        # For now, return the bbox from the first source
        # Can be improved to average polygons or select based on confidence
        result = {
            "polygon": self.polygon,
            "sources": self.sources,
            "consensus_count": len(self.sources)
        }
        
        if self.bbox_type:
            result["type"] = self.bbox_type
        
        if self.content:
            result["content"] = self.content
        
        return result
    
    def has_consensus(self) -> bool:
        """Check if this cluster has enough sources for consensus"""
        return len(self.sources) >= MIN_CONSENSUS_COUNT


class ConsistencyEngine:
    """Engine for finding consistent labels across multiple model outputs"""
    
    def __init__(self):
        pass
    
    def find_consistent_layout(
        self,
        raw_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Find consistent layout annotations from multiple sources
        
        Args:
            raw_results: Dictionary mapping service_name -> API response
            
        Returns:
            Dictionary with consistent layout labels and sources
        """
        logger.info(f"Finding consistent layout from {len(raw_results)} sources")
        
        # Extract bboxes from each source
        all_bboxes = []
        for service_name, result in raw_results.items():
            if "error" in result:
                logger.warning(f"Skipping {service_name} due to error")
                continue
            
            bboxes = self._extract_layout_bboxes(result)
            for bbox in bboxes:
                all_bboxes.append({
                    "bbox": bbox,
                    "source": service_name
                })
        
        logger.debug(f"Total bboxes extracted: {len(all_bboxes)}")
        
        # Cluster matching bboxes
        clusters = self._cluster_bboxes_by_overlap(all_bboxes)
        
        # Filter clusters with consensus
        consistent_labels = []
        sources_used = set()
        
        for cluster in clusters:
            if cluster.has_consensus():
                consistent_labels.append(cluster.get_consensus_bbox())
                sources_used.update(cluster.sources)
        
        logger.info(f"Found {len(consistent_labels)} consistent layout labels from {len(sources_used)} sources")
        
        return {
            "labels": consistent_labels,
            "sources": sorted(list(sources_used))
        }
    
    def find_consistent_text(
        self,
        raw_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Find consistent text annotations from multiple sources
        
        Args:
            raw_results: Dictionary mapping service_name -> API response
            
        Returns:
            Dictionary with consistent text labels and sources
        """
        logger.info(f"Finding consistent text from {len(raw_results)} sources")
        
        # Extract text bboxes from each source
        all_text_bboxes = []
        for service_name, result in raw_results.items():
            if "error" in result:
                logger.warning(f"Skipping {service_name} due to error")
                continue
            
            text_bboxes = self._extract_text_bboxes(result)
            for bbox in text_bboxes:
                all_text_bboxes.append({
                    "bbox": bbox,
                    "source": service_name
                })
        
        logger.debug(f"Total text bboxes extracted: {len(all_text_bboxes)}")
        
        # Cluster matching text bboxes (spatial + textual similarity)
        clusters = self._cluster_text_bboxes(all_text_bboxes)
        
        # Filter clusters with consensus
        consistent_labels = []
        sources_used = set()
        
        for cluster in clusters:
            if cluster.has_consensus():
                label = cluster.get_consensus_bbox()
                consistent_labels.append(label)
                sources_used.update(cluster.sources)
        
        logger.info(f"Found {len(consistent_labels)} consistent text labels from {len(sources_used)} sources")
        
        return {
            "labels": consistent_labels,
            "sources": sorted(list(sources_used))
        }
    
    def find_consistent_table_structure(
        self,
        raw_results: Dict[str, Dict[str, Any]],
        table_polygon: List[List[float]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find consistent table structure from multiple sources
        
        Args:
            raw_results: Dictionary mapping service_name -> API response for a table
            table_polygon: The polygon coordinates of the table
            
        Returns:
            Dictionary with consistent table HTML and sources, or None if no consensus
        """
        logger.info(f"Finding consistent table structure from {len(raw_results)} sources")
        
        # Extract HTML from each source
        html_groups = defaultdict(list)  # html -> [sources]
        
        for service_name, result in raw_results.items():
            if "error" in result:
                logger.warning(f"Skipping {service_name} due to error")
                continue
            
            html = self._extract_table_html(result)
            if html:
                # Group by S-TEDS similarity
                found_match = False
                for existing_html in list(html_groups.keys()):
                    steds = calculate_steds(html, existing_html)
                    if steds <= STEDS_THRESHOLD:
                        html_groups[existing_html].append(service_name)
                        found_match = True
                        break
                
                if not found_match:
                    html_groups[html] = [service_name]
        
        # Find the HTML with most consensus
        best_html = None
        best_sources = []
        max_consensus = 0
        
        for html, sources in html_groups.items():
            if len(sources) > max_consensus:
                max_consensus = len(sources)
                best_html = html
                best_sources = sources
        
        # Check if we have consensus
        if max_consensus >= MIN_CONSENSUS_COUNT:
            logger.info(f"Found consistent table structure with {max_consensus} sources in agreement")
            return {
                "crop_polygon": table_polygon,
                "html": best_html,
                "sources": sorted(best_sources)
            }
        
        logger.warning(f"No consensus for table structure (max agreement: {max_consensus})")
        return None
    
    def _extract_layout_bboxes(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract layout bboxes from API response"""
        bboxes = []
        
        # Handle different response formats
        if "layout" in api_response:
            layout_data = api_response["layout"]
            if isinstance(layout_data, list):
                bboxes = layout_data
            elif isinstance(layout_data, dict) and "regions" in layout_data:
                bboxes = layout_data["regions"]
        elif "regions" in api_response:
            bboxes = api_response["regions"]
        elif "results" in api_response:
            results = api_response["results"]
            if isinstance(results, list):
                bboxes = results
        
        # Ensure each bbox has required fields
        normalized_bboxes = []
        for bbox in bboxes:
            if "polygon" in bbox or "bbox" in bbox:
                normalized_bbox = {
                    "polygon": bbox.get("polygon", bbox.get("bbox", [])),
                    "type": bbox.get("type", bbox.get("label", "unknown"))
                }
                normalized_bboxes.append(normalized_bbox)
        
        return normalized_bboxes
    
    def _extract_text_bboxes(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract text bboxes from API response"""
        text_bboxes = []
        
        # Handle different response formats
        if "text" in api_response:
            text_data = api_response["text"]
            if isinstance(text_data, list):
                text_bboxes = text_data
            elif isinstance(text_data, dict) and "lines" in text_data:
                text_bboxes = text_data["lines"]
        elif "lines" in api_response:
            text_bboxes = api_response["lines"]
        elif "results" in api_response:
            results = api_response["results"]
            if isinstance(results, list):
                text_bboxes = results
        
        # Ensure each bbox has required fields
        normalized_bboxes = []
        for bbox in text_bboxes:
            if ("polygon" in bbox or "bbox" in bbox) and ("content" in bbox or "text" in bbox):
                normalized_bbox = {
                    "polygon": bbox.get("polygon", bbox.get("bbox", [])),
                    "content": bbox.get("content", bbox.get("text", ""))
                }
                normalized_bboxes.append(normalized_bbox)
        
        return normalized_bboxes
    
    def _extract_table_html(self, api_response: Dict[str, Any]) -> Optional[str]:
        """Extract table HTML from API response"""
        # Handle different response formats
        if "html" in api_response:
            return api_response["html"]
        elif "table" in api_response and isinstance(api_response["table"], dict):
            return api_response["table"].get("html")
        elif "structure" in api_response:
            structure = api_response["structure"]
            if isinstance(structure, str):
                return structure
            elif isinstance(structure, dict):
                return structure.get("html")
        
        return None
    
    def _cluster_bboxes_by_overlap(
        self,
        bbox_list: List[Dict[str, Any]]
    ) -> List[BBoxCluster]:
        """
        Cluster bboxes by spatial overlap
        Implements granularity preference: prefer finer-grained bboxes
        """
        if not bbox_list:
            return []
        
        clusters = []
        used_indices = set()
        
        # Sort by bbox area (smaller first) to prioritize finer-grained bboxes
        bbox_list_sorted = sorted(
            enumerate(bbox_list),
            key=lambda x: self._compute_polygon_area(x[1]["bbox"].get("polygon", []))
        )
        
        for idx, item in bbox_list_sorted:
            if idx in used_indices:
                continue
            
            bbox = item["bbox"]
            source = item["source"]
            polygon = bbox.get("polygon", [])
            
            # Find or create cluster
            matched_cluster = None
            for cluster in clusters:
                # Check if this bbox matches the cluster
                iou = calculate_iou(polygon, cluster.polygon)
                overlap_ratio = calculate_overlap_ratio(polygon, cluster.polygon)
                
                if iou >= IOU_THRESHOLD or overlap_ratio >= OVERLAP_AREA_RATIO_THRESHOLD:
                    matched_cluster = cluster
                    break
            
            if matched_cluster:
                matched_cluster.add_bbox(bbox, source)
            else:
                # Create new cluster
                cluster = BBoxCluster(bbox, source)
                clusters.append(cluster)
            
            used_indices.add(idx)
        
        return clusters
    
    def _cluster_text_bboxes(
        self,
        text_bbox_list: List[Dict[str, Any]]
    ) -> List[BBoxCluster]:
        """
        Cluster text bboxes by spatial overlap AND text similarity
        """
        if not text_bbox_list:
            return []
        
        clusters = []
        used_indices = set()
        
        # Sort by bbox area (smaller first) for granularity preference
        text_bbox_list_sorted = sorted(
            enumerate(text_bbox_list),
            key=lambda x: self._compute_polygon_area(x[1]["bbox"].get("polygon", []))
        )
        
        for idx, item in text_bbox_list_sorted:
            if idx in used_indices:
                continue
            
            bbox = item["bbox"]
            source = item["source"]
            polygon = bbox.get("polygon", [])
            content = bbox.get("content", "")
            
            # Find or create cluster
            matched_cluster = None
            for cluster in clusters:
                # Check spatial overlap
                iou = calculate_iou(polygon, cluster.polygon)
                overlap_ratio = calculate_overlap_ratio(polygon, cluster.polygon)
                
                spatial_match = (iou >= IOU_THRESHOLD or 
                               overlap_ratio >= OVERLAP_AREA_RATIO_THRESHOLD)
                
                # Check text similarity
                text_sim = 1.0 - calculate_ned(content, cluster.content, normalize=True)
                text_match = text_sim >= TEXT_SIMILARITY_THRESHOLD
                
                if spatial_match and text_match:
                    matched_cluster = cluster
                    break
            
            if matched_cluster:
                matched_cluster.add_bbox(bbox, source)
            else:
                # Create new cluster
                cluster = BBoxCluster(bbox, source)
                clusters.append(cluster)
            
            used_indices.add(idx)
        
        return clusters
    
    def _compute_polygon_area(self, polygon: List[List[float]]) -> float:
        """Compute area of a polygon"""
        if not polygon or len(polygon) < 3:
            return 0.0
        
        # Simple bounding box area
        x_coords = [p[0] for p in polygon]
        y_coords = [p[1] for p in polygon]
        
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        
        return width * height
