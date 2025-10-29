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
    
    def __repr__(self):
        return f"<{{self.tag}}>{{self.text}}</{{self.tag}}>"


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
    """Calculate Simplified Tree Edit Distance Score (S-TEDS)"""
    tree1_node = parse_html_tree(html1)
    tree2_node = parse_html_tree(html2)
    
    if tree1_node is None and tree2_node is None:
        return 0.0
    if tree1_node is None or tree2_node is None:
        return 1.0
    
    return 0.0