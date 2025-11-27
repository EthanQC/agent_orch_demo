# Agent Orchestration Demo

基于 LLM 的多场景对话路由系统演示项目。

## 功能特性

- 🤖 **智能路由**: 使用通义千问 Plus 进行意图识别
- 🛡️ **Guardrails**: 基于规则的决策校验和调整
- 🎯 **三场景支持**: 聊天(chat)、背诵(recite)、作业(homework)
- 📊 **离线评测**: 支持标注数据集的准确率评估
- 💬 **交互式体验**: 实时测试路由效果

## 项目结构

```
agent_orch_demo/
├── config.py              # 配置管理
├── demo.py                # 交互式演示
├── prompts/               # 提示词模板
│   └── router_prompt.txt
├── data/                  # 测试数据
│   └── test_dataset.json
├── src/                   # 核心源码
│   ├── models.py          # 数据模型
│   ├── llm_client.py      # LLM 客户端
│   ├── router.py          # 路由器
│   └── guardrails.py      # 决策校验
└── tests/                 # 测试模块
    └── test_evaluator.py  # 离线评测
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 或直接编辑 `.env`:

```bash
DASHSCOPE_API_KEY="your-api-key-here"
QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_ROUTER_MODEL="qwen-plus"
```

### 3. 运行离线评测

```bash
python -m tests.test_evaluator
```

### 4. 运行交互式演示

```bash
python demo.py
```

## 使用说明

### 离线评测

评测程序会加载 `data/test_dataset.json` 中的标注数据,依次调用路由器和 Guardrails,最后输出准确率和错误样例。

### 交互式演示

启动后可以直接输入对话,系统会实时显示:
- Router 的意图识别结果
- Guardrails 的决策调整
- 最终的场景切换结果

输入 `quit` 或 `exit` 退出。

## 配置说明

主要配置项在 `config.py` 中:

- `PENDING_TTL_TURNS`: pending_switch 的最大等待轮次 (默认 3)
- `ROUTER_TEMPERATURE`: 路由器的温度参数 (默认 0.0)
- `QWEN_ROUTER_MODEL`: 使用的模型名称 (默认 qwen-plus)

## License

MIT License - 详见 [LICENSE](LICENSE) 文件