from src.models import Scene, SessionState
from src.router import call_llm_router, router_output_to_dict
from src.guardrails import apply_guardrails


def interactive_loop():
    """交互式 REPL 循环"""
    print("=" * 60)
    print("交互式 Router + Guardrails Demo")
    print("=" * 60)
    print("输入 'quit' 或 'exit' 退出")
    print()
    
    state = SessionState(active_scene=Scene.CHAT)
    
    while True:
        # 显示当前状态
        print(f"\n[当前场景] {state.active_scene.value}")
        if state.pending_switch is not None:
            print(
                f"[待确认切换] target={state.pending_switch.target_scene.value}, "
                f"等待轮次={state.pending_switch.age_turns}"
            )
        
        # 获取用户输入
        user = input("\n你: ").strip()
        if user.lower() in ("quit", "exit"):
            print("\n再见!")
            break
        
        if not user:
            continue
        
        # 调用路由器
        router_out = call_llm_router(user, state)
        route_dict = router_output_to_dict(router_out)
        
        # 应用 Guardrails
        decision = apply_guardrails(route_dict, state)
        
        # 更新会话状态
        state.active_scene = decision.target_scene
        
        # 显示决策信息
        print("\n" + "-" * 60)
        print("[Router 输出]")
        print(f"  意图: {route_dict['intent']}")
        print(f"  评分: {route_dict['score']}")
        print(f"  置信度: {route_dict['confidence']}")
        print(f"  槽位: {route_dict['slots']}")
        print(f"  理由: {route_dict['reason']}")
        
        print("\n[Guardrails 决策]")
        print(f"  动作: {decision.action}")
        print(f"  目标场景: {decision.target_scene.value}")
        
        # 模拟场景响应
        print("\n[系统响应]")
        if decision.target_scene == Scene.RECITE:
            print("  📚 现在处于【背诵场景】,这里应该由 ReciteWorkflow 来处理下一步。")
        elif decision.target_scene == Scene.HOMEWORK:
            print("  ✏️ 现在处于【作业场景】,这里应该由 HomeworkWorkflow 来处理下一步。")
        else:
            print("  💬 现在处于【聊天场景】,这里应该由 ChatWorkflow 来生成回复。")
        
        print("-" * 60)


if __name__ == "__main__":
    interactive_loop()