---
name: email-sender
description: 接收来自白名单发件人的邮件，并可向任意邮箱发送邮件（标题、正文必填，附件可选）
---
此技能提供了一个基于FastAPI的邮件服务。首选使用远程服务器 http://dimond.top:5030 进行收发邮件（推荐），因为本地默认没有配置 EMAIL_SENDER/EMAIL_PASSWORD 环境变量。本地运行（python app.py, http://localhost:5030）仅在你已正确配置环境变量时使用。

API接口：
默认服务器基址：http://dimond.top:5030
1. GET / - 获取API信息
2. GET /emails/?limit=10&days=7 - 获取来自白名单发件人的邮件（仅返回包含标题与正文的邮件，附件列表可选返回）
3. POST /send-email/ - 向任意邮箱发送邮件（subject、body 必填；attachments 可选为文件路径数组，需为服务器可读路径）
4. GET /allowed-senders/ - 获取允许的发件人列表

请求/响应示例：

- 读取邮件

  请求
  GET http://dimond.top:5030/emails?limit=10&days=7

  响应（示例）
  [
    {
      "id": "123",
      "subject": "示例标题",
      "sender": "939342547@qq.com",
      "date": "Wed, 10 Mar 2026 12:34:56 +0800",
      "body": "正文内容或预览",
      "attachments": ["附件1.pdf", "图片.png"]
    }
  ]

- 发送邮件

  请求
  POST http://dimond.top:5030/send-email
  Content-Type: application/json
  {
    "to": "someone@example.com",
    "subject": "测试标题",
    "body": "测试正文",
    "attachments": ["/absolute/path/to/file1.pdf"]
  }

  说明
  - subject、body 为必填项；attachments 为可选项（字符串数组）
  - attachments 为服务器上可访问的文件绝对路径（远程优先）。若需直接上传本地文件，建议后续扩展 multipart 表单（当前未实现）。

也可以通过命令行方式使用：
python email_sender.py [title] [content] [path_to_attachment]

python email_receiver.py [limit] [days]
其中 limit 是获取邮件的最大数量（默认10），days 是获取最近几天的邮件（默认7天）
仅显示来自以下邮箱的邮件：939342547@qq.com, 1119623207@qq.com, jiangjimjim@gmail.com
