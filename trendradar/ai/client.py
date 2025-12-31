# coding=utf-8
"""
DeepSeek 官方 API 客户端

兼容 OpenAI API 格式，调用 DeepSeek V3 模型
"""

import os
import json
from typing import Optional, List, Dict, Any

import requests


class DeepSeekClient:
    """DeepSeek 官方 API 客户端"""

    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 300,
    ):
        """
        初始化客户端

        Args:
            api_key: API 密钥，默认从环境变量 DEEPSEEK_API_KEY 获取
            base_url: API 基础 URL
            model: 模型名称
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.model = model or os.environ.get("DEEPSEEK_MODEL", self.DEFAULT_MODEL)
        self.timeout = timeout

        if not self.api_key:
            print("⚠️ 警告: 未配置 DEEPSEEK_API_KEY，AI 总结功能将不可用")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> Optional[str]:
        """
        调用聊天补全 API

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Returns:
            生成的文本内容，失败返回 None
        """
        if not self.api_key:
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                print(f"⚠️ AI API 返回格式异常: {result}")
                return None

        except requests.exceptions.Timeout:
            print(f"⚠️ AI API 请求超时 ({self.timeout}s)")
            return None
        except requests.exceptions.RequestException as e:
            print(f"⚠️ AI API 请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"⚠️ AI API 返回解析失败: {e}")
            return None

    def simple_chat(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        简单对话接口

        Args:
            prompt: 用户提问
            system_prompt: 系统提示词

        Returns:
            AI 回复内容
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self.chat_completion(messages)

    def is_available(self) -> bool:
        """检查 API 是否可用"""
        return bool(self.api_key)
