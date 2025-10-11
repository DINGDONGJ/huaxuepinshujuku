# 危化品数据库 Web应用使用指南

> **版本**: 1.0  
> **创建日期**: 2025-10-09  
> **技术栈**: Python Flask + MySQL + HTML/CSS/JavaScript

---

## 📋 目录

- [快速开始](#-快速开始)
- [功能说明](#-功能说明)
- [安装步骤](#-安装步骤)
- [配置说明](#-配置说明)
- [使用指南](#-使用指南)
- [API接口](#-api接口)
- [故障排查](#-故障排查)

---

## 🚀 快速开始

### 1. 安装Python依赖

```powershell
# 安装Flask和PyMySQL
pip install Flask==3.0.0 PyMySQL==1.1.0

# 或使用requirements.txt
pip install -r requirements.txt
```

### 2. 配置数据库连接

编辑 `app.py` 文件，修改数据库配置：

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '你的MySQL密码',  # ⚠️ 修改这里
    'database': '危化品数据库',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
```

### 3. 启动应用

```powershell
python app.py
```

**成功启动后会看到**：
```
============================================================
🚀 危化品数据库 Web应用启动中...
============================================================
📍 访问地址: http://localhost:5000
💡 提示: 请确保已在 app.py 中配置正确的数据库密码
============================================================
```

### 4. 访问应用

在浏览器中打开：**http://localhost:5000**

---

## 🎯 功能说明

### 主要功能

| 功能 | 说明 | 使用方式 |
|------|------|---------|
| **完整查询** | 一次性查询化学品的所有信息（8个类别） | 输入名称 → 点击"完整查询" |
| **引导查询** | 显示四类别按钮，点击查询特定类别 | 输入名称 → 点击"引导查询" → 点击类别按钮 |
| **支持CAS号** | 可以使用CAS号查询 | 输入CAS号（如50-00-0） |
| **美观UI** | 现代化渐变设计，响应式布局 | - |

### 查询类别

1. **📜 管理要求** - 法律法规条款、文档链接
2. **⚠️ 使用要求** - 安全操作规程（SOP）
3. **🔶 识别与许可** - GHS分类、运输分类、目录标识
4. **🚨 应急措施** - 急救、消防、泄漏处理

---

## 📦 安装步骤

### 步骤1: 检查环境

```powershell
# 检查Python版本（需要3.7+）
python --version

# 检查pip
pip --version

# 检查MySQL服务
mysql --version
```

### 步骤2: 安装依赖

```powershell
# 进入项目目录
cd C:\Users\Administrator.DESKTOP-URBQKM0\Desktop\huaxuepinshujuku

# 安装Python包
pip install -r requirements.txt
```

### 步骤3: 确保数据库已初始化

```sql
-- 在MySQL中验证
mysql -u root -p

USE 危化品数据库;

-- 查看表
SHOW TABLES;

-- 查看存储过程
SHOW PROCEDURE STATUS WHERE Db = '危化品数据库';

-- 应该有3个存储过程：
-- 获取化学品完整信息
-- 获取引导词
-- 按类别查询
```

### 步骤4: 修改配置

编辑 `app.py`：

```python
DB_CONFIG = {
    'host': 'localhost',        # MySQL服务器地址
    'user': 'root',             # 用户名
    'password': '你的密码',      # ⚠️ 修改这里
    'database': '危化品数据库',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
```

### 步骤5: 启动应用

```powershell
python app.py
```

---

## ⚙️ 配置说明

### 数据库配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `host` | MySQL服务器地址 | `localhost` |
| `user` | 数据库用户名 | `root` |
| `password` | 数据库密码 | ⚠️ **必须修改** |
| `database` | 数据库名 | `危化品数据库` |
| `charset` | 字符集 | `utf8mb4` |

### 应用配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `debug` | 调试模式 | `True` |
| `host` | 监听地址 | `0.0.0.0` |
| `port` | 监听端口 | `5000` |

**生产环境建议**：
```python
app.run(debug=False, host='127.0.0.1', port=5000)
```

---

## 📖 使用指南

### 1. 完整查询模式

**步骤**：
1. 在搜索框输入化学品名称（如"甲醛"）或CAS号（如"50-00-0"）
2. 点击 **"🔍 完整查询"** 按钮
3. 查看8个结果集：
   - 基本信息
   - 管理要求
   - 使用要求
   - GHS分类
   - 运输分类
   - 目录标识
   - 应急措施
   - 别名信息

**示例**：
```
输入: 甲醛
输出: 
- CAS号: 50-00-0
- 中文名: 甲醛
- 法规条款: 3条
- 操作规程: 2条
- 应急措施: 3条
...
```

### 2. 引导查询模式

**步骤**：
1. 在搜索框输入化学品名称
2. 点击 **"📋 引导查询"** 按钮
3. 显示4个类别按钮，每个显示数据条数
4. 点击任意类别按钮查看该类别的详细信息

**示例**：
```
输入: 甲醛
显示按钮:
[管理要求 - 查看法律法规要求 (3条)]
[使用要求 - 查看安全操作规程 (2条)]
[识别与许可 - 查看GHS分类、运输许可 (3条)]
[应急措施 - 查看应急预案和处置措施 (3条)]
```

### 3. 支持的输入格式

| 输入类型 | 示例 | 说明 |
|---------|------|------|
| 中文名 | `甲醛` | 化学品中文名称 |
| 英文名 | `Formaldehyde` | 需要数据库中有匹配 |
| CAS号 | `50-00-0` | 精确匹配 |
| CAS号（无连字符） | `50000` | 需要修改存储过程支持 |

---

## 🔌 API接口

### 1. 完整查询接口

**请求**：
```http
POST /api/search
Content-Type: application/json

{
  "name": "甲醛"
}
```

**响应**：
```json
{
  "basic_info": {
    "CAS号": "50-00-0",
    "中文名": "甲醛",
    "英文名": "Formaldehyde",
    "分子式": "CH2O",
    "EC编号": "200-001-8"
  },
  "management": [...],
  "sop": [...],
  "ghs": [...],
  "transport": [...],
  "catalog": [...],
  "emergency": [...],
  "aliases": {...}
}
```

### 2. 引导词接口

**请求**：
```http
POST /api/guide
Content-Type: application/json

{
  "name": "甲醛"
}
```

**响应**：
```json
{
  "guides": [
    {
      "类别": "管理要求",
      "描述": "查看法律法规要求",
      "数据条数": 3,
      "类别键": "MANAGEMENT"
    },
    ...
  ]
}
```

### 3. 按类别查询接口

**请求**：
```http
POST /api/category
Content-Type: application/json

{
  "name": "甲醛",
  "category": "MANAGEMENT"
}
```

**类别键**：
- `MANAGEMENT` - 管理要求
- `USE_SOP` - 使用要求
- `IDENTIFICATION_PERMIT` - 识别与许可
- `EMERGENCY` - 应急措施

**响应**：
```json
{
  "data": [
    {
      "文档类型": "法规",
      "法规名称": "危险化学品安全管理条例",
      "条款编号": "第15条",
      "条款标题": "安全技术说明书要求",
      ...
    }
  ]
}
```

### 4. 化学品列表接口

**请求**：
```http
GET /api/chemicals
```

**响应**：
```json
{
  "chemicals": [
    {
      "CAS号": "50-00-0",
      "中文名": "甲醛",
      "英文名": "Formaldehyde"
    },
    ...
  ]
}
```

---

## 🛠️ 故障排查

### 问题1: 无法启动应用

**错误信息**：`ModuleNotFoundError: No module named 'flask'`

**解决方案**：
```powershell
pip install Flask PyMySQL
```

---

### 问题2: 数据库连接失败

**错误信息**：`pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")`

**解决方案**：
1. 检查MySQL服务是否运行
2. 检查 `app.py` 中的数据库配置
3. 测试连接：
```powershell
mysql -u root -p 危化品数据库
```

---

### 问题3: 查询返回空结果

**错误信息**：`未找到该化学品`

**解决方案**：
```sql
-- 检查化学品是否存在
SELECT * FROM 化学品 WHERE 中文名 = '甲醛';

-- 检查存储过程
SHOW PROCEDURE STATUS WHERE Db = '危化品数据库';

-- 手动测试存储过程
CALL 获取化学品完整信息('甲醛');
```

---

### 问题4: 中文乱码

**错误信息**：查询结果显示乱码

**解决方案**：
1. 确保数据库使用 `utf8mb4` 字符集
2. 确保 `app.py` 中配置了 `charset='utf8mb4'`
3. 确保HTML文件包含：
```html
<meta charset="UTF-8">
```

---

### 问题5: 端口被占用

**错误信息**：`Address already in use`

**解决方案**：
1. 更换端口：
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

2. 或杀死占用进程：
```powershell
# 查找占用5000端口的进程
netstat -ano | findstr :5000

# 杀死进程（PID替换为实际进程ID）
taskkill /PID <PID> /F
```

---

## 📊 性能优化

### 1. 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_化学品_中文名 ON 化学品(中文名);
CREATE INDEX idx_化学品_CAS号 ON 化学品(CAS号);

-- 分析表
ANALYZE TABLE 化学品;
```

### 2. 缓存优化

可以使用Flask-Caching：
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/search', methods=['POST'])
@cache.cached(timeout=300, query_string=True)
def search():
    # ...
```

### 3. 连接池

使用连接池提高性能：
```python
from dbutils.pooled_db import PooledDB

pool = PooledDB(
    creator=pymysql,
    maxconnections=10,
    **DB_CONFIG
)
```

---

## 🔐 安全建议

### 1. 生产环境配置

```python
# 禁用调试模式
app.run(debug=False)

# 使用环境变量存储密码
import os
DB_CONFIG['password'] = os.environ.get('DB_PASSWORD')
```

### 2. SQL注入防护

存储过程已自动防止SQL注入，但仍建议：
- 不直接拼接SQL语句
- 使用参数化查询
- 验证用户输入

### 3. HTTPS部署

生产环境建议使用：
- Nginx反向代理
- SSL证书
- Gunicorn或uWSGI

---

## 📝 文件结构

```
huaxuepinshujuku/
├── app.py                    # Flask应用主文件
├── requirements.txt          # Python依赖
├── WEB应用使用指南.md        # 本文件
├── templates/
│   └── index.html           # 前端页面
├── db/
│   └── chinese/
│       └── unified_query.sql # 存储过程
└── README.md                # 项目总览
```

---

## 🎉 快速测试

```powershell
# 1. 安装依赖
pip install Flask PyMySQL

# 2. 修改app.py中的数据库密码

# 3. 启动应用
python app.py

# 4. 打开浏览器访问
# http://localhost:5000

# 5. 输入"甲醛"测试查询
```

---

## 📞 技术支持

如有问题，请检查：

1. **数据库** - 存储过程是否正确创建
2. **配置** - 数据库连接信息是否正确
3. **日志** - 查看终端输出的错误信息
4. **浏览器** - 打开开发者工具查看网络请求

---

**祝使用愉快！** 🚀

**版本**: 1.0  
**最后更新**: 2025-10-09

