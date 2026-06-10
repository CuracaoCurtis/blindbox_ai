"""商品检索包。"""

from .recommender import ProductCatalog, extract_source_url, rule_reason

__all__ = ["ProductCatalog", "extract_source_url", "rule_reason"]
