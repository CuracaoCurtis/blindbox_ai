"""
日志工具模块 - 提供统一的日志记录功能
"""
import logging
import sys
from typing import Optional


def get_logger(
    name: str, 
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称（通常使用 __name__）
        level: 日志级别
        format_string: 日志格式（可选）
        
    Returns:
        logging.Logger 实例
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加handler
    if not logger.handlers:
        logger.setLevel(level)
        
        # 控制台输出
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # 日志格式
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        formatter = logging.Formatter(format_string, datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # 禁止向上传播（避免重复）
        logger.propagate = False
    
    return logger


def setup_file_logging(logger: logging.Logger, log_file: str, level: int = logging.INFO):
    """
    添加文件日志输出
    
    Args:
        logger: 日志记录器
        log_file: 日志文件路径
        level: 日志级别
    """
    from pathlib import Path
    
    # 确保日志目录存在
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


# 创建默认日志器
default_logger = get_logger("blindbox_ai")

if __name__ == "__main__":
    # 测试日志
    logger = get_logger(__name__)
    logger.info("日志模块测试")
    logger.warning("这是一条警告")
    logger.error("这是一条错误")
