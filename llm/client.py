"""通用 OpenAI-compatible Chat Completions 客户端。"""
import json
import time
from typing import Any, Dict, List, Optional

import requests

from config.settings import settings


def extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """从纯 JSON 或 Markdown 代码块中提取一个 JSON 对象。"""
    if not text:
        return None

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "", 1).replace("```JSON", "", 1)
        cleaned = cleaned.replace("```", "").strip()

    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else None
    except (TypeError, ValueError):
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(cleaned[start:end + 1])
        return value if isinstance(value, dict) else None
    except (TypeError, ValueError):
        return None


class LLMClient:
    """最小化的 OpenAI-compatible 客户端，失败时返回 None。"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        session=None,
    ):
        self.base_url = (base_url if base_url is not None else settings.LLM_BASE_URL).strip().rstrip("/")
        self.api_key = (api_key if api_key is not None else settings.LLM_API_KEY).strip()
        self.model = (model if model is not None else settings.LLM_MODEL).strip()
        self.timeout = timeout if timeout is not None else settings.LLM_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else settings.LLM_MAX_RETRIES
        self.session = session or requests.Session()
        self.last_status = "unconfigured" if not self.configured else "ready"
        self.last_error = ""

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    @property
    def endpoint(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return self.base_url + "/chat/completions"

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        if not self.configured:
            self.last_status = "unconfigured"
            self.last_error = "LLM_BASE_URL、LLM_API_KEY 或 LLM_MODEL 未配置"
            return None

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": settings.LLM_TEMPERATURE if temperature is None else temperature,
            "max_tokens": settings.LLM_MAX_TOKENS if max_tokens is None else max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
        }

        attempts = max(1, self.max_retries + 1)
        for attempt in range(attempts):
            try:
                response = self.session.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    if isinstance(content, str) and content.strip():
                        self.last_status = "enabled"
                        self.last_error = ""
                        return content.strip()
                    self.last_error = "模型返回了空内容"
                    break

                self.last_error = "模型接口 HTTP {}".format(response.status_code)
                if response.status_code not in (408, 429) and response.status_code < 500:
                    break
            except (requests.Timeout, requests.ConnectionError) as exc:
                self.last_error = type(exc).__name__
            except (KeyError, IndexError, TypeError, ValueError, requests.RequestException) as exc:
                self.last_error = type(exc).__name__
                break

            if attempt + 1 < attempts:
                time.sleep(0.15)

        self.last_status = "degraded"
        return None

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        text = self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        data = extract_json_object(text or "")
        if text and data is None:
            self.last_status = "degraded"
            self.last_error = "模型返回内容不是有效 JSON"
        return data


def get_default_client() -> LLMClient:
    return LLMClient()
