# 文档索引 📚

> 快速找到您需要的文档

---

## 📖 所有文档列表

### 🚀 快速开始
- **[快速上手指南](QUICK_START_GUIDE.md)** ⭐ 推荐新手阅读
  - 5分钟快速安装
  - 核心功能速览
  - 常用命令
  - 快速排错

### 📘 完整文档
- **[README 主文档](README.md)** ⭐ 完整项目文档
  - 项目简介
  - 核心功能详解
  - 系统架构
  - 完整使用指南
  - 常见问题解答
  - 性能优化说明

### 👨‍💻 开发者资源
- **[开发者指南](DEVELOPER_GUIDE.md)** ⭐ 二次开发必读
  - 架构设计
  - 核心模块解析
  - API文档
  - 数据库设计
  - 扩展开发示例
  - 性能优化技巧
  - 调试方法
  - 部署指南

---

## 🎯 按需求查找文档

### 我是新手，第一次使用
👉 阅读顺序：
1. [快速上手指南](QUICK_START_GUIDE.md) - 10分钟安装和运行
2. [README 使用指南部分](README.md#使用指南) - 学习基本操作
3. 开始使用系统

### 我遇到了问题
👉 查找顺序：
1. [快速上手 - 快速排错](QUICK_START_GUIDE.md#快速排错)
2. [README - 常见问题](README.md#常见问题)
3. 检查浏览器控制台（F12）
4. 提交Issue

### 我想了解性能优化
👉 阅读：
1. [README - 性能优化](README.md#性能优化)
2. [开发者指南 - 性能优化](DEVELOPER_GUIDE.md#性能优化)

### 我想扩展功能
👉 阅读：
1. [开发者指南 - 扩展开发](DEVELOPER_GUIDE.md#扩展开发)
2. [开发者指南 - 核心模块](DEVELOPER_GUIDE.md#核心模块)
3. [开发者指南 - API文档](DEVELOPER_GUIDE.md#api文档)

### 我想修改数据库
👉 阅读：
1. [开发者指南 - 数据库设计](DEVELOPER_GUIDE.md#数据库设计)
2. 查看 `init_simple_db.sql`

### 我想部署到生产环境
👉 阅读：
1. [开发者指南 - 部署指南](DEVELOPER_GUIDE.md#部署指南)

---

## 📋 文档特性对照表

| 文档 | 适合人群 | 阅读时间 | 内容深度 |
|-----|---------|---------|---------|
| 快速上手指南 | 🔰 新手用户 | 5-10分钟 | ⭐ 入门 |
| README主文档 | 👥 所有用户 | 30-60分钟 | ⭐⭐⭐ 完整 |
| 开发者指南 | 👨‍💻 开发者 | 1-2小时 | ⭐⭐⭐⭐⭐ 深入 |

---

## 🔍 快速查找

### 安装相关
- [环境要求](README.md#环境要求)
- [安装步骤](README.md#安装步骤)
- [配置说明](QUICK_START_GUIDE.md#步骤4配置数据库密码)

### 功能使用
- [化学品查询](README.md#1-化学品查询)
- [PDF法规查询](README.md#2-pdf法规查询)
- [数据爬取](README.md#3-数据爬取)
- [数据导入](README.md#4-数据导入)

### 技术架构
- [系统架构](README.md#系统架构)
- [技术栈](README.md#技术栈)
- [核心模块](DEVELOPER_GUIDE.md#核心模块)
- [数据库设计](DEVELOPER_GUIDE.md#数据库设计)

### 性能优化
- [PDF加载优化](README.md#1-pdf加载优化提升60-80)
- [PDF搜索优化](README.md#2-pdf搜索优化提升10-20倍)
- [缓存机制](README.md#缓存机制详解)
- [前端优化技巧](DEVELOPER_GUIDE.md#前端优化技巧)
- [后端优化技巧](DEVELOPER_GUIDE.md#后端优化技巧)

### 开发扩展
- [扩展开发](DEVELOPER_GUIDE.md#扩展开发)
- [API文档](DEVELOPER_GUIDE.md#api文档)
- [调试技巧](DEVELOPER_GUIDE.md#调试技巧)

### 问题解决
- [常见问题（用户版）](README.md#常见问题)
- [快速排错](QUICK_START_GUIDE.md#快速排错)
- [调试方法](DEVELOPER_GUIDE.md#调试技巧)

---

## 💡 学习路径建议

### 路径1：普通用户（使用系统）
```
快速上手指南 → 安装并运行 → 基本使用 → 遇到问题查看FAQ
```

### 路径2：管理员（部署维护）
```
README完整阅读 → 理解架构 → 配置优化 → 开发者指南（部署部分）
```

### 路径3：开发者（二次开发）
```
README快速了解 → 开发者指南详细阅读 → 核心代码分析 → 开始开发
```

---

## 📝 其他资源

### 项目文件
- `init_simple_db.sql` - 数据库初始化脚本
- `sample_data.sql` - 样例数据
- `requirements.txt` - Python依赖列表
- `app.py` - Flask后端主文件
- `templates/index.html` - 前端主页面

### 工具脚本
- `install_deps.bat` - 依赖安装脚本（Windows）
- `start_web.bat` - 启动脚本（Windows）
- `run_scraper.bat` - 爬虫脚本（Windows）
- `scrape_to_json.py` - Python爬虫程序

### 数据目录
- `msds_json/` - MSDS数据（JSON格式）
- `pdf/` - 法规PDF文档
- `uploads/` - 用户上传文件
- `msds_json/images/` - MSDS图片

---

## 🔗 外部资源

### 官方文档链接
- [Flask官方文档](https://flask.palletsprojects.com/)
- [PDF.js官方文档](https://mozilla.github.io/pdf.js/)
- [MySQL官方文档](https://dev.mysql.com/doc/)
- [Python官方文档](https://docs.python.org/zh-cn/3/)

### 教程资源
- [Flask入门教程](https://tutorial.helloflask.com/)
- [MySQL教程](https://www.runoob.com/mysql/mysql-tutorial.html)
- [JavaScript教程](https://zh.javascript.info/)

---

## 📞 获取帮助

### 问题反馈流程
1. 📖 查看相关文档
2. 🔍 搜索已有的Issue
3. 🐛 如果是新问题，提交Issue
4. 💬 提供详细的错误信息和复现步骤

### Issue模板

**Bug报告**：
```markdown
**描述问题**
简短描述问题

**复现步骤**
1. 打开...
2. 点击...
3. 看到错误...

**预期行为**
应该...

**实际行为**
但是...

**环境信息**
- 操作系统：Windows 10
- Python版本：3.9
- MySQL版本：8.0
- 浏览器：Chrome 110

**截图**
如果可能，附上截图

**错误日志**
粘贴相关的错误日志
```

**功能请求**：
```markdown
**功能描述**
希望添加...功能

**使用场景**
这个功能可以用于...

**建议的实现方式**
可以通过...实现

**替代方案**
或者...
```

---

## ✅ 文档维护

### 文档版本
- 创建日期：2025-10-16
- 最后更新：2025-10-16
- 文档版本：v2.0.0

### 文档状态
- ✅ README.md - 完整
- ✅ QUICK_START_GUIDE.md - 完整
- ✅ DEVELOPER_GUIDE.md - 完整
- ✅ DOCUMENTATION_INDEX.md - 完整

---

## 🙏 文档反馈

如果您发现：
- 📝 文档有错误或不清楚的地方
- 💡 有改进建议
- ❓ 缺少某些说明

欢迎提交Issue或Pull Request！

---

**祝您使用愉快！** 🎉

