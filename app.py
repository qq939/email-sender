from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import os
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import smtplib
import dotenv
from datetime import datetime, timedelta
import re

# 加载环境变量
dotenv.load_dotenv()
dotenv.load_dotenv("asset/.env")

# 全局参数
# 允许接收邮件的发件人白名单
ALLOWED_SENDERS = [
    "939342547@qq.com",
    "1119623207@qq.com", 
    "jiangjimjim@gmail.com"
]

# 邮箱账户配置
EMAIL_ACCOUNT = os.getenv("EMAIL_SENDER", "939342547@qq.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
IMAP_SERVER = "imap.qq.com"
IMAP_PORT = 993

# Pydantic模型定义
class EmailItem(BaseModel):
    id: str
    subject: str
    sender: str
    date: Optional[str] = None
    body: str

class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str

class SendEmailResponse(BaseModel):
    success: bool
    message: str

# 初始化FastAPI应用
app = FastAPI(
    title="Email Service API",
    description="API for receiving emails from allowed senders and sending emails",
    version="1.0.0"
)

def get_emails_from_allowed_senders(
    limit: int = 10,
    days: int = 7
) -> List[EmailItem]:
    """
    从允许的发件人接收邮件
    """
    if not EMAIL_ACCOUNT or not EMAIL_PASSWORD:
        print("Error: EMAIL_SENDER or EMAIL_PASSWORD environment variables not set.")
        return []
    
    try:
        # 连接到邮箱服务器
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        
        # 选择收件箱
        mail.select('inbox')
        
        # 搜索最近的邮件
        since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        typ, data = mail.search(None, f'SINCE {since_date}')
        
        email_ids = data[0].split()
        # 限制邮件数量
        email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        
        emails = []
        
        for email_id in reversed(email_ids):  # 最新的邮件在前
            typ, msg_data = mail.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # 解码邮件主题
            subject = decode_header(msg['Subject'])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            
            # 获取发件人
            sender = msg['From']
            # 提取邮箱地址
            sender_addr_match = re.search(r'<(.*)>', sender)
            if sender_addr_match:
                sender_addr = sender_addr_match.group(1)
            else:
                sender_addr = sender.strip('"')
            
            # 检查发件人是否在白名单中
            if sender_addr in ALLOWED_SENDERS:
                # 获取邮件正文
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                
                email_info = EmailItem(
                    id=email_id.decode(),
                    subject=subject,
                    sender=sender_addr,
                    date=msg['Date'],
                    body=body[:500] + "..." if len(body) > 500 else body  # 限制长度
                )
                emails.append(email_info)
        
        mail.close()
        mail.logout()
        
        return emails
        
    except Exception as e:
        print(f"Failed to retrieve emails: {e}")
        return []

def send_email(to_email: str, subject: str, body: str) -> dict:
    """
    发送邮件的函数
    """
    # 验证收件人邮箱是否在白名单中
    if to_email not in ALLOWED_SENDERS:
        return {
            "success": False,
            "message": f"Email recipient '{to_email}' is not in the allowed list."
        }
    
    # 获取配置
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        return {
            "success": False,
            "message": "EMAIL_SENDER or EMAIL_PASSWORD environment variables not set."
        }
    
    try:
        # 构建邮件
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = formataddr(("OpenClaw Email Service", sender_email))
        msg["To"] = to_email
        
        # 添加正文
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        # 发送邮件
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return {
            "success": True,
            "message": f"Email sent successfully to {to_email}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to send email: {str(e)}"
        }

@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "Welcome to Email Service API",
        "description": "API for receiving emails from allowed senders and sending emails",
        "allowed_senders": ALLOWED_SENDERS
    }

@app.get("/emails/", response_model=List[EmailItem])
async def get_emails(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of emails to retrieve"),
    days: int = Query(7, ge=1, le=30, description="Number of recent days to check")
):
    """
    获取来自白名单发件人的邮件
    """
    emails = get_emails_from_allowed_senders(limit=limit, days=days)
    return emails

@app.post("/send-email/", response_model=SendEmailResponse)
async def send_email_endpoint(request: SendEmailRequest):
    """
    发送邮件到指定邮箱（必须在白名单内）
    """
    result = send_email(request.to, request.subject, request.body)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return SendEmailResponse(success=True, message=result["message"])

@app.get("/allowed-senders/")
async def get_allowed_senders():
    """
    获取允许的发件人列表
    """
    return {"allowed_senders": ALLOWED_SENDERS}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5030)