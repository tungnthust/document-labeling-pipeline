"""
Tree Edit Distance (S-TEDS) calculations for table structure matching
Simplified Tree Edit Distance for comparing table structures in HTML format
"""

from typing import Dict, List, Any, Optional
from html.parser import HTMLParser
import apted
from apted import APTED, Config
from apted.helpers import Tree


class TableNode:
    """Represents a node in the table tree structure"""
    
    def __init__(self, tag: str, text: str = "", attributes: Dict[str, str] = None):
        self.tag = tag
        self.text = text.strip() if text else ""
        self.attributes = attributes or {}
        self.children = []
    
    def add_child(self, child):
        """Add a child node"""
        self.children.append(child)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation"""
        return {
            "tag": self.tag,
            "text": self.text,
            "attributes": self.attributes,
            "children": [child.to_dict() for child in self.children]
        }
    
    def to_apted_tree(self) -> Tree:
        """Convert TableNode to APTED Tree format"""
        # Create tree string representation
        if self.children:
            children_str = "".join([child.to_apted_tree().to_string() for child in self.children])
            tree_str = f"{{{self.tag}{children_str}}}"
        else:
            tree_str = f"{{{self.tag}}}"
        
        return Tree.from_text(tree_str)
    
    def __repr__(self):
        return f"<{self.tag}>{self.text}</{self.tag}>"


class TableHTMLParser(HTMLParser):
    """Parse HTML table structure into a tree"""
    
    def __init__(self):
        super().__init__()
        self.root = None
        self.current_node = None
        self.node_stack = []
    
    def handle_starttag(self, tag, attrs):
        """Handle opening tags"""
        attrs_dict = dict(attrs) if attrs else {}
        node = TableNode(tag=tag, attributes=attrs_dict)
        
        if self.root is None:
            self.root = node
            self.current_node = node
        else:
            self.current_node.add_child(node)
            self.node_stack.append(self.current_node)
            self.current_node = node
    
    def handle_endtag(self, tag):
        """Handle closing tags"""
        if self.node_stack:
            self.current_node = self.node_stack.pop()
    
    def handle_data(self, data):
        """Handle text data"""
        if self.current_node and data.strip():
            self.current_node.text += data.strip()


def parse_html_tree(html_string: str) -> Optional[TableNode]:
    """Parse HTML string into a tree structure"""
    if not html_string or not html_string.strip():
        return None
    
    parser = TableHTMLParser()
    try:
        parser.feed(html_string)
        return parser.root
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return None


def calculate_steds(html1: str, html2: str) -> float:
    """
    Calculate Simplified Tree Edit Distance Score (S-TEDS)
    Returns normalized edit distance: 0 = identical, 1 = completely different
    
    Args:
        html1: First HTML string
        html2: Second HTML string
        
    Returns:
        S-TEDS score between 0 (identical) and 1 (completely different)
    """
    # Parse HTML strings to tree structures
    tree1_node = parse_html_tree(html1)
    tree2_node = parse_html_tree(html2)
    
    # Handle edge cases
    if tree1_node is None and tree2_node is None:
        return 0.0
    if tree1_node is None or tree2_node is None:
        return 1.0
    
    try:
        # Convert to APTED tree format
        tree1 = tree1_node.to_apted_tree()
        tree2 = tree2_node.to_apted_tree()
        
        # Calculate tree edit distance
        apted_calculator = APTED(tree1, tree2)
        distance = apted_calculator.compute_edit_distance()
        
        # Normalize by the size of the larger tree
        size1 = count_nodes(tree1_node)
        size2 = count_nodes(tree2_node)
        max_size = max(size1, size2)
        
        if max_size == 0:
            return 0.0
        
        normalized_distance = distance / max_size
        
        # Clamp to [0, 1]
        return min(1.0, max(0.0, normalized_distance))
    
    except Exception as e:
        # If APTED fails, fall back to simple comparison
        # Compare normalized HTML strings
        html1_clean = normalize_html(html1)
        html2_clean = normalize_html(html2)
        
        if html1_clean == html2_clean:
            return 0.0
        else:
            return 1.0


def count_nodes(node: TableNode) -> int:
    """Count total nodes in tree"""
    count = 1  # Current node
    for child in node.children:
        count += count_nodes(child)
    return count


def normalize_html(html: str) -> str:
    """Normalize HTML for comparison"""
    if not html:
        return ""
    
    # Remove extra whitespace
    import re
    html = re.sub(r'\s+', ' ', html)
    html = html.strip()
    html = html.lower()
    
    return html


def are_tables_identical(html1: str, html2: str) -> bool:
    """
    Check if two HTML table structures are identical (S-TEDS = 0)
    
    Args:
        html1: First HTML string
        html2: Second HTML string
        
    Returns:
        True if tables are identical
    """
    steds = calculate_steds(html1, html2)
    return steds == 0.0