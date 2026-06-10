import unittest

from rag.recommender import ProductCatalog, extract_source_url
from tests.helpers import sample_dataframe
from user_profile.parser import default_profile


class RecommenderTests(unittest.TestCase):
    def setUp(self):
        self.catalog = ProductCatalog(dataframe=sample_dataframe())

    def test_hard_budget_and_exclusions_are_never_relaxed(self):
        profile = default_profile()
        profile.update(
            {
                "preferred_styles": ["毛绒挂件"],
                "excluded_styles": ["暗黑潮酷"],
                "max_price": 150,
            }
        )
        results = self.catalog.search(profile, 20)

        self.assertTrue(results)
        self.assertTrue(all(item["price"] <= 150 for item in results))
        self.assertTrue(all(item["style"] != "暗黑潮酷" for item in results))
        self.assertEqual(results[0]["id"], "sanrio-plush")

    def test_series_is_deduplicated_by_source_url(self):
        profile = default_profile()
        profile["preferred_ips"] = ["MOLLY"]
        results = self.catalog.search(profile, 20)
        ids = {item["id"] for item in results}

        self.assertFalse({"molly-a", "molly-hidden"}.issubset(ids))

    def test_target_price_affects_order(self):
        profile = default_profile()
        profile["target_price"] = 125
        results = self.catalog.search(profile, 5)
        self.assertEqual(results[0]["id"], "sanrio-plush")

    def test_source_url_is_extracted(self):
        url = extract_source_url("description 来源: https://shop.example.com/item")
        self.assertEqual(url, "https://shop.example.com/item")

    def test_non_blindbox_badge_is_filtered(self):
        results = self.catalog.search(default_profile(), 20)
        self.assertNotIn("sanrio-badge", {item["id"] for item in results})

    def test_sold_out_product_is_filtered(self):
        results = self.catalog.search(default_profile(), 20)
        self.assertNotIn("sold-out-plush", {item["id"] for item in results})


if __name__ == "__main__":
    unittest.main()
