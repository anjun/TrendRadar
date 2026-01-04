# coding=utf-8
"""
新闻总结服务

使用 AI 模型对热点新闻进行智能总结
"""

from typing import List, Dict, Optional

from trendradar.ai.client import DeepSeekClient


class NewsSummarizer:
    """新闻总结器"""

    # 系统提示词
    SYSTEM_PROMPT = """你是一个专业的新闻摘要助手。你的任务是将热点新闻列表总结成简洁、有洞察力的摘要。

要求：
1. 按主题分类整理新闻，使用 emoji 标记不同类别
2. 每个类别下列出 2-3 条最重要的新闻要点
3. 对热点事件进行简短评论或背景补充
4. 语言简洁有力，突出重点
5. 总字数控制在 500 字以内
6. 使用 Markdown 格式输出
7. **重要：必须保留原文中的具体名称**，包括但不限于：
   - 公司全称或简称（如：航天宏图、比亚迪、宁德时代）
   - 股票代码（如：688066、300750）
   - 人物姓名
   - 具体金额、数据
   - 不要用"某公司"、"某股票"等模糊表述替代具体名称
8. **重要：必须在每条新闻要点后附上来源链接**，使用 Markdown 链接格式 [来源](url)。如果多条相似新闻被合并，只保留一个最具代表性的来源链接即可

输出格式示例：
🔥 **科技热点**
• 华为发布新产品，引发市场关注... [新浪财经](https://example.com/news1)
• OpenAI 在 AI 技术上取得突破性进展... [36氪](https://example.com/news2)

💰 **财经动态**
• 航天宏图(688066)因信披违规被立案调查... [同花顺](https://example.com/news3)

💡 **简要评论：** 今日市场热点集中在...

🌍 **社会民生**
• 重大政策解读... [央视新闻](https://example.com/news4)"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        初始化总结器

        Args:
            api_key: API 密钥
            model: 模型名称
        """
        self.client = DeepSeekClient(api_key=api_key, model=model)

    def summarize_news(
        self,
        stats: List[Dict],
        max_news: int = 50,
    ) -> Optional[str]:
        """
        总结热点新闻

        Args:
            stats: 统计数据列表，包含热点词汇和对应新闻
            max_news: 最大处理新闻数

        Returns:
            AI 生成的总结内容，失败返回 None
        """
        if not self.client.is_available():
            print("⚠️ AI 服务不可用，跳过新闻总结")
            return None

        # 构建新闻内容
        news_content = self._build_news_content(stats, max_news)
        if not news_content:
            print("⚠️ 没有新闻内容需要总结")
            return None

        # 构建提示词
        prompt = f"""请总结以下热点新闻：

{news_content}

请按照系统提示的格式输出总结。"""

        print(f"🤖 正在调用 AI 总结 {len(news_content)} 字符的新闻内容...")

        result = self.client.simple_chat(prompt, self.SYSTEM_PROMPT)

        if result:
            print(f"✅ AI 总结完成，生成 {len(result)} 字符")
        else:
            print("⚠️ AI 总结失败")

        return result

    def _build_news_content(self, stats: List[Dict], max_news: int) -> str:
        """
        构建新闻内容文本

        Args:
            stats: 统计数据列表
            max_news: 最大新闻数

        Returns:
            格式化的新闻文本
        """
        lines = []
        news_count = 0

        for stat in stats:
            if news_count >= max_news:
                break

            word = stat.get("word", "")
            titles = stat.get("titles", [])

            if not titles:
                continue

            # 添加关键词标题
            lines.append(f"【{word}】")

            for title_data in titles:
                if news_count >= max_news:
                    break

                title = title_data.get("title", "")
                source = title_data.get("source_name", "")
                # 优先使用 mobile_url，其次使用 url
                url = title_data.get("mobile_url") or title_data.get("url", "")

                if title:
                    if url:
                        lines.append(f"- {title} ({source}) [链接]({url})")
                    else:
                        lines.append(f"- {title} ({source})")
                    news_count += 1

            lines.append("")  # 空行分隔

        return "\n".join(lines)

    def is_available(self) -> bool:
        """检查总结服务是否可用"""
        return self.client.is_available()
