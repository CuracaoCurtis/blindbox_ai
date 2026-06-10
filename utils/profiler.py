"""
性能分析工具 - 函数耗时装饰器
"""
import time
from functools import wraps
from typing import Callable, Any
from .logger import get_logger

logger = get_logger(__name__)


def timeit(func: Callable) -> Callable:
    """
    装饰器：记录函数执行时间
    
    使用方式:
        @timeit
        def my_function():
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000  # 毫秒
        
        # 根据耗时选择日志级别
        if elapsed > 1000:
            logger.warning(f"{func.__name__} 耗时: {elapsed:.2f}ms (>1s)")
        elif elapsed > 100:
            logger.info(f"{func.__name__} 耗时: {elapsed:.2f}ms")
        else:
            logger.debug(f"{func.__name__} 耗时: {elapsed:.2f}ms")
        
        return result
    return wrapper


def log_time(func: Callable) -> Callable:
    """别名，同 timeit"""
    return timeit(func)


class Timer:
    """计时器上下文管理器"""
    
    def __init__(self, name: str = "操作"):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        elapsed = (time.time() - self.start_time) * 1000
        logger.info(f"{self.name} 耗时: {elapsed:.2f}ms")


if __name__ == "__main__":
    # 测试装饰器
    @timeit
    def test_function():
        time.sleep(0.1)
    
    test_function()
    
    # 测试上下文管理器
    with Timer("测试操作"):
        time.sleep(0.05)
