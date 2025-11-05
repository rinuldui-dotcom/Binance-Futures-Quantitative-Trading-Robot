import logging
from typing import Dict, List
from .telegram_notifier import TelegramNotifier
from .email_notifier import EmailNotifier

class NotificationManager:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.notifiers = []
        
        self.setup_notifiers()
        
    def setup_notifiers(self):
        """设置通知器"""
        # Telegram 通知
        if self.config['notifications']['telegram']['enabled']:
            self.notifiers.append(TelegramNotifier(self.config))
            
        # 邮件通知
        if self.config['notifications']['email']['enabled']:
            self.notifiers.append(EmailNotifier(self.config))
            
        self.logger.info(f"初始化 {len(self.notifiers)} 个通知器")
        
    async def send_message(self, message: str, event_type: str = "info"):
        """发送消息"""
        for notifier in self.notifiers:
            try:
                if notifier.should_notify(event_type):
                    await notifier.send(message, event_type)
            except Exception as e:
                self.logger.error(f"发送通知失败 {notifier.__class__.__name__}: {e}")
                
    async def send_alert(self, title: str, message: str, level: str = "warning"):
        """发送警报"""
        alert_message = f"🚨 {title}\n{message}"
        await self.send_message(alert_message, level)
