import unittest

from user_profile.parser import default_profile, parse_user_message


class ProfileParserTests(unittest.TestCase):
    def test_rule_parser_extracts_negative_budget_style_and_purpose(self):
        result = parse_user_message("不要暗黑风，150元内毛绒送礼", default_profile())
        profile = result["profile"]

        self.assertEqual(result["intent"], "recommend")
        self.assertIn("暗黑潮酷", profile["excluded_styles"])
        self.assertIn("毛绒挂件", profile["preferred_styles"])
        self.assertIn("送礼", profile["purposes"])
        self.assertEqual(profile["max_price"], 150)
        self.assertIsNone(result["ask_question"])

    def test_follow_up_preserves_and_replaces_preferences(self):
        first = parse_user_message("想要 Molly，预算200以内", default_profile())
        second = parse_user_message("预算提高到300", first["profile"])
        third = parse_user_message("换成三丽鸥", second["profile"])

        self.assertIn("MOLLY", second["profile"]["preferred_ips"])
        self.assertEqual(second["profile"]["max_price"], 300)
        self.assertEqual(third["profile"]["preferred_ips"], ["SANRIO"])
        self.assertEqual(third["profile"]["max_price"], 300)

    def test_compare_indices_are_zero_based(self):
        result = parse_user_message("比较第一款和第三款", default_profile())
        self.assertEqual(result["intent"], "compare")
        self.assertEqual(result["compare_indices"], [0, 2])

    def test_reset_clears_profile(self):
        profile = parse_user_message("想要 Molly，预算200以内", default_profile())["profile"]
        result = parse_user_message("重置偏好", profile)
        self.assertEqual(result["intent"], "reset")
        self.assertEqual(result["profile"], default_profile())


if __name__ == "__main__":
    unittest.main()
