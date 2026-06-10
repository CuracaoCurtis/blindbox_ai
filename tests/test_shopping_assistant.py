import json
import unittest

from rag.recommender import ProductCatalog
from shopping_assistant import ShoppingAssistant
from tests.helpers import sample_dataframe
from user_profile.parser import default_profile


class UnconfiguredLLM:
    configured = False


class DynamicLLM:
    configured = True

    def __init__(self, hallucinate=False):
        self.hallucinate = hallucinate
        self.calls = 0

    def chat_json(self, messages, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return {
                "intent": "recommend",
                "profile_updates": {
                    "preferred_ips": ["SANRIO"],
                    "preferred_styles": ["毛绒挂件"],
                    "max_price": 150,
                },
                "clear_fields": [],
                "compare_indices": [],
                "ask_question": None,
            }
        payload = json.loads(messages[1]["content"])
        if self.hallucinate:
            selected = [{"id": "invented-product", "reason": "不存在的商品"}]
        else:
            selected = [{"id": payload["candidates"][0]["id"], "reason": "匹配预算和偏好"}]
        return {"summary": "AI 推荐结果", "selected": selected}


class ShoppingAssistantTests(unittest.TestCase):
    def setUp(self):
        self.catalog = ProductCatalog(dataframe=sample_dataframe())

    def test_rule_mode_recommends_real_products_and_compares(self):
        assistant = ShoppingAssistant(self.catalog, UnconfiguredLLM())
        result = assistant.process_message("不要暗黑风，150元内毛绒送礼", default_profile())

        self.assertEqual(result["ai_status"], "unconfigured")
        self.assertTrue(result["items"])
        self.assertTrue(all(item["price"] <= 150 for item in result["items"]))
        self.assertNotIn("dark-figure", {item["id"] for item in result["items"]})

        compare = assistant.process_message("比较第一款和第二款", result["profile"], result["items"])
        self.assertEqual(compare["intent"], "compare")
        self.assertIn("商品对比", compare["reply"])
        self.assertIn(result["items"][0]["name"], compare["reply"])

    def test_valid_ai_rerank_is_used(self):
        assistant = ShoppingAssistant(self.catalog, DynamicLLM())
        result = assistant.process_message("三丽鸥毛绒，预算150以内", default_profile())

        self.assertEqual(result["ai_status"], "enabled")
        self.assertEqual(result["items"][0]["reason"], "匹配预算和偏好")
        self.assertIn("AI 推荐结果", result["reply"])

    def test_hallucinated_candidate_id_is_discarded(self):
        assistant = ShoppingAssistant(self.catalog, DynamicLLM(hallucinate=True))
        result = assistant.process_message("三丽鸥毛绒，预算150以内", default_profile())
        ids = {item["id"] for item in result["items"]}

        self.assertNotIn("invented-product", ids)
        self.assertTrue(ids)
        self.assertEqual(result["ai_status"], "degraded")
        self.assertIn("AI 服务暂时不可用", result["reply"])


if __name__ == "__main__":
    unittest.main()
