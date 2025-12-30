# coding=utf-8
"""
配置加载模块

负责从 YAML 配置文件和环境变量加载配置。
支持从 .env 文件加载本地开发配置。
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

from .config import parse_multi_account_config, validate_paired_configs


def _load_dotenv(env_path: str = ".env") -> bool:
    """
    加载 .env 文件到环境变量（简易实现，无需 python-dotenv 依赖）

    Args:
        env_path: .env 文件路径

    Returns:
        是否成功加载
    """
    env_file = Path(env_path)
    if not env_file.exists():
        return False

    loaded_count = 0
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith("#"):
                    continue
                # 解析 KEY=VALUE 格式
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    # 移除引号
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    # 只有环境变量未设置时才加载
                    if key and key not in os.environ:
                        os.environ[key] = value
                        loaded_count += 1
        if loaded_count > 0:
            print(f"📄 从 .env 文件加载了 {loaded_count} 个环境变量")
        return True
    except Exception as e:
        print(f"⚠️ 加载 .env 文件失败: {e}")
        return False


# 模块加载时自动加载 .env 文件
_load_dotenv()


def _get_env_bool(key: str, default: bool = False) -> Optional[bool]:
    """从环境变量获取布尔值，如果未设置返回 None"""
    value = os.environ.get(key, "").strip().lower()
    if not value:
        return None
    return value in ("true", "1")


def _get_env_int(key: str, default: int = 0) -> int:
    """从环境变量获取整数值"""
    value = os.environ.get(key, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_env_str(key: str, default: str = "") -> str:
    """从环境变量获取字符串值"""
    return os.environ.get(key, "").strip() or default


def _load_app_config(config_data: Dict) -> Dict:
    """加载应用配置"""
    app_config = config_data.get("app", {})
    return {
        "VERSION_CHECK_URL": app_config.get("version_check_url", ""),
        "SHOW_VERSION_UPDATE": app_config.get("show_version_update", True),
        "TIMEZONE": _get_env_str("TIMEZONE") or app_config.get("timezone", "Asia/Shanghai"),
    }


def _load_crawler_config(config_data: Dict) -> Dict:
    """加载爬虫配置"""
    crawler_config = config_data.get("crawler", {})
    enable_crawler_env = _get_env_bool("ENABLE_CRAWLER")
    return {
        "REQUEST_INTERVAL": crawler_config.get("request_interval", 100),
        "USE_PROXY": crawler_config.get("use_proxy", False),
        "DEFAULT_PROXY": crawler_config.get("default_proxy", ""),
        "ENABLE_CRAWLER": enable_crawler_env if enable_crawler_env is not None else crawler_config.get("enable_crawler", True),
    }


def _load_report_config(config_data: Dict) -> Dict:
    """加载报告配置"""
    report_config = config_data.get("report", {})

    # 环境变量覆盖
    sort_by_position_env = _get_env_bool("SORT_BY_POSITION_FIRST")
    reverse_content_env = _get_env_bool("REVERSE_CONTENT_ORDER")
    max_news_env = _get_env_int("MAX_NEWS_PER_KEYWORD")

    return {
        "REPORT_MODE": _get_env_str("REPORT_MODE") or report_config.get("mode", "daily"),
        "RANK_THRESHOLD": report_config.get("rank_threshold", 10),
        "SORT_BY_POSITION_FIRST": sort_by_position_env if sort_by_position_env is not None else report_config.get("sort_by_position_first", False),
        "MAX_NEWS_PER_KEYWORD": max_news_env or report_config.get("max_news_per_keyword", 0),
        "REVERSE_CONTENT_ORDER": reverse_content_env if reverse_content_env is not None else report_config.get("reverse_content_order", False),
    }


def _load_notification_config(config_data: Dict) -> Dict:
    """加载通知配置"""
    notification = config_data.get("notification", {})
    enable_notification_env = _get_env_bool("ENABLE_NOTIFICATION")

    return {
        "ENABLE_NOTIFICATION": enable_notification_env if enable_notification_env is not None else notification.get("enable_notification", True),
        "MESSAGE_BATCH_SIZE": notification.get("message_batch_size", 4000),
        "DINGTALK_BATCH_SIZE": notification.get("dingtalk_batch_size", 20000),
        "FEISHU_BATCH_SIZE": notification.get("feishu_batch_size", 29000),
        "BARK_BATCH_SIZE": notification.get("bark_batch_size", 3600),
        "SLACK_BATCH_SIZE": notification.get("slack_batch_size", 4000),
        "BATCH_SEND_INTERVAL": notification.get("batch_send_interval", 1.0),
        "FEISHU_MESSAGE_SEPARATOR": notification.get("feishu_message_separator", "---"),
        "MAX_ACCOUNTS_PER_CHANNEL": _get_env_int("MAX_ACCOUNTS_PER_CHANNEL") or notification.get("max_accounts_per_channel", 3),
    }


def _load_push_window_config(config_data: Dict) -> Dict:
    """加载推送窗口配置"""
    notification = config_data.get("notification", {})
    push_window = notification.get("push_window", {})
    time_range = push_window.get("time_range", {})

    enabled_env = _get_env_bool("PUSH_WINDOW_ENABLED")
    once_per_day_env = _get_env_bool("PUSH_WINDOW_ONCE_PER_DAY")

    return {
        "ENABLED": enabled_env if enabled_env is not None else push_window.get("enabled", False),
        "TIME_RANGE": {
            "START": _get_env_str("PUSH_WINDOW_START") or time_range.get("start", "08:00"),
            "END": _get_env_str("PUSH_WINDOW_END") or time_range.get("end", "22:00"),
        },
        "ONCE_PER_DAY": once_per_day_env if once_per_day_env is not None else push_window.get("once_per_day", True),
    }


def _load_weight_config(config_data: Dict) -> Dict:
    """加载权重配置"""
    weight = config_data.get("weight", {})
    return {
        "RANK_WEIGHT": weight.get("rank_weight", 1.0),
        "FREQUENCY_WEIGHT": weight.get("frequency_weight", 1.0),
        "HOTNESS_WEIGHT": weight.get("hotness_weight", 1.0),
    }


def _load_storage_config(config_data: Dict) -> Dict:
    """加载存储配置"""
    storage = config_data.get("storage", {})
    formats = storage.get("formats", {})
    local = storage.get("local", {})
    remote = storage.get("remote", {})
    pull = storage.get("pull", {})

    txt_enabled_env = _get_env_bool("STORAGE_TXT_ENABLED")
    html_enabled_env = _get_env_bool("STORAGE_HTML_ENABLED")
    pull_enabled_env = _get_env_bool("PULL_ENABLED")

    return {
        "BACKEND": _get_env_str("STORAGE_BACKEND") or storage.get("backend", "auto"),
        "FORMATS": {
            "SQLITE": formats.get("sqlite", True),
            "TXT": txt_enabled_env if txt_enabled_env is not None else formats.get("txt", True),
            "HTML": html_enabled_env if html_enabled_env is not None else formats.get("html", True),
        },
        "LOCAL": {
            "DATA_DIR": local.get("data_dir", "output"),
            "RETENTION_DAYS": _get_env_int("LOCAL_RETENTION_DAYS") or local.get("retention_days", 0),
        },
        "REMOTE": {
            "ENDPOINT_URL": _get_env_str("S3_ENDPOINT_URL") or remote.get("endpoint_url", ""),
            "BUCKET_NAME": _get_env_str("S3_BUCKET_NAME") or remote.get("bucket_name", ""),
            "ACCESS_KEY_ID": _get_env_str("S3_ACCESS_KEY_ID") or remote.get("access_key_id", ""),
            "SECRET_ACCESS_KEY": _get_env_str("S3_SECRET_ACCESS_KEY") or remote.get("secret_access_key", ""),
            "REGION": _get_env_str("S3_REGION") or remote.get("region", ""),
            "RETENTION_DAYS": _get_env_int("REMOTE_RETENTION_DAYS") or remote.get("retention_days", 0),
        },
        "PULL": {
            "ENABLED": pull_enabled_env if pull_enabled_env is not None else pull.get("enabled", False),
            "DAYS": _get_env_int("PULL_DAYS") or pull.get("days", 7),
        },
    }


def _load_webhook_config(config_data: Dict) -> Dict:
    """加载 Webhook 配置"""
    notification = config_data.get("notification", {})
    webhooks = notification.get("webhooks", {})

    return {
        # 飞书
        "FEISHU_WEBHOOK_URL": _get_env_str("FEISHU_WEBHOOK_URL") or webhooks.get("feishu_url", ""),
        # 钉钉
        "DINGTALK_WEBHOOK_URL": _get_env_str("DINGTALK_WEBHOOK_URL") or webhooks.get("dingtalk_url", ""),
        # 企业微信
        "WEWORK_WEBHOOK_URL": _get_env_str("WEWORK_WEBHOOK_URL") or webhooks.get("wework_url", ""),
        "WEWORK_MSG_TYPE": _get_env_str("WEWORK_MSG_TYPE") or webhooks.get("wework_msg_type", "markdown"),
        # Telegram
        "TELEGRAM_BOT_TOKEN": _get_env_str("TELEGRAM_BOT_TOKEN") or webhooks.get("telegram_bot_token", ""),
        "TELEGRAM_CHAT_ID": _get_env_str("TELEGRAM_CHAT_ID") or webhooks.get("telegram_chat_id", ""),
        # 邮件
        "EMAIL_FROM": _get_env_str("EMAIL_FROM") or webhooks.get("email_from", ""),
        "EMAIL_PASSWORD": _get_env_str("EMAIL_PASSWORD") or webhooks.get("email_password", ""),
        "EMAIL_TO": _get_env_str("EMAIL_TO") or webhooks.get("email_to", ""),
        "EMAIL_SMTP_SERVER": _get_env_str("EMAIL_SMTP_SERVER") or webhooks.get("email_smtp_server", ""),
        "EMAIL_SMTP_PORT": _get_env_str("EMAIL_SMTP_PORT") or webhooks.get("email_smtp_port", ""),
        # ntfy
        "NTFY_SERVER_URL": _get_env_str("NTFY_SERVER_URL") or webhooks.get("ntfy_server_url") or "https://ntfy.sh",
        "NTFY_TOPIC": _get_env_str("NTFY_TOPIC") or webhooks.get("ntfy_topic", ""),
        "NTFY_TOKEN": _get_env_str("NTFY_TOKEN") or webhooks.get("ntfy_token", ""),
        # Bark
        "BARK_URL": _get_env_str("BARK_URL") or webhooks.get("bark_url", ""),
        # Slack
        "SLACK_WEBHOOK_URL": _get_env_str("SLACK_WEBHOOK_URL") or webhooks.get("slack_webhook_url", ""),
    }


def _print_notification_sources(config: Dict) -> None:
    """打印通知渠道配置来源信息"""
    notification_sources = []
    max_accounts = config["MAX_ACCOUNTS_PER_CHANNEL"]

    if config["FEISHU_WEBHOOK_URL"]:
        accounts = parse_multi_account_config(config["FEISHU_WEBHOOK_URL"])
        count = min(len(accounts), max_accounts)
        source = "环境变量" if os.environ.get("FEISHU_WEBHOOK_URL") else "配置文件"
        notification_sources.append(f"飞书({source}, {count}个账号)")

    if config["DINGTALK_WEBHOOK_URL"]:
        accounts = parse_multi_account_config(config["DINGTALK_WEBHOOK_URL"])
        count = min(len(accounts), max_accounts)
        source = "环境变量" if os.environ.get("DINGTALK_WEBHOOK_URL") else "配置文件"
        notification_sources.append(f"钉钉({source}, {count}个账号)")

    if config["WEWORK_WEBHOOK_URL"]:
        accounts = parse_multi_account_config(config["WEWORK_WEBHOOK_URL"])
        count = min(len(accounts), max_accounts)
        source = "环境变量" if os.environ.get("WEWORK_WEBHOOK_URL") else "配置文件"
        notification_sources.append(f"企业微信({source}, {count}个账号)")

    if config["TELEGRAM_BOT_TOKEN"] and config["TELEGRAM_CHAT_ID"]:
        tokens = parse_multi_account_config(config["TELEGRAM_BOT_TOKEN"])
        chat_ids = parse_multi_account_config(config["TELEGRAM_CHAT_ID"])
        valid, count = validate_paired_configs(
            {"bot_token": tokens, "chat_id": chat_ids},
            "Telegram",
            required_keys=["bot_token", "chat_id"]
        )
        if valid and count > 0:
            count = min(count, max_accounts)
            token_source = "环境变量" if os.environ.get("TELEGRAM_BOT_TOKEN") else "配置文件"
            notification_sources.append(f"Telegram({token_source}, {count}个账号)")

    if config["EMAIL_FROM"] and config["EMAIL_PASSWORD"] and config["EMAIL_TO"]:
        from_source = "环境变量" if os.environ.get("EMAIL_FROM") else "配置文件"
        notification_sources.append(f"邮件({from_source})")

    if config["NTFY_SERVER_URL"] and config["NTFY_TOPIC"]:
        topics = parse_multi_account_config(config["NTFY_TOPIC"])
        tokens = parse_multi_account_config(config["NTFY_TOKEN"])
        if tokens:
            valid, count = validate_paired_configs(
                {"topic": topics, "token": tokens},
                "ntfy"
            )
            if valid and count > 0:
                count = min(count, max_accounts)
                server_source = "环境变量" if os.environ.get("NTFY_SERVER_URL") else "配置文件"
                notification_sources.append(f"ntfy({server_source}, {count}个账号)")
        else:
            count = min(len(topics), max_accounts)
            server_source = "环境变量" if os.environ.get("NTFY_SERVER_URL") else "配置文件"
            notification_sources.append(f"ntfy({server_source}, {count}个账号)")

    if config["BARK_URL"]:
        accounts = parse_multi_account_config(config["BARK_URL"])
        count = min(len(accounts), max_accounts)
        bark_source = "环境变量" if os.environ.get("BARK_URL") else "配置文件"
        notification_sources.append(f"Bark({bark_source}, {count}个账号)")

    if config["SLACK_WEBHOOK_URL"]:
        accounts = parse_multi_account_config(config["SLACK_WEBHOOK_URL"])
        count = min(len(accounts), max_accounts)
        slack_source = "环境变量" if os.environ.get("SLACK_WEBHOOK_URL") else "配置文件"
        notification_sources.append(f"Slack({slack_source}, {count}个账号)")

    if notification_sources:
        print(f"通知渠道配置来源: {', '.join(notification_sources)}")
        print(f"每个渠道最大账号数: {max_accounts}")
    else:
        print("未配置任何通知渠道")


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件

    Args:
        config_path: 配置文件路径，默认从环境变量 CONFIG_PATH 获取或使用 config/config.yaml

    Returns:
        包含所有配置的字典

    Raises:
        FileNotFoundError: 配置文件不存在
    """
    if config_path is None:
        config_path = os.environ.get("CONFIG_PATH", "config/config.yaml")

    if not Path(config_path).exists():
        raise FileNotFoundError(f"配置文件 {config_path} 不存在")

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    print(f"配置文件加载成功: {config_path}")

    # 合并所有配置
    config = {}

    # 应用配置
    config.update(_load_app_config(config_data))

    # 爬虫配置
    config.update(_load_crawler_config(config_data))

    # 报告配置
    config.update(_load_report_config(config_data))

    # 通知配置
    config.update(_load_notification_config(config_data))

    # 推送窗口配置
    config["PUSH_WINDOW"] = _load_push_window_config(config_data)

    # 权重配置
    config["WEIGHT_CONFIG"] = _load_weight_config(config_data)

    # 平台配置
    config["PLATFORMS"] = config_data.get("platforms", [])

    # 存储配置
    config["STORAGE"] = _load_storage_config(config_data)

    # Webhook 配置
    config.update(_load_webhook_config(config_data))

    # 打印通知渠道配置来源
    _print_notification_sources(config)

    return config
