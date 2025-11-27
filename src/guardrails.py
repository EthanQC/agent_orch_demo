from typing import Dict, Any

import config
from src.models import (
    Intent,
    Confidence,
    Scene,
    SessionState,
    GuardrailsDecision,
    PendingSwitch,
)


def _base_decision_without_pending(
    intent: Intent,
    confidence: Confidence,
    slots: Dict[str, Any],
    state: SessionState,
) -> GuardrailsDecision:
    """
    不考虑 pending_switch 时的基础决策逻辑
    
    Args:
        intent: 路由器识别的意图
        confidence: 置信度
        slots: 提取的槽位信息
        state: 当前会话状态
        
    Returns:
        GuardrailsDecision: 决策结果
    """
    active = state.active_scene
    
    # 继续当前场景
    if intent == Intent.CONTINUE:
        return GuardrailsDecision(
            scene=active,
            action="continue",
            target_scene=active,
            slots={},
        )
    
    # 明确的业务场景意图
    if intent in (Intent.CHAT, Intent.RECITE, Intent.HOMEWORK):
        target_scene = Scene(intent.value)
        
        # 高置信度: 直接切换
        if confidence == Confidence.HIGH:
            if target_scene == active:
                return GuardrailsDecision(
                    scene=active,
                    action="continue",
                    target_scene=active,
                    slots=slots,
                )
            else:
                return GuardrailsDecision(
                    scene=target_scene,
                    action="switch",
                    target_scene=target_scene,
                    slots=slots,
                )
        
        # 中置信度: 如果目标不同于当前,先挂 pending_switch
        if confidence == Confidence.MID and target_scene != active:
            state.pending_switch = PendingSwitch(
                target_scene=target_scene,
                slots=slots,
                age_turns=0,
            )
            # 本轮仍按当前场景处理
            return GuardrailsDecision(
                scene=active,
                action="continue",
                target_scene=active,
                slots={},
            )
        
        # 低置信度: 保守,继续当前
        return GuardrailsDecision(
            scene=active,
            action="continue",
            target_scene=active,
            slots={},
        )
    
    # 其他情况: 保持当前场景
    return GuardrailsDecision(
        scene=active,
        action="continue",
        target_scene=active,
        slots={},
    )


def apply_guardrails(
    route: Dict[str, Any],
    state: SessionState
) -> GuardrailsDecision:
    """
    应用 Guardrails 规则,返回最终决策
    
    Args:
        route: 路由器输出 (字典格式)
        state: 当前会话状态 (会被修改)
        
    Returns:
        GuardrailsDecision: 最终决策结果
    """
    intent = Intent(route["intent"])
    confidence = Confidence(route["confidence"])
    slots: Dict[str, Any] = route.get("slots", {}) or {}
    active = state.active_scene
    
    # 0. 维护 pending_switch TTL
    if state.pending_switch is not None:
        state.pending_switch.age_turns += 1
        if state.pending_switch.age_turns > config.PENDING_TTL_TURNS:
            # 超时,清空
            state.pending_switch = None
    
    # 1. exit_current: 无条件退出当前任务回 chat
    if intent == Intent.EXIT:
        state.pending_switch = None
        return GuardrailsDecision(
            scene=Scene.CHAT,
            action="exit",
            target_scene=Scene.CHAT,
            slots={},
        )
    
    # 2. 如果存在 pending_switch,优先处理确认/否认逻辑
    if state.pending_switch is not None:
        ps = state.pending_switch
        target_intent = Intent(ps.target_scene.value)
        
        # 2.1 用户明确转向 target_scene,且置信度至少 MID → 确认切换
        if intent == target_intent and confidence in (Confidence.MID, Confidence.HIGH):
            merged_slots = {**ps.slots, **slots}
            state.pending_switch = None
            return GuardrailsDecision(
                scene=ps.target_scene,
                action="switch",
                target_scene=ps.target_scene,
                slots=merged_slots,
            )
        
        # 2.2 用户明确高置信度地跑向另一个场景 → 放弃原 pending
        if (
            intent not in (Intent.CONTINUE,)
            and intent != target_intent
            and confidence == Confidence.HIGH
        ):
            state.pending_switch = None
            return _base_decision_without_pending(
                intent=intent,
                confidence=confidence,
                slots=slots,
                state=state,
            )
        
        # 2.3 否则: 继续维持当前场景
        return GuardrailsDecision(
            scene=active,
            action="continue",
            target_scene=active,
            slots={},
        )
    
    # 3. 没有 pending_switch: 使用基础逻辑
    return _base_decision_without_pending(
        intent=intent,
        confidence=confidence,
        slots=slots,
        state=state,
    )