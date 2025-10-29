"""
Main entry point for Document Labeling Pipeline
Runs the 6-step pipeline for document labeling
"""

import asyncio
import argparse
import sys
from pathlib import Path
from loguru import logger

from pipeline.workflow_manager import WorkflowManager
from config import INPUT_DIR, OUTPUT_DIR, LOG_FILE, LOG_FORMAT


def setup_logging(log_file: str = LOG_FILE, verbose: bool = False):
    """Setup logging configuration"""
    logger.remove()  # Remove default handler
    
    # Console handler
    log_level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        format=LOG_FORMAT,
        level=log_level,
        colorize=True
    )
    
    # File handler
    logger.add(
        log_file,
        format=LOG_FORMAT,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )


async def main_async(args):
    """Main async function"""
    # Setup logging
    setup_logging(args.log_file, args.verbose)
    
    logger.info("=" * 80)
    logger.info("Document Labeling Pipeline - Starting")
    logger.info("=" * 80)
    
    # Initialize workflow manager
    workflow_manager = WorkflowManager()
    
    # Process input
    input_path = Path(args.input_dir)
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {args.input_dir}")
        return 1
    
    # Create output directories
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_path}")
    
    try:
        if input_path.is_file():
            # Process single image
            logger.info(f"Processing single image: {input_path}")
            result = await workflow_manager.process_image(str(input_path))
            logger.success("Processing completed successfully")
        elif input_path.is_dir():
            # Process directory
            logger.info(f"Processing directory: {input_path}")
            results = await workflow_manager.process_directory(str(input_path))
            logger.success(f"Processed {len(results)} images successfully")
        else:
            logger.error(f"Invalid input path: {input_path}")
            return 1
    except Exception as e:
        logger.exception(f"Error during processing: {e}")
        return 1
    
    logger.info("=" * 80)
    logger.info("Document Labeling Pipeline - Completed")
    logger.info("=" * 80)
    
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Document Labeling Pipeline - Consistent Ground Truth Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single image
  python main.py --input-dir input_images/sample.jpg
  
  # Process a directory of images
  python main.py --input-dir input_images/ --output-dir output/
  
  # Enable verbose logging
  python main.py --input-dir input_images/ --verbose
        """
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        default=INPUT_DIR,
        help=f'Input directory or file path (default: {INPUT_DIR})'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=OUTPUT_DIR,
        help=f'Output directory path (default: {OUTPUT_DIR})'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default=LOG_FILE,
        help=f'Log file path (default: {LOG_FILE})'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    
    args = parser.parse_args()
    
    # Run async main
    exit_code = asyncio.run(main_async(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
