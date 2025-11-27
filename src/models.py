from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional


class Scene(str, Enum):
    """业务场景枚举"""
    CHAT = "chat"
    RECITE = "recite"
    HOMEWORK = "homework"


class Intent(str, Enum):
    """用户意图枚举"""
    CHAT = "chat"
    RECITE = "recite"
    HOMEWORK = "homework"
    CONTINUE = "continue_current"
    EXIT = "exit_current"


class Confidence(str, Enum):
    """置信度枚举"""
    HIGH = "HIGH"
    MID = "MID"
    LOW = "LOW"


@dataclass
class RouterOutput:
    """路由器输出结果"""
    intent: Intent
    confidence: Confidence
    score: int
    slots: Dict[str, Any]
    reason: str = ""


@dataclass
class PendingSwitch:
    """等待用户确认的场景切换请求"""
    target_scene: Scene
    slots: Dict[str, Any] = field(default_factory=dict)
    age_turns: int = 0  # 已经等待了多少轮用户输入


@dataclass
class SessionState:
    """
    会话状态
    - active_scene: 当前所在业务场景
    - scene_state: 具体场景内部状态
    - pending_switch: 是否存在"待确认切场景"
    """
    active_scene: Scene = Scene.CHAT
    scene_state: Dict[str, Any] = field(default_factory=dict)
    pending_switch: Optional[PendingSwitch] = None

    def copy(self) -> "SessionState":
        """深拷贝会话状态"""
        return SessionState(
            active_scene=self.active_scene,
            scene_state=dict(self.scene_state),
            pending_switch=self.pending_switch,
        )


@dataclass
class GuardrailsDecision:
    """Guardrails 决策结果"""
    scene: Scene          # 本轮交给哪个场景 workflow 处理
    action: str           # "continue" | "switch" | "exit"
    target_scene: Scene   # 切换/退出后最终的 active_scene
    slots: Dict[str, Any]