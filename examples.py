#!/usr/bin/env python3
"""
Example usage script for Document Labeling Pipeline
Demonstrates various usage patterns
"""

import asyncio
import json
from pathlib import Path

from pipeline import WorkflowManager, APIManager, ConsistencyEngine
from metrics import calculate_ned, calculate_iou, calculate_steds


async def example_single_image():
    """Example: Process a single image"""
    print("\n" + "="*80)
    print("Example 1: Processing a Single Image")
    print("="*80)
    
    workflow_manager = WorkflowManager()
    
    # Process one image
    image_path = "input_images/sample_document.jpg"
    
    # Check if image exists
    if not Path(image_path).exists():
        print(f"Image not found: {image_path}")
        print("Please place a sample image in the input_images/ directory")
        return
    
    result = await workflow_manager.process_image(image_path)
    
    print(f"\nProcessing complete!")
    print(f"  Image: {result['image_id']}")
    print(f"  Layout labels found: {len(result['consistent_annotations']['layout_analysis'].get('labels', []))}")
    print(f"  Text labels found: {len(result['consistent_annotations']['text_extraction'].get('labels', []))}")
    print(f"  Table labels found: {len(result['consistent_annotations']['table_structure_recognition'].get('labels', []))}")


async def example_directory():
    """Example: Process all images in a directory"""
    print("\n" + "="*80)
    print("Example 2: Processing a Directory")
    print("="*80)
    
    workflow_manager = WorkflowManager()
    
    # Process directory
    input_dir = "input_images/"
    
    if not Path(input_dir).exists():
        print(f"Directory not found: {input_dir}")
        return
    
    results = await workflow_manager.process_directory(input_dir)
    
    print(f"\nProcessed {len(results)} images")
    
    for result in results:
        print(f"\n  {result['image_id']}:")
        print(f"    Layout: {len(result['consistent_annotations']['layout_analysis'].get('labels', []))} labels")
        print(f"    Text: {len(result['consistent_annotations']['text_extraction'].get('labels', []))} labels")
        print(f"    Tables: {len(result['consistent_annotations']['table_structure_recognition'].get('labels', []))} labels")


async def example_custom_api_calls():
    """Example: Make custom API calls"""
    print("\n" + "="*80)
    print("Example 3: Custom API Calls")
    print("="*80)
    
    api_manager = APIManager()
    
    image_path = "input_images/sample_document.jpg"
    
    if not Path(image_path).exists():
        print(f"Image not found: {image_path}")
        return
    
    # Call specific APIs
    print("\nCalling layout analysis APIs...")
    layout_results = await api_manager.call_layout_analysis(image_path)
    
    print(f"Received responses from {len(layout_results)} services:")
    for service_name, result in layout_results.items():
        if "error" in result:
            print(f"  {service_name}: ERROR - {result['error']}")
        else:
            print(f"  {service_name}: SUCCESS")
    
    # Call text extraction APIs
    print("\nCalling text extraction APIs...")
    text_results = await api_manager.call_text_extraction(image_path)
    
    print(f"Received responses from {len(text_results)} services:")
    for service_name, result in text_results.items():
        if "error" in result:
            print(f"  {service_name}: ERROR - {result['error']}")
        else:
            print(f"  {service_name}: SUCCESS")


def example_consistency_engine():
    """Example: Use ConsistencyEngine directly"""
    print("\n" + "="*80)
    print("Example 4: Using ConsistencyEngine Directly")
    print("="*80)
    
    engine = ConsistencyEngine()
    
    # Mock layout results from multiple services
    mock_layout = {
        "service_a": {
            "layout": [
                {"polygon": [[10, 10], [200, 10], [200, 50], [10, 50]], "type": "text"},
                {"polygon": [[10, 60], [200, 60], [200, 300], [10, 300]], "type": "table"}
            ]
        },
        "service_b": {
            "regions": [
                {"polygon": [[12, 12], [198, 12], [198, 48], [12, 48]], "type": "text"},
                {"polygon": [[10, 60], [200, 60], [200, 300], [10, 300]], "type": "table"}
            ]
        },
        "service_c": {
            "results": [
                {"polygon": [[11, 11], [199, 11], [199, 49], [11, 49]], "type": "text"}
            ]
        }
    }
    
    # Find consistent layout
    consistent_layout = engine.find_consistent_layout(mock_layout)
    
    print(f"\nConsistent layout results:")
    print(f"  Found {len(consistent_layout['labels'])} consistent labels")
    print(f"  Sources in agreement: {consistent_layout['sources']}")
    
    for i, label in enumerate(consistent_layout['labels'], 1):
        print(f"\n  Label {i}:")
        print(f"    Type: {label.get('type', 'unknown')}")
        print(f"    Sources: {label.get('sources', [])}")
        print(f"    Consensus count: {label.get('consensus_count', 0)}")


