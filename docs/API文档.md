# SonjayOS API文档

## 概述

SonjayOS提供了一套完整的RESTful API，用于与AI服务、用户界面、安全系统等核心组件进行交互。本文档详细描述了所有可用的API端点、请求格式和响应格式。

## 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 通用响应格式

所有API响应都遵循以下格式：

```json
{
    "success": true,
    "data": {},
    "message": "操作成功",
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "uuid-string"
}
```

错误响应格式：

```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": {}
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "uuid-string"
}
```

## AI服务API

### 1. 文本生成

**端点**: `POST /ai/generate`

**描述**: 使用Llama 3.1模型生成文本响应

**请求体**:
```json
{
    "prompt": "你好，请介绍一下SonjayOS操作系统",
    "max_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.9,
    "stream": false
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "response": "SonjayOS是一个基于Ubuntu 24.04 LTS的AI集成操作系统...",
        "tokens_used": 150,
        "inference_time": 2.5,
        "model_used": "llama3.1:8b"
    }
}
```

### 2. 语音识别

**端点**: `POST /ai/speech/recognize`

**描述**: 使用Whisper模型进行语音识别

**请求体**:
```json
{
    "audio_data": "base64-encoded-audio",
    "language": "zh",
    "model_size": "base"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "text": "识别出的文本内容",
        "confidence": 0.95,
        "language": "zh",
        "processing_time": 1.2
    }
}
```

### 3. 语义搜索

**端点**: `POST /ai/search/semantic`

**描述**: 使用嵌入模型进行语义搜索

**请求体**:
```json
{
    "query": "关于人工智能的文档",
    "limit": 10,
    "min_similarity": 0.3
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "results": [
            {
                "file_path": "/home/user/documents/ai_research.md",
                "similarity_score": 0.85,
                "content_snippet": "人工智能技术正在快速发展...",
                "file_type": ".md",
                "last_modified": 1704067200
            }
        ],
        "total_results": 1,
        "search_time": 0.5
    }
}
```

## 用户界面API

### 1. 主题管理

**端点**: `GET /ui/themes`

**描述**: 获取可用主题列表

**响应**:
```json
{
    "success": true,
    "data": {
        "themes": [
            {
                "name": "light_work",
                "display_name": "浅色工作主题",
                "background": "#FFFFFF",
                "accent_color": "#2196F3",
                "text_color": "#212121"
            }
        ],
        "current_theme": "light_work"
    }
}
```

**端点**: `POST /ui/themes/switch`

**描述**: 切换主题

**请求体**:
```json
{
    "theme_name": "dark_work"
}
```

### 2. 桌面小部件

**端点**: `GET /ui/widgets`

**描述**: 获取桌面小部件状态

**响应**:
```json
{
    "success": true,
    "data": {
        "ai_assistant": {
            "enabled": true,
            "status": "listening",
            "last_activity": "2024-01-01T00:00:00Z"
        },
        "system_monitor": {
            "enabled": true,
            "cpu_usage": 45.2,
            "memory_usage": 67.8
        }
    }
}
```

## 安全系统API

### 1. 威胁检测

**端点**: `GET /security/threats`

**描述**: 获取安全威胁信息

**响应**:
```json
{
    "success": true,
    "data": {
        "total_events": 15,
        "threats_detected": 3,
        "recent_events": [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "event_type": "cpu_anomaly",
                "severity": "medium",
                "description": "CPU使用率异常高",
                "risk_score": 0.7
            }
        ]
    }
}
```

### 2. 安全报告

**端点**: `GET /security/report`

**描述**: 获取安全报告

**查询参数**:
- `hours`: 报告时间范围（小时）

**响应**:
```json
{
    "success": true,
    "data": {
        "time_range_hours": 24,
        "total_events": 25,
        "threat_type_distribution": {
            "cpu_anomaly": 5,
            "memory_anomaly": 3,
            "network_anomaly": 2
        },
        "severity_distribution": {
            "low": 10,
            "medium": 8,
            "high": 5,
            "critical": 2
        },
        "average_risk_score": 0.45
    }
}
```

## 系统管理API

### 1. 系统状态

**端点**: `GET /system/status`

**描述**: 获取系统状态信息

**响应**:
```json
{
    "success": true,
    "data": {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "disk_usage": 23.5,
        "network_usage": 12.3,
        "uptime": 86400,
        "services": {
            "ai_service": "running",
            "ui_service": "running",
            "security_service": "running"
        }
    }
}
```

### 2. 性能优化

**端点**: `POST /system/optimize`

**描述**: 执行系统优化

**请求体**:
```json
{
    "optimization_type": "full",
    "include_cache_cleanup": true,
    "include_memory_optimization": true
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "optimization_completed": true,
        "improvements": {
            "cpu_usage_reduction": 15.2,
            "memory_usage_reduction": 8.7,
            "disk_space_freed": "2.3GB"
        },
        "duration": 45.2
    }
}
```

