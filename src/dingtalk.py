import os
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class DingTalkNotifier:
    """钉钉机器人通知器"""
    
    def __init__(self, webhook: str = None, secret: str = None):
        self.webhook = webhook or os.getenv("DINGTALK_WEBHOOK")
        self.secret = secret or os.getenv("DINGTALK_SECRET", "")
        
        if not self.webhook:
            logger.warning("DINGTALK_WEBHOOK not found")
    
    def _sign(self) -> str:
        """生成签名"""
        if not self.secret:
            return ""
        
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        return f"&timestamp={timestamp}&sign={sign}"
    
    def send_text(self, content: str, at_mobiles: list = None, is_at_all: bool = False) -> bool:
        """发送文本消息"""
        if not self.webhook:
            logger.error("Webhook not configured")
            return False
        
        url = f"{self.webhook}{self._sign()}"
        
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": is_at_all
            }
        }
        
        try:
            response = requests.post(url, data=json.dumps(data), timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info("Message sent successfully")
                return True
            else:
                logger.error(f"Failed to send message: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def send_markdown(self, title: str, content: str) -> bool:
        """发送 Markdown 消息"""
        if not self.webhook:
            logger.error("Webhook not configured")
            return False
        
        url = f"{self.webhook}{self._sign()}"
        
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content
            }
        }
        
        try:
            response = requests.post(url, data=json.dumps(data), timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info("Markdown message sent successfully")
                return True
            else:
                logger.error(f"Failed to send markdown: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending markdown: {e}")
            return False
    
    def send_weekly_report(self, title: str, report_content: str) -> bool:
        """发送周报"""
        markdown_content = f"""## {title}

{report_content}

---
*由 GitHub Actions 自动生成*"""
        
        return self.send_markdown(title, markdown_content)


def create_notifier(config: Dict = None) -> DingTalkNotifier:
    """创建钉钉通知器"""
    if config:
        webhook = config.get("webhook", "").replace("${DINGTALK_WEBHOOK}", os.getenv("DINGTALK_WEBHOOK", ""))
        secret = config.get("secret", "")
        return DingTalkNotifier(webhook=webhook, secret=secret)
    
    return DingTalkNotifier()
