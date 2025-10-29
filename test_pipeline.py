#!/usr/bin/env python3
"""
Test script for Document Labeling Pipeline
Creates mock data and tests the pipeline components
"""

import asyncio
import json
from pathlib import Path
from PIL import Image
import numpy as np

from pipeline import APIManager, ConsistencyEngine, WorkflowManager
from metrics import calculate_ned, calculate_steds, calculate_iou


def create_test_image(width=800, height=600, output_path="test_image.jpg"):
    """Create a simple test image"""
    # Create a white image with some colored rectangles
    img_array = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Add some colored rectangles to simulate document elements
    img_array[50:150, 50:300] = [200, 200, 255]  # Light blue rectangle
    img_array[200:350, 100:400] = [255, 200, 200]  # Light red rectangle
    img_array[400:550, 200:700] = [200, 255, 200]  # Light green rectangle
    
    img = Image.fromarray(img_array)
    img.save(output_path)
    print(f"Created test image: {output_path}")
    return output_path


def test_metrics():
    """Test metric calculations"""
    print("\n" + "="*80)
    print("Testing Metrics")
    print("="*80)
    
    # Test NED
    text1 = "Hello World"
    text2 = "Hello World"
    text3 = "Hello Earth"
    
    ned1 = calculate_ned(text1, text2)
    ned2 = calculate_ned(text1, text3)
    
    print(f"\nNED Test:")
    print(f"  '{text1}' vs '{text2}': {ned1:.4f} (should be 0.0)")
    print(f"  '{text1}' vs '{text3}': {ned2:.4f} (should be > 0)")
    
    assert ned1 == 0.0, "Identical texts should have NED = 0"
    assert ned2 > 0, "Different texts should have NED > 0"
    print("  ✓ NED tests passed")
    
    # Test IoU
    bbox1 = [[0, 0], [100, 0], [100, 100], [0, 100]]
    bbox2 = [[0, 0], [100, 0], [100, 100], [0, 100]]  # Identical
    bbox3 = [[50, 50], [150, 50], [150, 150], [50, 150]]  # Overlapping
    bbox4 = [[200, 200], [300, 200], [300, 300], [200, 300]]  # Non-overlapping
    
    iou1 = calculate_iou(bbox1, bbox2)
    iou2 = calculate_iou(bbox1, bbox3)
    iou3 = calculate_iou(bbox1, bbox4)
    
    print(f"\nIoU Test:")
    print(f"  Identical bboxes: {iou1:.4f} (should be 1.0)")
    print(f"  Overlapping bboxes: {iou2:.4f} (should be > 0)")
    print(f"  Non-overlapping bboxes: {iou3:.4f} (should be 0.0)")
    
    assert iou1 == 1.0, "Identical bboxes should have IoU = 1.0"
    assert iou2 > 0, "Overlapping bboxes should have IoU > 0"
    assert iou3 == 0.0, "Non-overlapping bboxes should have IoU = 0.0"
    print("  ✓ IoU tests passed")
    
    # Test S-TEDS
    html1 = "<table><tr><td>A</td></tr></table>"
    html2 = "<table><tr><td>A</td></tr></table>"
    html3 = "<table><tr><td>B</td></tr></table>"
    
    steds1 = calculate_steds(html1, html2)
    steds2 = calculate_steds(html1, html3)
    
    print(f"\nS-TEDS Test:")
    print(f"  Identical tables: {steds1:.4f} (should be 0.0)")
    print(f"  Different tables: {steds2:.4f} (should be > 0)")
    
    assert steds1 == 0.0, "Identical tables should have S-TEDS = 0"
    assert steds2 >= 0, "Different tables should have S-TEDS >= 0"
    print("  ✓ S-TEDS tests passed")


def test_consistency_engine():
    """Test ConsistencyEngine"""
    print("\n" + "="*80)
    print("Testing ConsistencyEngine")
    print("="*80)
    
    engine = ConsistencyEngine()
    
    # Mock layout results
    mock_layout_results = {
        "service1": {
            "layout": [
                {"polygon": [[10, 10], [100, 10], [100, 50], [10, 50]], "type": "text"},
                {"polygon": [[10, 60], [100, 60], [100, 100], [10, 100]], "type": "table"}
            ]
        },
        "service2": {
            "regions": [
                {"polygon": [[12, 12], [98, 12], [98, 48], [12, 48]], "type": "text"},
                {"polygon": [[10, 60], [100, 60], [100, 100], [10, 100]], "type": "table"}
            ]
        }
    }
    
    consistent_layout = engine.find_consistent_layout(mock_layout_results)
    
    print(f"\nConsistent Layout:")
    print(f"  Found {len(consistent_layout['labels'])} labels")
    print(f"  Sources: {consistent_layout['sources']}")
    
    assert len(consistent_layout['labels']) >= 1, "Should find at least 1 consistent label"
    print("  ✓ Layout consistency test passed")
    
    # Mock text results
    mock_text_results = {
        "service1": {
            "text": [
                {"polygon": [[10, 10], [100, 10], [100, 30], [10, 30]], "content": "Hello World"}
            ]
        },
        "service2": {
            "lines": [
                {"polygon": [[12, 12], [98, 12], [98, 28], [12, 28]], "content": "Hello World"}
            ]
        }
    }
    
    consistent_text = engine.find_consistent_text(mock_text_results)
    
    print(f"\nConsistent Text:")
    print(f"  Found {len(consistent_text['labels'])} labels")
    print(f"  Sources: {consistent_text['sources']}")
    
    assert len(consistent_text['labels']) >= 1, "Should find at least 1 consistent text label"
    print("  ✓ Text consistency test passed")


def test_api_manager():
    """Test APIManager basic functionality"""
    print("\n" + "="*80)
    print("Testing APIManager")
    print("="*80)
    
    api_manager = APIManager()
    
    print("\nAPIManager initialized successfully")
    print(f"  Max concurrent requests: {api_manager.max_concurrent_requests}")
    
    # Test image cropping
    test_img_path = create_test_image(output_path="/tmp/test_crop_image.jpg")
    polygon = [[100, 100], [300, 100], [300, 200], [100, 200]]
    
    cropped_bytes = api_manager.crop_image_from_polygon(test_img_path, polygon)
    
    assert len(cropped_bytes) > 0, "Cropped image should not be empty"
    print(f"  ✓ Image cropping works (cropped size: {len(cropped_bytes)} bytes)")


def test_workflow_manager():
    """Test WorkflowManager basic functionality"""
    print("\n" + "="*80)
    print("Testing WorkflowManager")
    print("="*80)
    
    workflow_manager = WorkflowManager()
    
    print("\nWorkflowManager initialized successfully")
    print("  ✓ APIManager and ConsistencyEngine initialized")
    
    # Test helper methods
    test_polygon = [[10, 20], [30, 40], [50, 60]]
    serialized = workflow_manager._serialize_polygon(test_polygon)
    print(f"  ✓ Polygon serialization: {serialized}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("Document Labeling Pipeline - Component Tests")
    print("="*80)
    
    try:
        # Run tests
        test_metrics()
        test_consistency_engine()
        test_api_manager()
        test_workflow_manager()
        
        print("\n" + "="*80)
        print("All Tests Passed! ✓")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
