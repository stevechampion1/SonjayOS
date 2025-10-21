# SonjayOS 贡献指南

感谢您对SonjayOS项目的关注！本指南将帮助您了解如何为项目做出贡献。

## 贡献方式

### 1. 报告问题
- 使用GitHub Issues报告bug
- 提供详细的复现步骤
- 包含系统信息和错误日志

### 2. 功能建议
- 使用GitHub Discussions提出新功能建议
- 详细描述功能需求和预期效果
- 讨论实现方案和技术细节

### 3. 代码贡献
- Fork项目仓库
- 创建功能分支
- 提交代码更改
- 创建Pull Request

## 开发环境设置

### 系统要求
- Ubuntu 24.04 LTS (推荐)
- Python 3.11+
- Node.js 18+
- 32GB RAM (推荐)
- 500GB存储空间

### 快速开始

1. **克隆项目**
   ```bash
   git clone https://github.com/sonjayos/sonjayos.git
   cd sonjayos
   ```

2. **设置开发环境**
   ```bash
   # 使用Makefile
   make dev-setup
   
   # 或手动设置
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   npm install
   ```

3. **启动开发模式**
   ```bash
   make dev
   ```

## 代码规范

### Python代码规范
- 遵循PEP 8
- 使用Black进行代码格式化
- 使用isort进行导入排序
- 使用flake8进行代码检查
- 使用mypy进行类型检查

### JavaScript代码规范
- 遵循ESLint规则
- 使用Prettier进行代码格式化
- 使用JSDoc进行文档注释

### 提交信息规范
使用语义化提交信息：
- `feat:` 新功能
- `fix:` 修复bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

## 开发流程

### 1. 创建分支
```bash
git checkout -b feature/your-feature-name
```

### 2. 开发功能
- 编写代码
- 添加测试
- 更新文档

### 3. 代码检查
```bash
# 格式化代码
make format

# 检查代码
make lint

# 运行测试
make test
```

### 4. 提交代码
```bash
git add .
git commit -m "feat: 添加新功能"
git push origin feature/your-feature-name
```

### 5. 创建Pull Request
- 填写PR模板
- 描述更改内容
- 关联相关Issue
- 请求代码审查

## 测试指南

### 单元测试
```bash
# 运行Python测试
pytest src/tests/ -v

# 运行JavaScript测试
npm test
```

### 集成测试
```bash
# 启动开发环境
make dev

# 测试API接口
curl http://localhost:8000/api/v1/system/status
```

### 性能测试
```bash
# 运行性能分析
make perf
```

## 文档贡献

### 文档类型
- 用户手册
- 开发文档
- API文档
- 安装指南

### 文档规范
- 使用Markdown格式
- 包含代码示例
- 提供截图和图表
- 保持文档更新

## 发布流程

### 版本号规范
使用语义化版本号：
- `MAJOR.MINOR.PATCH`
- 主版本号：不兼容的API修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

### 发布步骤
1. 更新版本号
2. 更新CHANGELOG.md
3. 创建Release标签
4. 构建发布包
5. 发布到GitHub

## 社区准则

### 行为准则
- 尊重他人
- 建设性讨论
- 包容性环境
- 专业态度

### 沟通渠道
- GitHub Issues: 问题报告
- GitHub Discussions: 功能讨论
- 邮件列表: 重要通知
- 文档网站: 使用指南

## 许可证

本项目采用MIT许可证。贡献的代码将遵循相同的许可证。

## 联系方式

- 项目主页: https://github.com/sonjayos/sonjayos
- 问题反馈: https://github.com/sonjayos/sonjayos/issues
- 功能讨论: https://github.com/sonjayos/sonjayos/discussions
- 邮件联系: team@sonjayos.com

## 致谢

感谢所有为SonjayOS项目做出贡献的开发者！

---

**让我们一起构建更好的AI操作系统！** 🚀
