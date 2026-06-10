"""项目配置文件。"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def _load_simple_env(path):
    """python-dotenv 不可用时读取本项目所需的简单 KEY=VALUE 配置。"""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


if load_dotenv is not None:
    load_dotenv(PROJECT_ROOT / ".env")
else:
    _load_simple_env(PROJECT_ROOT / ".env")


def _env_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_float(name, default):
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


class Settings:
    """全局配置类"""
    
    # ========== 数据路径 ==========
    PRODUCTS_CSV_PATH = DATA_DIR / "products.csv"
    PRODUCTS_RAW_CSV_PATH = DATA_DIR / "products_raw.csv"
    SUMMARY_TXT_PATH = DATA_DIR / "summary.txt"
    
    # ========== OpenAI-compatible 大模型配置 ==========
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").strip().rstrip("/")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
    LLM_MODEL = os.getenv("LLM_MODEL", "").strip()
    LLM_TIMEOUT = _env_int("LLM_TIMEOUT", 30)
    LLM_MAX_RETRIES = _env_int("LLM_MAX_RETRIES", 1)
    LLM_TEMPERATURE = _env_float("LLM_TEMPERATURE", 0.2)
    LLM_MAX_TOKENS = _env_int("LLM_MAX_TOKENS", 900)
    
    # ========== 检索默认值 ==========
    DEFAULT_SEARCH_K = 5
    DEFAULT_CANDIDATE_K = 20
    DEFAULT_MAX_PRICE = 9999
    DEFAULT_MIN_PRICE = 0
    
    # ========== 爬虫配置 ==========
    CRAWL_SLEEP_SECONDS = 0.2
    CRAWL_MAX_PAGES = 8
    CRAWL_TIMEOUT = 30
    CRAWL_RETRIES = 2
    
    # ========== 数据库配置（可选，角色2使用）==========
    DB_HOST = "localhost"
    DB_USER = "root"
    DB_PASSWORD = ""  # 修改为你的MySQL密码
    DB_NAME = "blindbox"
    DB_PORT = 3306
    
    @classmethod
    def ensure_dirs(cls):
        """确保必要目录存在"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def llm_configured(cls):
        """是否已提供完整的云端模型配置。"""
        return bool(cls.LLM_BASE_URL and cls.LLM_API_KEY and cls.LLM_MODEL)
    
    @classmethod
    def display(cls):
        """打印当前配置"""
        print("=" * 50)
        print("当前配置:")
        print(f"  数据目录: {DATA_DIR}")
        print(f"  商品数据: {cls.PRODUCTS_CSV_PATH}")
        print(f"  AI状态: {'已配置' if cls.llm_configured() else '未配置（规则模式）'}")
        print(f"  大模型: {cls.LLM_MODEL or '未设置'}")
        print("  检索方式: 硬条件过滤 + 可解释加权排序 + AI重排")
        print("=" * 50)


# 创建全局实例
settings = Settings()

# 确保目录存在
settings.ensure_dirs()

if __name__ == "__main__":
    settings.display()
