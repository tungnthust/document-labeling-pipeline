"""
Overlap Area Ratio and IoU calculations for BBox matching
"""

from typing import List, Tuple
import numpy as np


def compute_bbox_area(polygon: List[List[float]]) -> float:
    """
    Calculate the area of a polygon (bbox)
    
    Args:
        polygon: List of [x, y] coordinates
        
    Returns:
        Area of the polygon
    """
    if len(polygon) < 3:
        return 0.0
    
    # Using Shoelace formula
    x = [point[0] for point in polygon]
    y = [point[1] for point in polygon]
    
    return 0.5 * abs(sum(x[i] * y[i + 1] - x[i + 1] * y[i] for i in range(-1, len(x) - 1)))


def polygon_to_bbox(polygon: List[List[float]]) -> Tuple[float, float, float, float]:
    """
    Convert polygon to bounding box (x_min, y_min, x_max, y_max)
    
    Args:
        polygon: List of [x, y] coordinates
        
    Returns:
        Tuple of (x_min, y_min, x_max, y_max)
    """
    x_coords = [point[0] for point in polygon]
    y_coords = [point[1] for point in polygon]
    
    return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))


def calculate_intersection_area(bbox1: Tuple[float, float, float, float], 
                                bbox2: Tuple[float, float, float, float]) -> float:
    """
    Calculate intersection area between two bounding boxes
    
    Args:
        bbox1: First bbox (x_min, y_min, x_max, y_max)
        bbox2: Second bbox (x_min, y_min, x_max, y_max)
        
    Returns:
        Intersection area
    """
    x_min = max(bbox1[0], bbox2[0])
    y_min = max(bbox1[1], bbox2[1])
    x_max = min(bbox1[2], bbox2[2])
    y_max = min(bbox1[3], bbox2[3])
    
    if x_max < x_min or y_max < y_min:
        return 0.0
    
    return (x_max - x_min) * (y_max - y_min)


def calculate_iou(polygon1: List[List[float]], 
                  polygon2: List[List[float]]) -> float:
    """
    Calculate Intersection over Union (IoU) between two polygons
    
    Args:
        polygon1: First polygon coordinates
        polygon2: Second polygon coordinates
        
    Returns:
        IoU value between 0 and 1
    """
    # Convert polygons to bounding boxes
    bbox1 = polygon_to_bbox(polygon1)
    bbox2 = polygon_to_bbox(polygon2)
    
    # Calculate areas
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    
    # Calculate intersection
    intersection = calculate_intersection_area(bbox1, bbox2)
    
    # Calculate union
    union = area1 + area2 - intersection
    
    if union == 0:
        return 0.0
    
    return intersection / union


def calculate_overlap_ratio(polygon1: List[List[float]], 
                           polygon2: List[List[float]]) -> float:
    """
    Calculate overlap ratio (intersection / min(area1, area2))
    This is useful for detecting when a smaller bbox is inside a larger one
    
    Args:
        polygon1: First polygon coordinates
        polygon2: Second polygon coordinates
        
    Returns:
        Overlap ratio between 0 and 1
    """
    # Convert polygons to bounding boxes
    bbox1 = polygon_to_bbox(polygon1)
    bbox2 = polygon_to_bbox(polygon2)
    
    # Calculate areas
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    
    # Calculate intersection
    intersection = calculate_intersection_area(bbox1, bbox2)
    
    # Calculate ratio with respect to smaller bbox
    min_area = min(area1, area2)
    
    if min_area == 0:
        return 0.0
    
    return intersection / min_area


def is_bbox_inside(inner_polygon: List[List[float]], 
                   outer_polygon: List[List[float]], 
                   threshold: float = 0.9) -> bool:
    """
    Check if one bbox is inside another
    
    Args:
        inner_polygon: Potentially inner bbox
        outer_polygon: Potentially outer bbox
        threshold: Overlap ratio threshold to consider as "inside"
        
    Returns:
        True if inner_polygon is inside outer_polygon
    """
    overlap = calculate_overlap_ratio(inner_polygon, outer_polygon)
    return overlap >= threshold
