"""
RAG检索模块
"""
from .searcher import VectorSearcher, search_by_tags, get_searcher
from .build_index import build_product_index

__version__ = "1.0.0"
__all__ = [
    "VectorSearcher",
    "search_by_tags", 
    "get_searcher",
    "build_product_index"
]