## 开发工具API

### 1. 代码补全

**端点**: `POST /dev/code-completion`

**描述**: 获取代码补全建议

**请求体**:
```json
{
    "file_path": "/home/user/project/main.py",
    "language": "python",
    "content": "def hello_world():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    hello_world()",
    "cursor_line": 5,
    "cursor_column": 8
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "completions": [
            {
                "text": "print(",
                "start_line": 5,
                "end_line": 5,
                "start_column": 8,
                "end_column": 8,
                "confidence": 0.8,
                "completion_type": "function",
                "description": "打印函数"
            }
        ],
        "total_suggestions": 5
    }
}
```

### 2. 代码分析

**端点**: `POST /dev/code-analysis`

**描述**: 分析代码质量

**请求体**:
```json
{
    "file_path": "/home/user/project/main.py",
    "language": "python",
    "content": "def hello_world():\n    print('Hello, World!')"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "quality_score": 0.85,
        "issues": [
            {
                "type": "style",
                "severity": "low",
                "message": "函数名应使用snake_case",
                "line": 1,
                "column": 1
            }
        ],
        "suggestions": [
            {
                "type": "optimization",
                "message": "可以考虑添加类型注解",
                "line": 1
            }
        ]
    }
}
```

## WebSocket连接

### 实时通信

**端点**: `ws://localhost:8001/ws`

**描述**: WebSocket连接用于实时通信

**连接示例**:
```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onopen = function() {
    console.log('WebSocket连接已建立');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};

ws.onclose = function() {
    console.log('WebSocket连接已关闭');
};
```

**消息格式**:
```json
{
    "type": "ai_response",
    "data": {
        "response": "AI生成的响应",
        "timestamp": "2024-01-01T00:00:00Z"
    }
}
```

## 错误代码

| 代码 | 描述 |
|------|------|
| 400 | 请求参数错误 |
| 401 | 未授权访问 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 429 | 请求频率过高 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

## 认证

### 获取访问令牌

**端点**: `POST /auth/login`

**请求体**:
```json
{
    "username": "sonjayos",
    "password": "password"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "access_token": "jwt-token",
        "token_type": "Bearer",
        "expires_in": 3600
    }
}
```

### 使用令牌

在请求头中添加：
```
Authorization: Bearer your-jwt-token
```

## 速率限制

- **AI服务**: 每分钟60次请求
- **语音识别**: 每分钟30次请求
- **语义搜索**: 每分钟100次请求
- **系统管理**: 每分钟20次请求

## 示例代码

### Python示例

```python
import requests
import json

# 基础配置
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your-token"
}

# AI文本生成
def generate_text(prompt):
    response = requests.post(
        f"{BASE_URL}/ai/generate",
        headers=HEADERS,
        json={
            "prompt": prompt,
            "max_tokens": 512,
            "temperature": 0.7
        }
    )
    return response.json()

# 语义搜索
def semantic_search(query):
    response = requests.post(
        f"{BASE_URL}/ai/search/semantic",
        headers=HEADERS,
        json={
            "query": query,
            "limit": 10
        }
    )
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 生成文本
    result = generate_text("请介绍一下SonjayOS")
    print(result["data"]["response"])
    
    # 语义搜索
    search_result = semantic_search("人工智能文档")
    print(f"找到 {len(search_result['data']['results'])} 个结果")
```

### JavaScript示例

```javascript
// 基础配置
const BASE_URL = 'http://localhost:8000/api/v1';
const headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-token'
};

// AI文本生成
async function generateText(prompt) {
    const response = await fetch(`${BASE_URL}/ai/generate`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            prompt: prompt,
            max_tokens: 512,
            temperature: 0.7
        })
    });
    return await response.json();
}

// 语义搜索
async function semanticSearch(query) {
    const response = await fetch(`${BASE_URL}/ai/search/semantic`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            query: query,
            limit: 10
        })
    });
    return await response.json();
}

// 使用示例
async function main() {
    try {
        // 生成文本
        const result = await generateText('请介绍一下SonjayOS');
        console.log(result.data.response);
        
        // 语义搜索
        const searchResult = await semanticSearch('人工智能文档');
        console.log(`找到 ${searchResult.data.results.length} 个结果`);
    } catch (error) {
        console.error('请求失败:', error);
    }
}

main();
```

## 更新日志

### v1.0.0 (2024-01-01)
- 初始API版本发布
- 支持AI文本生成、语音识别、语义搜索
- 支持主题管理和桌面小部件
- 支持安全威胁检测和系统优化
- 支持代码补全和代码分析

## 支持

如有问题或建议，请联系：
- 邮箱: support@sonjayos.com
- 文档: https://docs.sonjayos.com
- 社区: https://community.sonjayos.com
