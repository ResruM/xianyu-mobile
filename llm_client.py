#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级 LLM 客户端（替代 openai 包）

只用标准库 urllib 实现，不需要安装 openai、httpx、pydantic、jiter 等依赖。
兼容 openai 包的核心调用方式：

    client = OpenAI(api_key=..., base_url=...)
    r = client.chat.completions.create(model=..., messages=[...], temperature=0.4)
    print(r.choices[0].message.content)
"""
import json
import time
import urllib.request
import urllib.error
import socket


class _Message:
    def __init__(self, content):
        self.content = content
        self.role = "assistant"


class _Choice:
    def __init__(self, message, finish_reason=None):
        self.message = message
        self.finish_reason = finish_reason


class _Response:
    def __init__(self, data):
        self._data = data
        self.choices = [
            _Choice(_Message(c.get("message", {}).get("content", "")),
                    c.get("finish_reason"))
            for c in data.get("choices", [])
        ]
        self.usage = data.get("usage", {})

    def __repr__(self):
        txt = self.choices[0].message.content if self.choices else ""
        return f"<Response: {txt[:50]}>"


class _Completions:
    def __init__(self, client):
        self._client = client

    def create(self, model=None, messages=None, temperature=0.7,
               max_tokens=500, top_p=1.0, timeout=60, **kwargs):
        return self._client._post(
            model=model, messages=messages or [],
            temperature=temperature, max_tokens=max_tokens,
            top_p=top_p, timeout=timeout,
        )


class _Chat:
    def __init__(self, client):
        self.completions = _Completions(client)


class OpenAI:
    """与 openai.OpenAI 用法兼容的精简实现"""

    def __init__(self, api_key=None, base_url=None, timeout=60, **kwargs):
        if not api_key:
            raise ValueError("缺少 API Key")
        self.api_key = api_key
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.timeout = timeout
        self.chat = _Chat(self)

    def _post(self, model, messages, temperature, max_tokens,
              top_p, timeout, retries=2):
        url = self.base_url + "/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "xianyu-mobile/1.0",
        }

        last_err = None
        for attempt in range(retries + 1):
            try:
                req = urllib.request.Request(url, data=body, headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw)
                if "choices" not in data:
                    err = data.get("error", {})
                    raise RuntimeError(
                        err.get("message") or f"接口返回异常: {raw[:200]}")
                return _Response(data)

            except urllib.error.HTTPError as e:
                detail = ""
                try:
                    detail = e.read().decode("utf-8", errors="replace")[:300]
                except Exception:
                    pass
                if e.code == 401:
                    raise RuntimeError(f"API Key 无效或已过期 (401)") from None
                if e.code == 402:
                    raise RuntimeError(f"账户余额不足 (402)") from None
                if e.code == 429:
                    last_err = RuntimeError("请求太频繁或超限 (429)")
                    time.sleep(2 * (attempt + 1))
                    continue
                if e.code == 404:
                    raise RuntimeError(
                        f"接口或模型不存在 (404)，请检查 MODEL_NAME/MODEL_BASE_URL\n{detail}"
                    ) from None
                last_err = RuntimeError(f"HTTP {e.code}: {detail}")

            except socket.timeout:
                last_err = RuntimeError(f"请求超时（{timeout}秒）")
            except urllib.error.URLError as e:
                last_err = RuntimeError(f"网络错误: {e.reason}")
            except json.JSONDecodeError:
                last_err = RuntimeError("接口返回的不是合法 JSON")

            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))

        raise last_err or RuntimeError("请求失败")
