"""
RAG检索核心模块
"""
import faiss
import numpy as np
import pickle
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from functools import lru_cache

from config.settings import settings
from database.models import UserProfile, SearchResult, Product
from rag.embeddings import embedding_model
from utils.logger import get_logger
from utils.profiler import timeit

logger = get_logger(__name__)


class VectorSearcher:
    """向量检索器"""
    
    def __init__(
        self,
        index_path: Optional[str] = None,
        metadata_path: Optional[str] = None
    ):
        """
        初始化检索器
        
        Args:
            index_path: FAISS索引路径
            metadata_path: 元数据路径
        """
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.metadata_path = metadata_path or settings.FAISS_METADATA_PATH
        
        if not Path(self.index_path).exists():
            raise FileNotFoundError(f"索引文件不存在: {self.index_path}")
        if not Path(self.metadata_path).exists():
            raise FileNotFoundError(f"元数据文件不存在: {self.metadata_path}")
        
        self._load_index_and_metadata()
        logger.info(f"检索器初始化完成，共 {len(self.product_metadata)} 件商品")
    
    def _load_index_and_metadata(self):
        """加载索引和元数据"""
        start_time = time.time()
        
        # 加载FAISS索引
        logger.info(f"正在加载FAISS索引: {self.index_path}")
        self.index = faiss.read_index(self.index_path)
        
        # 加载元数据
        logger.info(f"正在加载元数据: {self.metadata_path}")
        with open(self.metadata_path, 'rb') as f:
            self.product_metadata = pickle.load(f)
        
        load_time = (time.time() - start_time) * 1000
        logger.info(f"索引加载完成，耗时: {load_time:.2f}ms")
    
    def _profile_to_query(self, profile: Dict[str, Any]) -> str:
        """
        将用户画像转换为查询文本
        
        Args:
            profile: 用户画像字典
            
        Returns:
            查询文本
        """
        # 转换为Pydantic模型以便使用验证功能
        user_profile = UserProfile(**profile)
        return user_profile.to_query_text()
    
    def _filter_by_budget(
        self, 
        candidates: List[Dict[str, Any]], 
        budget_max: Optional[float],
        budget_min: Optional[float]
    ) -> List[Dict[str, Any]]:
        """按预算过滤商品"""
        filtered = []
        
        for candidate in candidates:
            price = candidate.get('price', 0)
            
            # 预算上限检查
            if budget_max is not None and price > budget_max:
                continue
            # 预算下限检查
            if budget_min is not None and price < budget_min:
                continue
            
            filtered.append(candidate)
        
        return filtered
    
    def _calculate_relevance_score(
        self, 
        similarity: float, 
        product: Dict[str, Any]
    ) -> float:
        """
        计算综合相关性分数
        
        Args:
            similarity: 向量相似度
            product: 商品信息
            
        Returns:
            综合相关性分数
        """
        # 基础相似度分数
        score = similarity
        
        # 可以考虑加入其他因素，如：
        # 1. 价格因素（如果预算范围内较低的价格）
        # 2. 流行度因素
        # 3. 新品因素等
        
        return score
    
    @timeit
    def search(
        self,
        profile: Dict[str, Any],
        k: int = 5,
        filter_budget: bool = True,
        return_raw: bool = False
    ) -> List[SearchResult]:
        """
        根据用户画像检索商品
        
        Args:
            profile: 用户画像字典
            k: 返回商品数量
            filter_budget: 是否按预算过滤
            return_raw: 是否返回原始数据
            
        Returns:
            检索结果列表
        """
        # 1. 将画像转换为查询文本
        query_text = self._profile_to_query(profile)
        logger.debug(f"检索查询: {query_text}")
        
        # 2. 编码查询文本
        query_vector = embedding_model.encode(query_text, normalize=True)
        
        # 3. FAISS检索（搜索k*3个，为后续过滤留空间）
        search_k = min(k * 3, len(self.product_metadata))
        distances, indices = self.index.search(
            query_vector.reshape(1, -1), 
            k=search_k
        )
        
        # 4. 获取候选商品
        candidates = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx == -1:  # 无效索引
                continue
            
            product_data = self.product_metadata[idx].copy()
            product_data['similarity_score'] = float(distance)
            candidates.append(product_data)
        
        # 5. 预算过滤
        if filter_budget:
            budget_max = profile.get('budget_max')
            budget_min = profile.get('budget_min')
            candidates = self._filter_by_budget(candidates, budget_max, budget_min)
        
        # 6. 计算综合相关性分数
        for candidate in candidates:
            similarity = candidate['similarity_score']
            candidate['relevance_score'] = self._calculate_relevance_score(
                similarity, candidate
            )
        
        # 7. 按相关性排序
        candidates.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # 8. 截取前k个结果
        top_k = candidates[:k]
        
        if return_raw:
            return top_k
        
        # 转换为SearchResult对象
        results = []
        for item in top_k:
            # 转换为Product模型
            product_dict = {k: v for k, v in item.items() 
                          if k not in ['similarity_score', 'relevance_score']}
            product = Product(**product_dict)
            
            result = SearchResult(
                product=product,
                similarity_score=item['similarity_score'],
                relevance_score=item.get('relevance_score', 0)
            )
            results.append(result)
        
        logger.info(f"检索完成，返回 {len(results)} 个结果")
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取检索器统计信息"""
        return {
            "total_products": len(self.product_metadata),
            "embedding_dimension": self.index.d,
            "index_type": self.index.__class__.__name__,
            "index_path": str(self.index_path),
            "metadata_path": str(self.metadata_path)
        }


# 全局检索器实例
_searcher: Optional[VectorSearcher] = None


@lru_cache(maxsize=1)
def get_searcher() -> VectorSearcher:
    """
    获取全局检索器（单例模式）
    
    Returns:
        VectorSearcher实例
    """
    global _searcher
    if _searcher is None:
        _searcher = VectorSearcher()
    return _searcher


def search_by_tags(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    搜索接口函数（保持向后兼容）
    
    Args:
        profile: 用户画像字典
        
    Returns:
        商品字典列表
    """
    searcher = get_searcher()
    results = searcher.search(profile, return_raw=True)
    return results


def search_products(profile: Dict[str, Any], **kwargs) -> List[SearchResult]:
    """
    新版搜索接口
    
    Args:
        profile: 用户画像字典
        **kwargs: 其他搜索参数
        
    Returns:
        SearchResult列表
    """
    searcher = get_searcher()
    return searcher.search(profile, **kwargs)
