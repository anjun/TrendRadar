import os
import logging
import requests
from typing import List, Optional, Dict

# Configure logging
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = self.config.get("ENABLED", False)
        self.api_key = self.config.get("API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("SILICONFLOW_API_KEY")
        self.base_url = self.config.get("BASE_URL", "https://api.siliconflow.cn/v1")
        self.model = self.config.get("MODEL", "deepseek-ai/DeepSeek-V3")
        self.prompt = self.config.get("PROMPT", "请分析以下新闻：")
        self.timeout = self.config.get("TIMEOUT", 60)
        self.target_platforms = self.config.get("TARGET_PLATFORMS", [])

        if self.enabled and not self.api_key:
            # Check if we can find it in os.environ with other names
            if not self.api_key:
                logger.warning("AI analysis enabled but no API key found. Disabling.")
                self.enabled = False

    def analyze_titles(self, titles: List[str]) -> Optional[str]:
        if not self.enabled or not titles:
            return None
            
        # Format content
        content = "\n".join([f"- {t}" for t in titles])
        full_prompt = f"{self.prompt}\n\n{content}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": full_prompt}
            ],
            "stream": False
        }
        
        try:
            print(f"正在调用 AI 分析 ({self.model})...")
            response = requests.post(
                f"{self.base_url}/chat/completions", 
                headers=headers, 
                json=payload, 
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            analysis = result["choices"][0]["message"]["content"].strip()
            print("AI 分析完成")
            return analysis
        except Exception as e:
            logger.error(f"AI analysis failed (URL: {self.base_url}): {e}")
            print(f"AI 分析失败: {e}")
            return None

    def should_analyze_platform(self, platform_id: str) -> bool:
        if not self.enabled:
            return False
        if not self.target_platforms:
            return True # If no targets specified, analyze all (or maybe none? Assume strict)
        # If targets specified, only allow those
        return platform_id in self.target_platforms
