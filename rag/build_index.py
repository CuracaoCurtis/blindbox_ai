"""
构建商品向量索引
"""
import faiss
import numpy as np
import pickle
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm

from config.settings import settings
from database.connector import get_product_data
from database.models import Product
from rag.embeddings import embedding_model
from utils.logger import get_logger

logger = get_logger(__name__)


def build_product_text(product: Dict[str, Any]) -> str:
    """
    构建商品描述文本
    
    Args:
        product: 商品信息字典
        
    Returns:
        商品描述文本
    """
    # 提取关键信息
    name = product.get('name', '')
    ip = product.get('ip', '')
    style = product.get('style', '')
    description = product.get('description', '')
    category = product.get('category', '')
    
    # 构建文本描述
    parts = []
    if name:
        parts.append(f"商品名称：{name}")
    if ip:
        parts.append(f"IP系列：{ip}")
    if style:
        parts.append(f"设计风格：{style}")
    if category:
        parts.append(f"商品分类：{category}")
    if description:
        parts.append(f"商品描述：{description}")
    
    # 组合成连贯的文本
    product_text = "，".join(parts)
    return product_text.strip()


def create_faiss_index(dimension: int) -> faiss.Index:
    """
    创建FAISS索引
    
    Args:
        dimension: 向量维度
        
    Returns:
        FAISS索引
    """
    if settings.FAISS_INDEX_TYPE == "IndexFlatIP":
        # 内积索引（用于余弦相似度，向量需归一化）
        index = faiss.IndexFlatIP(dimension)
    elif settings.FAISS_INDEX_TYPE == "IndexFlatL2":
        # L2距离索引
        index = faiss.IndexFlatL2(dimension)
    else:
        raise ValueError(f"不支持的索引类型: {settings.FAISS_INDEX_TYPE}")
    
    return index


def build_product_index(
    index_path: Optional[str] = None,
    metadata_path: Optional[str] = None,
    batch_size: int = 1000
) -> Dict[str, Any]:
    """
    构建商品向量索引
    
    Args:
        index_path: 索引保存路径
        metadata_path: 元数据保存路径
        batch_size: 批处理大小
        
    Returns:
        构建统计信息
    """
    start_time = time.time()
    
    # 使用默认路径
    if index_path is None:
        index_path = settings.FAISS_INDEX_PATH
    if metadata_path is None:
        metadata_path = settings.FAISS_METADATA_PATH
    
    # 确保目录存在
    Path(index_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 加载商品数据
    all_products = []
    all_texts = []
    
    logger.info("开始加载商品数据...")
    for batch_products in get_product_data(batch_size):
        for product in batch_products:
            all_products.append(product)
            product_text = build_product_text(product)
            all_texts.append(product_text)
    
    if not all_products:
        logger.warning("没有找到商品数据")
        return {"status": "error", "message": "没有商品数据"}
    
    logger.info(f"共加载 {len(all_products)} 件商品")
    
    # 编码为向量
    logger.info("开始编码商品文本为向量...")
    embeddings = embedding_model.encode_batch(
        all_texts, 
        batch_size=128,
        normalize=True
    )
    
    dimension = embeddings.shape[1]
    logger.info(f"向量编码完成，维度: {dimension}")
    
    # 创建并填充索引
    logger.info("正在构建FAISS索引...")
    index = create_faiss_index(dimension)
    index.add(embeddings)
    
    # 保存索引
    logger.info(f"保存索引到: {index_path}")
    faiss.write_index(index, index_path)
    
    # 保存元数据
    logger.info(f"保存元数据到: {metadata_path}")
    with open(metadata_path, 'wb') as f:
        pickle.dump(all_products, f)
    
    # 统计信息
    elapsed_time = time.time() - start_time
    stats = {
        "status": "success",
        "total_products": len(all_products),
        "embedding_dimension": dimension,
        "index_type": settings.FAISS_INDEX_TYPE,
        "build_time_seconds": round(elapsed_time, 2),
        "products_per_second": round(len(all_products) / elapsed_time, 2),
        "index_size_mb": Path(index_path).stat().st_size / (1024 * 1024),
        "metadata_size_mb": Path(metadata_path).stat().st_size / (1024 * 1024)
    }
    
    logger.info(f"索引构建完成！统计信息: {stats}")
    return stats


if __name__ == "__main__":
    """命令行入口点"""
    import argparse
    
    parser = argparse.ArgumentParser(description="构建商品向量索引")
    parser.add_argument("--batch-size", type=int, default=1000, help="批处理大小")
    parser.add_argument("--index-path", type=str, help="索引保存路径")
    parser.add_argument("--metadata-path", type=str, help="元数据保存路径")
    
    args = parser.parse_args()
    
    stats = build_product_index(
        index_path=args.index_path,
        metadata_path=args.metadata_path,
        batch_size=args.batch_size
    )
    
    print("索引构建统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
