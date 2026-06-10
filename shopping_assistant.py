"""可测试的导购对话编排层。"""
import json
from typing import Any, Dict, List, Optional, Tuple

from config.settings import settings
from llm.client import LLMClient, get_default_client
from rag.recommender import ProductCatalog, rule_reason
from user_profile.parser import default_profile, normalize_profile, parse_user_message, profile_summary


AI_STATUS_LABELS = {
    "enabled": "AI 已启用",
    "unconfigured": "AI 未配置，使用规则模式",
    "degraded": "AI 调用失败，已降级为规则模式",
}


class ShoppingAssistant:
    def __init__(self, catalog: ProductCatalog, llm_client: Optional[LLMClient] = None):
        self.catalog = catalog
        self.llm_client = llm_client or get_default_client()

    @property
    def initial_ai_status(self) -> str:
        return "enabled" if self.llm_client.configured else "unconfigured"

    def process_message(
        self,
        user_input: str,
        profile: Optional[Dict[str, Any]] = None,
        last_items: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        current_profile = normalize_profile(profile or default_profile())
        parsed = parse_user_message(user_input, current_profile, self.llm_client)
        updated_profile = parsed["profile"]

        if parsed["intent"] == "reset":
            return self._result(
                "偏好已重置。告诉我你喜欢的风格、IP 和预算，我会重新推荐。",
                default_profile(),
                [],
                "enabled" if parsed.get("ai_used") else self.initial_ai_status,
                "reset",
            )

        if parsed["intent"] == "compare":
            status = self._status(parsed.get("ai_used", False), parsed.get("ai_failed", False))
            return self._result(
                self._compare_items(last_items or [], parsed.get("compare_indices") or [], updated_profile),
                updated_profile,
                [],
                status,
                "compare",
            )

        if parsed.get("ask_question"):
            status = self._status(parsed.get("ai_used", False), parsed.get("ai_failed", False))
            return self._result(parsed["ask_question"], updated_profile, [], status, "recommend")

        candidates = self.catalog.search(updated_profile, limit=settings.DEFAULT_CANDIDATE_K)
        if not candidates:
            status = self._status(parsed.get("ai_used", False), parsed.get("ai_failed", False))
            reply = "没有找到满足预算和排除条件的商品。可以提高预算或减少排除条件后再试。"
            return self._result(reply, updated_profile, [], status, "recommend")

        ranked, summary, rerank_success, rerank_failed = self._rerank_with_ai(
            user_input, updated_profile, candidates
        )
        items = ranked[: settings.DEFAULT_SEARCH_K]
        ai_success = rerank_success
        ai_failed = rerank_failed
        status = self._status(ai_success, ai_failed)
        reply = self._build_recommendation_reply(summary, items, status)
        return self._result(reply, updated_profile, items, status, "recommend")

    @staticmethod
    def _result(reply, profile, items, ai_status, intent):
        return {
            "reply": reply,
            "profile": normalize_profile(profile),
            "items": items,
            "ai_status": ai_status,
            "intent": intent,
        }

    def _status(self, any_success: bool, any_failed: bool) -> str:
        if any_success:
            return "enabled"
        if self.llm_client.configured and any_failed:
            return "degraded"
        return "enabled" if self.llm_client.configured else "unconfigured"

    def _rerank_with_ai(
        self,
        user_input: str,
        profile: Dict[str, Any],
        candidates: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], str, bool, bool]:
        fallback_summary = "根据{}，为你找到以下商品。".format(profile_summary(profile))
        fallback = []
        for candidate in candidates:
            item = dict(candidate)
            item["reason"] = rule_reason(item)
            fallback.append(item)

        if not self.llm_client.configured:
            return fallback, fallback_summary, False, False

        compact_candidates = [
            {
                "id": item["id"],
                "name": item["name"],
                "price": item["price"],
                "ip": item["ip"],
                "style": item["style"],
                "description": item["description"][:220],
                "rule_score": item["score"],
            }
            for item in candidates
        ]
        prompt = {
            "user_input": user_input,
            "profile": normalize_profile(profile),
            "candidates": compact_candidates,
            "requirements": [
                "只能选择 candidates 中存在的 id",
                "按匹配度排序，最多返回 5 个不同 id",
                "理由只能使用候选商品中明确给出的事实",
                "summary 和 reason 使用简洁中文",
            ],
            "output_example": {
                "summary": "推荐总结",
                "selected": [{"id": "候选ID", "reason": "推荐理由"}],
            },
        }
        data = self.llm_client.chat_json(
            [
                {
                    "role": "system",
                    "content": "你是盲盒导购排序器。严格只输出 JSON，不得创造候选列表外的商品。",
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            temperature=0.1,
            max_tokens=900,
        )
        if not isinstance(data, dict) or not isinstance(data.get("selected"), list):
            return fallback, fallback_summary, False, True

        candidate_map = {item["id"]: item for item in candidates}
        ranked = []
        selected_ids = set()
        for selected in data["selected"]:
            if isinstance(selected, str):
                item_id, reason = selected, ""
            elif isinstance(selected, dict):
                item_id = str(selected.get("id", ""))
                reason = str(selected.get("reason", "")).strip()
            else:
                continue
            if item_id not in candidate_map or item_id in selected_ids:
                continue
            item = dict(candidate_map[item_id])
            item["reason"] = reason[:180] or rule_reason(item)
            ranked.append(item)
            selected_ids.add(item_id)

        if not ranked:
            return fallback, fallback_summary, False, True

        for candidate in candidates:
            if candidate["id"] not in selected_ids:
                item = dict(candidate)
                item["reason"] = rule_reason(item)
                ranked.append(item)

        summary = str(data.get("summary", "")).strip()[:240] or fallback_summary
        return ranked, summary, True, False

    @staticmethod
    def _build_recommendation_reply(summary: str, items: List[Dict[str, Any]], ai_status: str) -> str:
        prefix = ""
        if ai_status == "unconfigured":
            prefix = "当前未配置 AI，以下结果由规则引擎生成。\n\n"
        elif ai_status == "degraded":
            prefix = "AI 服务暂时不可用，以下结果由规则引擎生成。\n\n"

        lines = [prefix + summary]
        for index, item in enumerate(items, 1):
            lines.append(
                "{}. **{}** - ¥{:.2f}\n   {}".format(
                    index, item["name"], item["price"], item.get("reason") or rule_reason(item)
                )
            )
        return "\n\n".join(lines)

    @staticmethod
    def _compare_items(
        last_items: List[Dict[str, Any]],
        requested_indices: List[int],
        profile: Dict[str, Any],
    ) -> str:
        if len(last_items) < 2:
            return "上一轮没有足够的推荐商品可供比较，请先让我推荐一组商品。"

        indices = requested_indices[:2] if requested_indices else [0, 1]
        if len(indices) < 2:
            indices = [indices[0], 1 if indices[0] != 1 else 0]
        if any(index < 0 or index >= len(last_items) for index in indices):
            return "你指定的商品序号不在上一轮推荐中，请选择 1 到 {}。".format(len(last_items))

        selected = [last_items[index] for index in indices]
        lines = [
            "### 商品对比",
            "| 商品 | 价格 | IP | 风格 | 店铺 |",
            "|---|---:|---|---|---|",
        ]
        for item in selected:
            name = str(item.get("name", "")).replace("|", "/")
            lines.append(
                "| {} | ¥{:.2f} | {} | {} | {} |".format(
                    name,
                    item.get("price", 0),
                    item.get("ip", ""),
                    item.get("style", ""),
                    item.get("shop", ""),
                )
            )

        target = normalize_profile(profile).get("target_price")
        if target is not None:
            recommendation = min(selected, key=lambda item: abs(item.get("price", 0) - target))
            advice = "更接近你的目标价，建议优先考虑 **{}**。".format(recommendation["name"])
        else:
            recommendation = min(selected, key=lambda item: item.get("price", 0))
            advice = "如果优先考虑价格，建议选择 **{}**。".format(recommendation["name"])
        lines.extend(["", advice])
        return "\n".join(lines)
