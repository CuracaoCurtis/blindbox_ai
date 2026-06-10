import unittest
from unittest.mock import Mock

import requests

from llm.client import LLMClient, extract_json_object


class FakeResponse:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class LLMClientTests(unittest.TestCase):
    def build_client(self, session, retries=1):
        return LLMClient(
            base_url="https://api.example.com/v1",
            api_key="secret",
            model="test-model",
            timeout=1,
            max_retries=retries,
            session=session,
        )

    def test_success_and_endpoint(self):
        session = Mock()
        session.post.return_value = FakeResponse(
            200, {"choices": [{"message": {"content": "OK"}}]}
        )
        client = self.build_client(session)

        self.assertEqual(client.chat([{"role": "user", "content": "hello"}]), "OK")
        self.assertEqual(client.last_status, "enabled")
        self.assertEqual(session.post.call_args.args[0], "https://api.example.com/v1/chat/completions")

    def test_timeout_is_retried_once(self):
        session = Mock()
        session.post.side_effect = [
            requests.Timeout(),
            FakeResponse(200, {"choices": [{"message": {"content": "after retry"}}]}),
        ]
        client = self.build_client(session, retries=1)

        self.assertEqual(client.chat([{"role": "user", "content": "hello"}]), "after retry")
        self.assertEqual(session.post.call_count, 2)

    def test_markdown_json_and_invalid_json(self):
        self.assertEqual(extract_json_object("```json\n{\"ok\": true}\n```"), {"ok": True})

        session = Mock()
        session.post.return_value = FakeResponse(
            200, {"choices": [{"message": {"content": "not json"}}]}
        )
        client = self.build_client(session)
        self.assertIsNone(client.chat_json([{"role": "user", "content": "json"}]))
        self.assertEqual(client.last_status, "degraded")

    def test_unconfigured_client_does_not_call_network(self):
        session = Mock()
        client = LLMClient(base_url="", api_key="", model="", session=session)
        self.assertIsNone(client.chat([{"role": "user", "content": "hello"}]))
        session.post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
