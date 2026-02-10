---
name: email-sender
description: 接收来自 939342547@qq.com, 1119623207@qq.com, jiangjimjim@gmail.com 的邮件，以及发送邮件到这些邮箱
---
此技能提供了一个基于FastAPI的邮件服务，运行在服务器5030端口（http://dimond.top:5030），和本地5030端口（python app.py 运行在 http://localhost:5030）

API接口：
1. GET / - 获取API信息
2. GET /emails/?limit=10&days=7 - 获取来自白名单发件人的邮件
3. POST /send-email/ - 发送邮件到指定邮箱（必须在白名单内）
4. GET /allowed-senders/ - 获取允许的发件人列表

也可以通过命令行方式使用：
python email_sender.py [title] [content] [path_to_attachment]

python email_receiver.py [limit] [days]
其中 limit 是获取邮件的最大数量（默认10），days 是获取最近几天的邮件（默认7天）
仅显示来自以下邮箱的邮件：939342547@qq.com, 1119623207@qq.com, jiangjimjim@gmail.com