def example_metrics():
    """Example: Use metrics directly"""
    print("\n" + "="*80)
    print("Example 5: Using Metrics Directly")
    print("="*80)
    
    # Text similarity
    text1 = "Invoice Number: INV-2024-001"
    text2 = "Invoice Number: INV-2024-001"
    text3 = "Invoice Number: INV-2024-002"
    
    ned1 = calculate_ned(text1, text2)
    ned2 = calculate_ned(text1, text3)
    
    print(f"\nText Similarity (NED):")
    print(f"  '{text1}'")
    print(f"  vs")
    print(f"  '{text2}'")
    print(f"  NED: {ned1:.4f} (similarity: {(1-ned1)*100:.1f}%)")
    
    print(f"\n  '{text1}'")
    print(f"  vs")
    print(f"  '{text3}'")
    print(f"  NED: {ned2:.4f} (similarity: {(1-ned2)*100:.1f}%)")
    
    # BBox overlap
    bbox1 = [[0, 0], [100, 0], [100, 100], [0, 100]]
    bbox2 = [[50, 50], [150, 50], [150, 150], [50, 150]]
    
    iou = calculate_iou(bbox1, bbox2)
    
    print(f"\nBBox Overlap (IoU):")
    print(f"  BBox 1: {bbox1}")
    print(f"  BBox 2: {bbox2}")
    print(f"  IoU: {iou:.4f} ({iou*100:.1f}% overlap)")
    
    # Table structure
    table1 = (
        "<table>"
        "<tr><td>A</td><td>B</td></tr>"
        "<tr><td>C</td><td>D</td></tr>"
        "</table>"
    )
    table2 = (
        "<table>"
        "<tr><td>A</td><td>B</td></tr>"
        "<tr><td>C</td><td>D</td></tr>"
        "</table>"
    )
    table3 = "<table><tr><td>X</td><td>Y</td></tr></table>"
    
    steds1 = calculate_steds(table1, table2)
    steds2 = calculate_steds(table1, table3)
    
    print(f"\nTable Structure (S-TEDS):")
    print(f"  Identical tables: S-TEDS = {steds1:.4f}")
    print(f"  Different tables: S-TEDS = {steds2:.4f}")


def example_reading_results():
    """Example: Read and analyze pipeline results"""
    print("\n" + "="*80)
    print("Example 6: Reading Pipeline Results")
    print("="*80)
    
    # Read unified label
    unified_path = Path("output/unified_labels/sample_image.json")
    
    if unified_path.exists():
        with open(unified_path, 'r') as f:
            unified_data = json.load(f)
        
        print(f"\nUnified Label for: {unified_data['image_id']}")
        print(f"  Image path: {unified_data['image_path']}")
        
        # Show raw annotations
        print(f"\n  Raw annotations from {len(unified_data['raw_annotations'])} tasks")
        for task, services in unified_data['raw_annotations'].items():
            print(f"    {task}: {len(services)} services")
        
        # Show consistent annotations
        print(f"\n  Consistent annotations:")
        layout = unified_data['consistent_annotations']['layout_analysis']
        print(f"    Layout: {len(layout.get('labels', []))} labels from {layout.get('sources', [])}")
        
        text = unified_data['consistent_annotations']['text_extraction']
        print(f"    Text: {len(text.get('labels', []))} labels from {text.get('sources', [])}")
        
        tables = unified_data['consistent_annotations']['table_structure_recognition']
        print(f"    Tables: {len(tables.get('labels', []))} labels")
    else:
        print(f"No unified label found at: {unified_path}")
        print("Run the pipeline first to generate results")
    
    # Read task-specific label
    layout_path = Path("output/consistent_labels_per_task/layout_analysis/sample_image.json")
    
    if layout_path.exists():
        with open(layout_path, 'r') as f:
            layout_data = json.load(f)
        
        print(f"\n\nTask-Specific Label: Layout Analysis")
        print(f"  Sources: {layout_data['sources']}")
        print(f"  Labels: {len(layout_data['labels'])}")
        
        for i, label in enumerate(layout_data['labels'][:3], 1):  # Show first 3
            print(f"\n    Label {i}:")
            print(f"      Type: {label.get('type', 'unknown')}")
            print(f"      Polygon: {label.get('polygon', [])[:2]}... (showing first 2 points)")
    else:
        print(f"\nNo layout label found at: {layout_path}")


async def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("Document Labeling Pipeline - Usage Examples")
    print("="*80)
    
    # Note: Most examples require actual API services to be running
    # For demonstration purposes, we'll show the example functions
    
    print("\n[Note: These examples require API services to be running]")
    print("Available examples:")
    print("  1. Process a single image")
    print("  2. Process a directory")
    print("  3. Make custom API calls")
    print("  4. Use ConsistencyEngine directly")
    print("  5. Use metrics directly")
    print("  6. Read pipeline results")
    
    # Run examples that don't require API services
    example_consistency_engine()
    example_metrics()
    example_reading_results()
    
    print("\n" + "="*80)
    print("Examples completed!")
    print("="*80)
    print("\nTo run examples that call APIs, ensure your API services are running:")
    print("  - Uncomment the async examples in this script")
    print("  - Start your API services on the configured ports")
    print("  - Place sample images in input_images/")


if __name__ == "__main__":
    asyncio.run(main())
