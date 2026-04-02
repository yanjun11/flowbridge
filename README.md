# FlowBridge

国内版 Zapier - 自动化工作流平台

## 功能特性

- ✅ 飞书审批触发器（审批通过自动触发工作流）`[PRIMARY]`
- 🔗 飞书多维表格触发器
- 📢 飞书机器人通知（`text` / `rich_text` / `interactive card`）
- 📨 企业微信群通知
- 🌐 HTTP 请求动作（调用任意后端 API）
- 🔌 可扩展的插件架构
- 📊 完整的执行记录追踪
- 🔒 Webhook 签名验证 + 事件去重
- 🛡️ SSRF 防护 + 模板注入防护
- 🔑 API Key 认证（`X-API-Key`）
- ♻️ 自动重试 + 异步执行

## 使用场景

### 场景 1（主场景）: 飞书审批通过 → 调用补偿 API → 飞书群 + 企微群通知

员工审批通过后，自动触发补偿接口，然后在飞书群和企微群同步通知处理结果。

### 场景 2: 飞书多维表格新增记录 → 多渠道通知

运营在多维表格新增记录后，自动推送到飞书机器人和企微机器人，减少人工同步。

### 场景 3: 飞书审批通过 → HTTP 请求 → 飞书卡片消息通知

审批通过后调用后端服务处理业务，再发送飞书 `interactive card` 消息回传处理结果。

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
API_KEY=your_api_key
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

### 示例 1: 飞书审批 → 调用后端 API + 飞书通知（主场景）

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "name": "审批通过后自动补偿并通知",
    "trigger_type": "feishu_approval",
    "trigger_config": {
      "approval_code": "B7C9A3F1"
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
            "approval_code": "{{trigger.approval_code}}",
            "instance_code": "{{trigger.instance_code}}",
            "applicant_open_id": "{{trigger.applicant_open_id}}"
          },
          "allow_internal": true
        }
      },
      {
        "type": "feishu_notify",
        "config": {
          "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
          "msg_type": "text",
          "message": "审批 {{trigger.instance_code}} 已通过，补偿流程已触发。"
        }
      }
    ]
  }'
```

### 示例 2: 飞书审批 → 飞书 + 企微双渠道通知

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "name": "审批通过双渠道通知",
    "trigger_type": "feishu_approval",
    "trigger_config": {
      "approval_code": "B7C9A3F1"
    },
    "actions": [
      {
        "type": "feishu_notify",
        "config": {
          "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
          "msg_type": "rich_text",
          "message": "审批通过：{{trigger.instance_code}}，申请人：{{trigger.applicant_open_id}}"
        }
      },
      {
        "type": "wecom_notify",
        "config": {
          "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
          "message": "审批通过：{{trigger.instance_code}}，已同步处理。"
        }
      }
    ]
  }'
```

### 示例 3: 飞书多维表格 → HTTP 请求

```bash
curl -X POST http://localhost:8000/api/workflows \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "name": "多维表格新增记录触发后端 API",
    "trigger_type": "feishu_bitable",
    "trigger_config": {
      "app_id": "cli_xxx",
      "app_secret": "xxx"
    },
    "actions": [
      {
        "type": "http_request",
        "config": {
          "url": "https://api.your-domain.com/sync/bitable",
          "method": "POST",
          "headers": {
            "Authorization": "Bearer {{env.API_TOKEN}}"
          },
          "body": {
            "record_id": "{{trigger.record_id}}",
            "operator": "{{trigger.operator_id}}"
          }
        }
      }
    ]
  }'
```

## Webhook 配置

在飞书开放平台中配置事件订阅回调地址：

- 审批事件回调：`POST /api/webhooks/feishu/approval`
- 多维表格回调：`POST /api/webhooks/feishu/bitable`

示例完整地址：

```text
https://your-domain/api/webhooks/feishu/approval
https://your-domain/api/webhooks/feishu/bitable
```

## 项目结构

```text
flowbridge/
├── src/
│   ├── api/                          # API 路由
│   │   ├── webhook.py                # Webhook 接收端点
│   │   ├── workflow.py               # 工作流 CRUD
│   │   └── execution.py              # 执行记录查询
│   ├── service/                      # 业务逻辑
│   │   ├── executor.py               # 工作流执行引擎
│   │   ├── plugin_manager.py         # 插件管理器
│   │   ├── template.py               # 模板渲染
│   │   └── cache.py                  # Redis 缓存
│   ├── plugins/                      # 触发器和动作插件
│   │   ├── base.py                   # 插件基类
│   │   ├── trigger/                  # 触发器插件
│   │   │   ├── feishu_approval.py    # 飞书审批触发器
│   │   │   └── feishu_bitable.py     # 飞书多维表格触发器
│   │   └── action/                   # 动作插件
│   ├── dao/                          # 数据访问层
│   │   └── orm/model/                # ORM 模型
│   ├── schema/                       # Pydantic 模型
│   └── conf/                         # 配置管理
├── docs/                             # 技术文档
│   ├── 技术预研文档.md
│   └── 技术设计文档.md
├── main.py                           # 应用入口
└── pyproject.toml                    # 项目配置
```

## 开发状态

**MVP v0.1.0** - 审批自动化主流程可用

已完成：

- ✅ 数据模型与 ORM
- ✅ 插件系统架构
- ✅ 飞书审批触发器（审批通过自动执行工作流）
- ✅ 飞书多维表格触发器
- ✅ 飞书机器人通知（text/rich_text/interactive）
- ✅ 企微群通知动作
- ✅ HTTP 请求动作
- ✅ 工作流执行引擎
- ✅ API 端点（webhook + CRUD + 执行记录查询）
- ✅ API 身份认证（X-API-Key）
- ✅ 安全加固（签名验证、SSRF 防护、事件去重）
- ✅ 单元测试覆盖

待完成：

- ⏳ 定时任务触发器（Cron）
- ⏳ 更多动作（钉钉通知、邮件发送）
- ⏳ Web UI 管理界面
- ⏳ Dockerfile + K8s 部署配置
