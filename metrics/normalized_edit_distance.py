"""
Normalized Edit Distance (NED) calculations for text matching
"""

import re
import unicodedata
from typing import List, Tuple
import textdistance


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison
    - Convert to lowercase
    - Remove extra whitespaces
    - Normalize unicode characters
    - Remove special characters (optional)
    
    Args:
        text: Input text string
        
    Returns:
        Normalized text string
    """
    if not text:
        return ""
    
    # Normalize unicode characters (NFD -> NFC)
    text = unicodedata.normalize('NFC', text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def calculate_levenshtein_distance(text1: str, text2: str) -> int:
    """
    Calculate Levenshtein distance between two strings
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        Levenshtein distance (number of edits)
    """
    return textdistance.levenshtein(text1, text2)


def calculate_ned(text1: str, text2: str, normalize: bool = True) -> float:
    """
    Calculate Normalized Edit Distance (NED) between two text strings
    NED = Levenshtein Distance / max(len(text1), len(text2))
    
    Args:
        text1: First text string
        text2: Second text string
        normalize: Whether to normalize text before comparison
        
    Returns:
        NED value between 0 (identical) and 1 (completely different)
    """
    # Normalize texts if requested
    if normalize:
        text1 = normalize_text(text1)
        text2 = normalize_text(text2)
    
    # Handle empty strings
    if not text1 and not text2:
        return 0.0
    if not text1 or not text2:
        return 1.0
    
    # Calculate Levenshtein distance
    distance = calculate_levenshtein_distance(text1, text2)
    
    # Normalize by maximum length
    max_length = max(len(text1), len(text2))
    
    if max_length == 0:
        return 0.0
    
    ned = distance / max_length
    
    return ned


def calculate_similarity(text1: str, text2: str, normalize: bool = True) -> float:
    """
    Calculate text similarity (1 - NED)
    
    Args:
        text1: First text string
        text2: Second text string
        normalize: Whether to normalize text before comparison
        
    Returns:
        Similarity value between 0 (completely different) and 1 (identical)
    """
    ned = calculate_ned(text1, text2, normalize)
    return 1.0 - ned


def are_texts_identical(text1: str, text2: str, normalize: bool = True) -> bool:
    """
    Check if two texts are identical (NED = 0)
    
    Args:
        text1: First text string
        text2: Second text string
        normalize: Whether to normalize text before comparison
        
    Returns:
        True if texts are identical
    """
    ned = calculate_ned(text1, text2, normalize)
    return ned == 0.0


def join_texts_by_reading_order(texts: List[str], separator: str = " ") -> str:
    """
    Join multiple text strings by reading order
    Useful for comparing paragraph vs lines
    
    Args:
        texts: List of text strings
        separator: Separator between texts (default: space)
        
    Returns:
        Joined text string
    """
    # Filter out empty texts
    texts = [t for t in texts if t and t.strip()]
    
    # Join with separator
    return separator.join(texts)


def compare_hierarchical_texts(paragraph_text: str, 
                               line_texts: List[str], 
                               normalize: bool = True) -> Tuple[float, str]:
    """
    Compare a paragraph text with multiple line texts
    Used for cross-granularity validation
    
    Args:
        paragraph_text: Text from paragraph-level detection
        line_texts: List of texts from line-level detections
        normalize: Whether to normalize text before comparison
        
    Returns:
        Tuple of (NED value, joined line text)
    """
    # Join line texts by reading order
    joined_text = join_texts_by_reading_order(line_texts)
    
    # Calculate NED
    ned = calculate_ned(paragraph_text, joined_text, normalize)
    
    return ned, joined_text