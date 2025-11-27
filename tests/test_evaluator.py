import json
from typing import List, Dict, Any

import config
from src.models import Scene, SessionState, PendingSwitch
from src.router import call_llm_router, router_output_to_dict
from src.guardrails import apply_guardrails


def load_test_dataset() -> List[Dict[str, Any]]:
    """从 JSON 文件加载测试数据集"""
    try:
        with open(config.TEST_DATASET_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(
            f"测试数据集文件不存在: {config.TEST_DATASET_FILE}\n"
            "请确保 data/test_dataset.json 文件存在"
        )


def build_state_from_sample(sample: Dict[str, Any]) -> SessionState:
    """根据测试样本构建会话状态"""
    st_def = sample["state"]
    active_scene = Scene(st_def["active_scene"])
    state = SessionState(active_scene=active_scene)
    
    if st_def.get("pending"):
        target = Scene(st_def["pending"]["target_scene"])
        state.pending_switch = PendingSwitch(
            target_scene=target,
            slots={},
            age_turns=0
        )
    
    return state


def run_offline_eval():
    """运行离线评测"""
    dataset = load_test_dataset()
    total = len(dataset)
    correct_scene = 0
    correct_action = 0
    errors: List[Dict[str, Any]] = []
    
    print("=" * 50)
    print("离线评测开始")
    print("=" * 50)
    print(f"样本数量: {total}")
    print()
    
    for idx, sample in enumerate(dataset, 1):
        print(f"处理样本 {idx}/{total}...", end='\r')
        
        state = build_state_from_sample(sample)
        user = sample["user"]
        
        # 调用路由器和 Guardrails
        router_out = call_llm_router(user, state)
        route_dict = router_output_to_dict(router_out)
        decision = apply_guardrails(route_dict, state)
        
        # 比对结果
        pred_scene = decision.target_scene.value
        pred_action = decision.action
        gold_scene = sample["gold_scene"]
        gold_action = sample["gold_action"]
        
        is_scene_ok = pred_scene == gold_scene
        is_action_ok = pred_action == gold_action
        
        if is_scene_ok:
            correct_scene += 1
        else:
            errors.append({
                "id": sample["id"],
                "kind": "scene",
                "gold": gold_scene,
                "pred": pred_scene,
                "route": route_dict,
                "user": user,
            })
        
        if is_action_ok:
            correct_action += 1
        else:
            errors.append({
                "id": sample["id"],
                "kind": "action",
                "gold": gold_action,
                "pred": pred_action,
                "route": route_dict,
                "user": user,
            })
    
    print()  # 清除进度提示
    print("=" * 50)
    print("评测结果")
    print("=" * 50)
    print(f"场景预测正确: {correct_scene}/{total} ({correct_scene/total:.1%})")
    print(f"动作预测正确: {correct_action}/{total} ({correct_action/total:.1%})")
    
    if errors:
        print(f"\n错误样例 (共 {len(errors)} 条,最多显示 10 条):")
        print("-" * 50)
        for err in errors[:10]:
            print(f"\n样本 {err['id']} [{err['kind']}错误]")
            print(f"  用户输入: {err['user']}")
            print(f"  标注答案: {err['gold']}")
            print(f"  预测结果: {err['pred']}")
            r = err["route"]
            print(f"  Router: intent={r['intent']}, score={r['score']}, conf={r['confidence']}")
            print(f"  理由: {r['reason']}")
    else:
        print("\n🎉 全部预测正确!")
    
    print("=" * 50)


if __name__ == "__main__":
    run_offline_eval()