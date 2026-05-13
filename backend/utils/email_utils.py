import imaplib
import email
from email.header import decode_header
import os
import logging
from datetime import datetime
import time

# 如果项目中已经配置了统一的 logger，您可以替换成项目现有的 logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailUtility:
    """
    邮件读取工具类，支持通过 IMAP 和授权码读取邮件主题、发件人、收件人、正文及附件。
    """
    
    def __init__(self, imap_server: str, email_addr: str, auth_code: str, attachment_dir: str = "./attachments"):
        """
        初始化邮件工具类
        :param imap_server: IMAP 服务器地址 (例如: 'imap.qq.com', 'imap.exmail.qq.com', 'imap.163.com')
        :param email_addr: 邮箱账号
        :param auth_code: 邮箱授权码/密码
        :param attachment_dir: 附件保存的本地目录路径
        """
        self.imap_server = imap_server
        self.email_addr = email_addr
        self.auth_code = auth_code
        self.attachment_dir = attachment_dir
        self.mail = None
        
        # 确保附件保存的本地目录存在
        if not os.path.exists(self.attachment_dir):
            os.makedirs(self.attachment_dir)
            logger.info(f"已创建附件保存目录: {os.path.abspath(self.attachment_dir)}")

    def connect(self):
        """连接 IMAP 服务器并登录"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_addr, self.auth_code)
            logger.info("✅ 成功连接到邮箱服务器并完成登录。")
        except Exception as e:
            logger.error(f"❌ 连接或登录邮箱失败: {e}")
            raise e

    def disconnect(self):
        """断开连接"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
                logger.info("🔌 已断开邮箱连接。")
            except Exception as e:
                logger.error(f"断开连接时发生异常: {e}")

    def decode_str(self, s: str) -> str:
        """解析并解码邮件头中的字符 (处理不同的编码格式)"""
        if not s:
            return ""
        decoded_list = decode_header(s)
        res = ""
        for decoded_bytes, charset in decoded_list:
            if isinstance(decoded_bytes, bytes):
                if charset:
                    try:
                        res += decoded_bytes.decode(charset)
                    except (LookupError, UnicodeDecodeError):
                        res += decoded_bytes.decode("utf-8", errors="replace")
                else:
                    res += decoded_bytes.decode("utf-8", errors="replace")
            else:
                res += str(decoded_bytes)
        return res

    def fetch_emails(self, since_date: datetime, until_date: datetime = None, folder: str = "INBOX"):
        """
        根据时间段筛选并读取邮件信息
        :param since_date: 起始时间 (datetime)
        :param until_date: 结束时间 (datetime)，不填则默认搜索到最新
        :param folder: 要搜索的邮件文件夹，默认为收件箱 (INBOX)
        """
        if not self.mail:
            logger.error("请先调用 connect() 方法连接邮箱！")
            return

        try:
            self.mail.select(folder)
            
            # 构造 IMAP 的日期搜索格式，例如 "01-Jan-2023"
            since_str = since_date.strftime("%d-%b-%Y")
            search_criteria = f'(SINCE "{since_str}")'
            
            if until_date:
                until_str = until_date.strftime("%d-%b-%Y")
                search_criteria = f'(SINCE "{since_str}" BEFORE "{until_str}")'

            logger.info(f"🔍 开始搜索邮件，搜索条件: {search_criteria}")
            status, messages = self.mail.search(None, search_criteria)
            
            if status != "OK":
                logger.error("搜索邮件失败，请检查条件。")
                return

            mail_ids = messages[0].split()
            logger.info(f"📬 共找到 {len(mail_ids)} 封符合条件的邮件。")

            # 遍历并解析每封邮件（为了效率，可以根据需求控制只读取前 N 封，或倒序处理）
            for mail_id in mail_ids:
                status, msg_data = self.mail.fetch(mail_id, "(RFC822)")
                if status != "OK":
                    logger.error(f"无法获取邮件 ID: {mail_id.decode('utf-8')}")
                    continue
                    
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        # 解析为 Email 消息对象
                        msg = email.message_from_bytes(response_part[1])
                        self._parse_and_log_email(msg)
                        
        except Exception as e:
            logger.error(f"读取邮件时发生异常: {e}")

    def _parse_and_log_email(self, msg):
        """解析单封邮件的字段、正文及附件"""
        subject = self.decode_str(msg.get("Subject"))
        sender = self.decode_str(msg.get("From"))
        receiver = self.decode_str(msg.get("To"))
        date = self.decode_str(msg.get("Date"))
        
        logger.info("=" * 60)
        logger.info(f"📅 发送时间: {date}")
        logger.info(f"📧 发件人  : {sender}")
        logger.info(f"🎯 收件人  : {receiver}")
        logger.info(f"📝 主题    : {subject}")
        
        body = ""
        
        # 判断邮件是否由多个部分组成（包含附件、HTML、纯文本等多部分）
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # 提取正文
                if content_type in ("text/plain", "text/html") and "attachment" not in content_disposition:
                    try:
                        charset = part.get_content_charset() or "utf-8"
                        part_body = part.get_payload(decode=True).decode(charset, errors="replace")
                        # 避免 HTML 覆盖 Plain 纯文本，简单拼接
                        body += part_body + "\n"
                    except Exception as e:
                        logger.warning(f"解析正文某一部分失败: {e}")
                
                # 提取并保存附件
                elif part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                    self._save_attachment(part, subject)
        else:
            # 单一结构邮件，直接提取正文
            try:
                charset = msg.get_content_charset() or "utf-8"
                body = msg.get_payload(decode=True).decode(charset, errors="replace")
            except Exception as e:
                body = f"[解析正文失败: {e}]"
                
        # 打印正文（若太长则截断打印预览）
        preview = body[:300].replace('\r', '').replace('\n', ' ') + "..." if len(body) > 300 else body.replace('\r', '').replace('\n', ' ')
        logger.info(f"📄 正文预览: {preview.strip()}")
        
    def _save_attachment(self, part, subject):
        """保存附件到本地目录"""
        filename = part.get_filename()
        if filename:
            filename = self.decode_str(filename)
            # 处理非法字符以保证文件名在 Windows/Linux 下都能安全保存
            safe_subject = "".join(c if c.isalnum() else "_" for c in subject)[:15]
            timestamp = str(int(time.time() * 100)) # 加个时间戳防止附件同名覆盖
            
            save_name = f"{safe_subject}_{timestamp}_{filename}"
            filepath = os.path.join(self.attachment_dir, save_name)
            
            try:
                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))
                # 打印出保存的绝对路径
                abs_path = os.path.abspath(filepath)
                logger.info(f"📎 [附件] 发现并保存附件: '{filename}'")
                logger.info(f"   => 保存路径: {abs_path}")
            except Exception as e:
                logger.error(f"❌ 保存附件 {filename} 失败: {e}")

if __name__ == "__main__":
    # 使用示例 (测试用)
    from datetime import timedelta
    
    # 请填入实际的参数
    SERVER = "imap.exmail.qq.com"  # 例如腾讯企业邮是 imap.exmail.qq.com，网易是 imap.163.com
    EMAIL = "your_email@example.com"
    AUTH_CODE = "your_auth_code_here" 
    
    util = EmailUtility(
        imap_server=SERVER,
        email_addr=EMAIL,
        auth_code=AUTH_CODE,
        attachment_dir="./downloaded_attachments"
    )
    
    try:
        util.connect()
        # 获取最近 3 天内的邮件
        since = datetime.now() - timedelta(days=3)
        util.fetch_emails(since_date=since)
    finally:
        util.disconnect()
