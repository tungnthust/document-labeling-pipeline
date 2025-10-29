"""
API Manager for Document Labeling Pipeline
Handles async API calls to multiple services
"""

import asyncio
import aiohttp
import base64
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from loguru import logger
from PIL import Image
import io

from config import (
    API_SERVICES, API_TIMEOUT, API_MAX_RETRIES, API_RETRY_DELAY,
    MAX_CONCURRENT_REQUESTS, get_api_url, get_services_for_task
)


class APIManager:
    """Manages API calls to multiple document processing services"""
    
    def __init__(self, max_concurrent_requests: int = MAX_CONCURRENT_REQUESTS):
        self.max_concurrent_requests = max_concurrent_requests
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
    
    async def _make_request(
        self, 
        session: aiohttp.ClientSession,
        service_name: str,
        endpoint_key: str,
        image_path: str,
        polygon: Optional[List[List[float]]] = None,
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Make a single API request with retry logic
        
        Args:
            session: aiohttp ClientSession
            service_name: Name of the API service
            endpoint_key: Endpoint key (e.g., 'get_layout', 'get_text')
            image_path: Path to the image file
            polygon: Optional polygon coordinates for ROI
            image_bytes: Optional pre-cropped image bytes
            
        Returns:
            API response as dictionary
        """
        url = get_api_url(service_name, endpoint_key)
        
        # Prepare request body
        body = {
            "filepath": str(image_path)
        }
        
        if polygon is not None:
            body["polygon"] = polygon
        
        if image_bytes is not None:
            # Encode image bytes to base64
            body["image_bytes"] = base64.b64encode(image_bytes).decode('utf-8')
        
        # Retry logic
        for attempt in range(API_MAX_RETRIES):
            try:
                async with self.semaphore:
                    async with session.post(
                        url,
                        json=body,
                        timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.debug(f"Success: {service_name}/{endpoint_key} - {image_path}")
                            return result
                        else:
                            error_text = await response.text()
                            logger.warning(
                                f"Attempt {attempt + 1}/{API_MAX_RETRIES} failed: "
                                f"{service_name}/{endpoint_key} - Status {response.status}: {error_text}"
                            )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Attempt {attempt + 1}/{API_MAX_RETRIES} timeout: "
                    f"{service_name}/{endpoint_key}"
                )
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{API_MAX_RETRIES} error: "
                    f"{service_name}/{endpoint_key} - {str(e)}"
                )
            
            # Wait before retry (except for last attempt)
            if attempt < API_MAX_RETRIES - 1:
                await asyncio.sleep(API_RETRY_DELAY * (attempt + 1))
        
        # All attempts failed
        logger.error(f"All attempts failed: {service_name}/{endpoint_key}")
        return {"error": f"Failed after {API_MAX_RETRIES} attempts"}
    
    async def call_layout_analysis(
        self,
        image_path: str,
        polygon: Optional[List[List[float]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Call all layout analysis services
        
        Args:
            image_path: Path to the image file
            polygon: Optional polygon for ROI (default: full image)
            
        Returns:
            Dictionary mapping service_name -> API response
        """
        services = get_services_for_task("layout_analysis")
        results = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for service_name in services:
                service_config = API_SERVICES[service_name]
                # Determine the appropriate endpoint key
                if "get_layout" in service_config["endpoints"]:
                    endpoint_key = "get_layout"
                elif "extract" in service_config["endpoints"]:
                    endpoint_key = "extract"
                else:
                    continue
                
                task = self._make_request(
                    session, service_name, endpoint_key, image_path, polygon
                )
                tasks.append((service_name, task))
            
            # Execute all tasks concurrently
            for service_name, task in tasks:
                try:
                    result = await task
                    results[service_name] = result
                except Exception as e:
                    logger.error(f"Error calling {service_name}: {e}")
                    results[service_name] = {"error": str(e)}
        
        return results
    
    async def call_text_extraction(
        self,
        image_path: str,
        polygon: Optional[List[List[float]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Call all text extraction services
        
        Args:
            image_path: Path to the image file
            polygon: Optional polygon for ROI (default: full image)
            
        Returns:
            Dictionary mapping service_name -> API response
        """
        services = get_services_for_task("text_extraction")
        results = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for service_name in services:
                service_config = API_SERVICES[service_name]
                # Determine the appropriate endpoint key
                if "get_text" in service_config["endpoints"]:
                    endpoint_key = "get_text"
                elif "extract" in service_config["endpoints"]:
                    endpoint_key = "extract"
                else:
                    continue
                
                task = self._make_request(
                    session, service_name, endpoint_key, image_path, polygon
                )
                tasks.append((service_name, task))
            
            # Execute all tasks concurrently
            for service_name, task in tasks:
                try:
                    result = await task
                    results[service_name] = result
                except Exception as e:
                    logger.error(f"Error calling {service_name}: {e}")
                    results[service_name] = {"error": str(e)}
        
        return results
    
    async def call_table_structure_recognition(
        self,
        image_path: str,
        table_polygon: List[List[float]],
        cropped_image_bytes: Optional[bytes] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Call all table structure recognition services for a specific table ROI
        
        Args:
            image_path: Path to the original image file
            table_polygon: Polygon coordinates of the table
            cropped_image_bytes: Optional pre-cropped image bytes
            
        Returns:
            Dictionary mapping service_name -> API response
        """
        services = get_services_for_task("table_structure_recognition")
        results = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for service_name in services:
                service_config = API_SERVICES[service_name]
                # Determine the appropriate endpoint key
                if "get_table_structure" in service_config["endpoints"]:
                    endpoint_key = "get_table_structure"
                elif "extract" in service_config["endpoints"]:
                    endpoint_key = "extract"
                else:
                    continue
                
                task = self._make_request(
                    session, service_name, endpoint_key, 
                    image_path, table_polygon, cropped_image_bytes
                )
                tasks.append((service_name, task))
            
            # Execute all tasks concurrently
            for service_name, task in tasks:
                try:
                    result = await task
                    results[service_name] = result
                except Exception as e:
                    logger.error(f"Error calling {service_name}: {e}")
                    results[service_name] = {"error": str(e)}
        
        return results
    
    def crop_image_from_polygon(
        self, 
        image_path: str, 
        polygon: List[List[float]]
    ) -> bytes:
        """
        Crop image based on polygon coordinates
        
        Args:
            image_path: Path to the image file
            polygon: Polygon coordinates [[x1, y1], [x2, y2], ...]
            
        Returns:
            Cropped image as bytes
        """
        try:
            # Load image
            img = Image.open(image_path)
            
            # Get bounding box from polygon
            x_coords = [p[0] for p in polygon]
            y_coords = [p[1] for p in polygon]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            
            # Crop image
            cropped = img.crop((x_min, y_min, x_max, y_max))
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            cropped.save(img_byte_arr, format=img.format or 'PNG')
            img_byte_arr.seek(0)
            
            return img_byte_arr.read()
        except Exception as e:
            logger.error(f"Error cropping image: {e}")
            return b""
