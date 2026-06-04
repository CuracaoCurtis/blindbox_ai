"""
向量编码模型封装
"""
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingModel:
    """向量编码模型单例"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """加载预训练模型"""
        try:
            logger.info(f"正在加载编码模型: {settings.EMBEDDING_MODEL}")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            # 测试模型
            test_embedding = self._model.encode(["测试文本"], normalize_embeddings=True)
            logger.info(f"模型加载成功，向量维度: {test_embedding.shape[1]}")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def encode(
        self, 
        texts: Union[str, List[str]], 
        normalize: bool = True,
        show_progress_bar: bool = False
    ) -> np.ndarray:
        """
        编码文本为向量
        
        Args:
            texts: 文本或文本列表
            normalize: 是否归一化向量
            show_progress_bar: 是否显示进度条
            
        Returns:
            向量数组
        """
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = self._model.encode(
            texts, 
            normalize_embeddings=normalize,
            show_progress_bar=show_progress_bar
        )
        return embeddings.astype('float32')
    
    def encode_batch(
        self, 
        texts: List[str], 
        batch_size: int = 32,
        normalize: bool = True
    ) -> np.ndarray:
        """批量编码文本"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.encode(batch, normalize=normalize, show_progress_bar=False)
            all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings)


# 全局模型实例
embedding_model = EmbeddingModel()
