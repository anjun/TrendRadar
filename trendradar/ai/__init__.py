# coding=utf-8
"""
AI 模块 - 提供 AI 新闻总结功能

使用硅基流动平台的 DeepSeek V3 模型
"""

from trendradar.ai.client import DeepSeekClient
from trendradar.ai.summarizer import NewsSummarizer

__all__ = ["DeepSeekClient", "NewsSummarizer"]
