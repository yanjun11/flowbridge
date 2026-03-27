# FlowBridge

国内版 Zapier - 自动化工作流平台

## 功能特性

- 🔗 飞书多维表格触发器
- 📢 飞书机器人通知 + 企业微信群通知
- 🌐 HTTP 请求动作（调用任意后端 API）
- 🔄 可扩展的插件架构
- 📊 完整的执行记录追踪
- 🔒 Webhook 签名验证（HMAC-SHA256 + 时间戳防重放）
- 🛡️ 安全防护（SSRF 防护、模板注入防护、事件去重）
- ♻️ 自动重试机制（3 次重试 + 指数退避）
- ⚡ 异步执行引擎（30s 超时控制）

## 技术栈

- FastAPI - 异步 Web 框架
- Tortoise ORM - 异步 ORM
- PostgreSQL - 数据库
- Redis - 缓存和分布式锁
- lark-oapi - 飞书 SDK

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
DATABASE_URL=postgres://user:password@localhost:5432/flowbridge
REDIS_URL=redis://localhost:6379/0
FEISHU_WEBHOOK_SECRET=your_feishu_secret
```

### 3. 初始化数据库

```bash
aerich init -t src.conf.TORTOISE_ORM
aerich init-db
```

### 4. 启动服务

```bash
python main.py
```

访问 http://localhost:8000/docs 查看 API 文档

## API 使用示例

### 示例 1: 飞书表格 → 飞书群通知

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "飞书表格新增通知",
    "trigger_type": "feishu_bitable",
    "trigger_config": {
      "app_id": "cli_xxx",
      "app_secret": "xxx"
    },
    "actions": [
      {
        "type": "feishu_notify",
        "config": {
          "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
          "message": "新增记录：{{trigger.record_name}}",
          "msg_type": "text"
        }
      }
    ]
  }'
```

### 示例 2: 飞书表格 → 企微群通知

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "飞书表格同步到企微",
    "trigger_type": "feishu_bitable",
    "trigger_config": {
      "app_id": "cli_xxx",
      "app_secret": "xxx"
    },
    "actions": [
      {
        "type": "wecom_notify",
        "config": {
          "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
          "message": "新增记录：{{trigger.name}}"
        }
      }
    ]
  }'
```

### 示例 3: 飞书表格 → 调用后端 API

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "飞书表格触发补偿",
    "trigger_type": "feishu_bitable",
    "trigger_config": {
      "app_id": "cli_xxx",
      "app_secret": "xxx"
    },
    "actions": [
      {
        "type": "http_request",
        "config": {
          "url": "http://admin-backend/api/compensate",
          "method": "POST",
          "headers": {
            "Authorization": "Bearer {{env.API_TOKEN}}"
          },
          "body": {
            "user_id": "{{trigger.user_id}}",
            "amount": "{{trigger.amount}}"
          },
          "allow_internal": true
        }
      }
    ]
  }'
```

### 配置飞书 Webhook

在飞书多维表格中配置 Webhook URL：
```
http://your-domain/api/webhooks/feishu/bitable
```

## 项目结构

```
flowbridge/
├── src/
│   ├── api/              # API 路由
│   │   ├── webhook.py    # Webhook 接收端点
│   │   ├── workflow.py   # 工作流 CRUD
│   │   └── execution.py  # 执行记录查询
│   ├── service/          # 业务逻辑
│   │   ├── executor.py   # 工作流执行引擎
│   │   ├── plugin_manager.py  # 插件管理器
│   │   ├── template.py   # 模板渲染
│   │   └── cache.py      # Redis 缓存
│   ├── plugins/          # 触发器和动作插件
│   │   ├── base.py       # 插件基类
│   │   ├── trigger/      # 触发器插件
│   │   └── action/       # 动作插件
│   ├── dao/              # 数据访问层
│   │   └── orm/model/    # ORM 模型
│   ├── schema/           # Pydantic 模型
│   └── conf/             # 配置管理
├── docs/                 # 技术文档
│   ├── 技术预研文档.md
│   └── 技术设计文档.md
├── main.py               # 应用入口
└── pyproject.toml        # 项目配置
```

## 开发状态

**MVP v0.1.0** - 核心功能已完成

- ✅ 数据模型与 ORM
- ✅ 插件系统架构
- ✅ 飞书多维表格触发器
- ✅ 企微通知动作
- ✅ 工作流执行引擎
- ✅ API 端点（webhook + CRUD）
- ✅ 安全加固（签名验证、SSRF 防护、事件去重）

**待完成：**
- ⏳ API 身份认证
- ⏳ 更多触发器（飞书审批、日历）
- ⏳ 更多动作（飞书消息、文档更新）
- ⏳ Web UI 管理界面
- ⏳ 单元测试覆盖
