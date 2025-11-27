import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# API 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv(
    "QWEN_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
QWEN_ROUTER_MODEL = os.getenv("QWEN_ROUTER_MODEL", "qwen-plus")

# 路由配置
ROUTER_TEMPERATURE = 0.0
PENDING_TTL_TURNS = 3

# 文件路径
PROMPTS_DIR = PROJECT_ROOT / "prompts"
DATA_DIR = PROJECT_ROOT / "data"
ROUTER_PROMPT_FILE = PROMPTS_DIR / "router_prompt.txt"
TEST_DATASET_FILE = DATA_DIR / "test_dataset.json"

# 确保目录存在
PROMPTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)