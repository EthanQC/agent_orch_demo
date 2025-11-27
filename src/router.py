import json
from typing import Dict, Any, List
from openai.types.chat import ChatCompletionMessageParam

import config
from src.llm_client import QwenClient
from src.models import RouterOutput, Intent, Confidence, SessionState


def load_router_prompt() -> str:
    """从文件加载路由器提示词"""
    try:
        with open(config.ROUTER_PROMPT_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise RuntimeError(
            f"路由器提示词文件不存在: {config.ROUTER_PROMPT_FILE}\n"
            "请确保 prompts/router_prompt.txt 文件存在"
        )


def build_state_summary(state: SessionState) -> str:
    """将当前状态序列化为 JSON 字符串"""
    ps_desc = None
    if state.pending_switch is not None:
        ps_desc = {
            "target_scene": state.pending_switch.target_scene.value,
            "age_turns": state.pending_switch.age_turns,
        }
    return json.dumps(
        {
            "active_scene": state.active_scene.value,
            "pending_switch": ps_desc,
        },
        ensure_ascii=False,
    )


def parse_router_response(content: str) -> RouterOutput:
    """解析 LLM 返回的 JSON 响应"""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # JSON 解析失败,返回兜底结果
        return RouterOutput(
            intent=Intent.CHAT,
            confidence=Confidence.LOW,
            score=0,
            slots={},
            reason=f"解析 JSON 失败,原始输出: {content[:100]}",
        )
    
    # 解析 intent
    intent_str = str(data.get("intent", "chat"))
    valid_intents = {"chat", "recite", "homework", "continue_current", "exit_current"}
    if intent_str not in valid_intents:
        intent_str = "chat"
    intent = Intent(intent_str)
    
    # 解析 score
    try:
        score = int(data.get("score", 0))
    except (ValueError, TypeError):
        score = 0
    score = max(0, min(100, score))
    
    # 根据 score 计算 confidence (不信任模型自己给的)
    if score >= 80:
        confidence = Confidence.HIGH
    elif score >= 55:
        confidence = Confidence.MID
    else:
        confidence = Confidence.LOW
    
    # 提取 slots 和 reason
    slots = data.get("slots", {}) or {}
    reason = str(data.get("reason", ""))
    
    return RouterOutput(
        intent=intent,
        confidence=confidence,
        score=score,
        slots=slots,
        reason=reason,
    )


def call_llm_router(user_text: str, state: SessionState) -> RouterOutput:
    """
    调用 Qwen API 进行路由决策
    
    Args:
        user_text: 用户输入文本
        state: 当前会话状态
        
    Returns:
        RouterOutput: 路由决策结果
    """
    client = QwenClient.get_client()
    system_prompt = load_router_prompt()
    state_summary = build_state_summary(state)
    
    # 使用正确的类型注解
    messages: List[ChatCompletionMessageParam] = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"当前会话状态: {state_summary}\n用户本轮输入: {user_text}",
        },
    ]
    
    try:
        completion = client.chat.completions.create(
            model=config.QWEN_ROUTER_MODEL,
            messages=messages,
            temperature=config.ROUTER_TEMPERATURE,
        )
        
        # 处理可能为 None 的 content
        content = completion.choices[0].message.content
        if content is None:
            # API 返回空内容,使用兜底逻辑
            return RouterOutput(
                intent=Intent.CHAT,
                confidence=Confidence.LOW,
                score=0,
                slots={},
                reason="API 返回内容为空",
            )
        
        return parse_router_response(content)
    
    except Exception as e:
        # 捕获所有 API 调用异常
        return RouterOutput(
            intent=Intent.CHAT,
            confidence=Confidence.LOW,
            score=0,
            slots={},
            reason=f"API 调用失败: {str(e)}",
        )


def router_output_to_dict(out: RouterOutput) -> Dict[str, Any]:
    """将 RouterOutput 转换为字典格式"""
    return {
        "intent": out.intent.value,
        "confidence": out.confidence.value,
        "score": out.score,
        "slots": out.slots,
        "reason": out.reason,
    }