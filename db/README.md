# 数据库脚本说明

本目录包含危化品数据库的所有SQL脚本文件（中文版）。

---

## 📁 文件结构

```
db/
└── chinese/                       # 中文版数据库脚本
    ├── init_database.sql          # 数据库初始化（18张表）
    ├── sample_data.sql            # 示例数据（甲醛、乙醇）
    ├── regulation_data.sql        # 法规条款（6条）
    ├── query_examples.sql         # 查询示例（8个场景）
    └── unified_query.sql          # 统一查询存储过程（3个）⭐
```

---

## 🚀 快速部署

### 方法1：使用 source 命令（最推荐）⭐

```powershell
# 1. 连接MySQL
mysql -u root -p
```

在MySQL中执行：
```sql
-- 2. 初始化数据库
source C:/Users/Administrator.DESKTOP-URBQKM0/Desktop/huaxuepinshujuku/db/chinese/init_database.sql

-- 3. 切换数据库
USE 危化品数据库;

-- 4. 导入数据
source C:/Users/Administrator.DESKTOP-URBQKM0/Desktop/huaxuepinshujuku/db/chinese/sample_data.sql
source C:/Users/Administrator.DESKTOP-URBQKM0/Desktop/huaxuepinshujuku/db/chinese/regulation_data.sql
source C:/Users/Administrator.DESKTOP-URBQKM0/Desktop/huaxuepinshujuku/db/chinese/unified_query.sql

-- 5. 验证
SHOW TABLES;
SELECT CAS号, 中文名 FROM 化学品;
CALL 获取化学品完整信息('甲醛');
```

### 方法2：使用 PowerShell

```powershell
cd C:\Users\Administrator.DESKTOP-URBQKM0\Desktop\huaxuepinshujuku

# 注意：必须使用 -Encoding UTF8 参数
Get-Content -Encoding UTF8 db\chinese\init_database.sql | mysql -u root -p
Get-Content -Encoding UTF8 db\chinese\sample_data.sql | mysql -u root -p 危化品数据库
Get-Content -Encoding UTF8 db\chinese\regulation_data.sql | mysql -u root -p 危化品数据库
Get-Content -Encoding UTF8 db\chinese\unified_query.sql | mysql -u root -p 危化品数据库
```

---

## 📄 文件详细说明

### 1. init_database.sql
**功能**：数据库初始化
- 创建数据库：`危化品数据库`
- 创建18张数据表（全中文表名列名）
- 设置索引和外键约束
- 初始化4个维度基础数据

**表结构**：
1. 化学品主数据（5张）：化学品、化学品别名、GHS分类、运输分类、目录标识
2. 文档与条款（5张）：法规机构、文档、文档版本、文档地域管辖、条款
3. 映射关系（1张）：化学品条款映射
4. 操作与应急（3张）：操作规程、操作规程步骤、应急卡片
5. MSDS数据（3张）：MSDS主表、MSDS章节、理化特性
6. NLP增强（2张）：自然语言维度、自然语言模板

### 2. sample_data.sql
**功能**：示例数据
- 2个化学品：甲醛（50-00-0）、乙醇（64-17-5）
- 完整的MSDS数据（16章节 × 2）
- GHS分类、运输分类
- 理化特性数据

**数据量**：约50条记录

### 3. regulation_data.sql
**功能**：法规条款数据
- 1个监管机构（应急管理部）
- 1部法规（《危险化学品安全管理条例》）
- 6条条款（覆盖4个维度）
- 10条化学品条款映射
- 4个操作规程（含步骤）
- 6个应急卡片

**数据量**：约30条记录

### 4. query_examples.sql
**功能**：查询示例
- 化学品基本信息查询
- 全文检索示例
- 法规条款查询
- MSDS信息查询
- GHS/运输分类查询
- 操作规程查询
- 应急卡片查询
- 数据统计查询

**共8个场景**，可直接在MySQL中执行

### 5. unified_query.sql ⭐
**功能**：统一查询存储过程

提供3个核心存储过程：

#### 存储过程1：获取化学品完整信息
```sql
CALL 获取化学品完整信息('甲醛');
```
返回6个结果集：
1. 基本信息
2. 管理要求（法规 + PDF链接）
3. 使用要求（SOP）
4. 识别与许可（GHS + 运输 + 目录）
5. 应急措施（急救 + 消防 + 泄漏）
6. 别名信息

#### 存储过程2：获取引导词
```sql
CALL 获取引导词('甲醛');
```
返回四个类别按钮及数量：
- 管理要求（X条）
- 使用要求（X条）
- 识别与许可（X条）
- 应急措施（X条）

#### 存储过程3：按类别查询
```sql
CALL 按类别查询('甲醛', 'MANAGEMENT');
```
参数：
- 化学品名称
- 维度键：MANAGEMENT / USE_SOP / IDENTIFICATION_PERMIT / EMERGENCY

---

## 🔍 验证安装

```sql
-- 连接数据库
mysql -u root -p 危化品数据库

-- 1. 查看所有表（应该有18张）
SHOW TABLES;

-- 2. 查看化学品数量
SELECT COUNT(*) AS 化学品数量 FROM 化学品;
-- 应返回: 2

-- 3. 查看化学品列表
SELECT CAS号, 中文名, 英文名 FROM 化学品;
-- 输出：
-- 50-00-0 | 甲醛 | Formaldehyde
-- 64-17-5 | 乙醇 | Ethanol

-- 4. 查看存储过程
SHOW PROCEDURE STATUS WHERE Db = '危化品数据库';
-- 应显示3个存储过程

-- 5. 测试统一查询
CALL 获取化学品完整信息('甲醛');
CALL 获取引导词('甲醛');
CALL 按类别查询('甲醛', 'MANAGEMENT');
```

---

## ⚠️ 注意事项

### 1. PowerShell 编码问题

**问题**：PowerShell的 `Get-Content` 默认可能导致中文乱码

**解决方案**：
- ✅ **推荐**：使用 `source` 命令（最可靠，无编码问题）
- ✅ **备选**：使用 `-Encoding UTF8` 参数
- ✅ **传统**：使用 `cmd /c` 命令

### 2. MySQL 字符集配置

确保MySQL配置正确：

```ini
# my.cnf 或 my.ini
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_0900_ai_ci

[client]
default-character-set = utf8mb4
```

### 3. 路径问题

- `source` 命令中的路径使用**正斜杠** `/`
- PowerShell命令中的路径使用**反斜杠** `\`
- 路径包含空格时需要用引号包围

### 4. 中文表名使用

在SQL语句中使用中文标识符时，建议使用反引号：

```sql
-- 推荐写法
SELECT `CAS号`, `中文名` FROM `化学品`;

-- 也可以省略（大多数情况）
SELECT CAS号, 中文名 FROM 化学品;
```

---

## 📊 数据库特性

| 特性 | 说明 |
|------|------|
| **数据库名** | `危化品数据库` |
| **表数量** | 18张 |
| **表名列名** | 全中文 |
| **字符集** | UTF-8（utf8mb4）|
| **示例数据** | 2个化学品（完整数据）|
| **法规条款** | 6条（4个维度）|
| **操作规程** | 4个SOP（含步骤）|
| **应急卡片** | 6个（急救/消防/泄漏）|
| **统一查询** | 3个存储过程 ✅ |
| **全文索引** | 3个表支持 ✅ |

---

## 📖 相关文档

- **../README.md** - 项目总览和完整使用指南
- **../危化品大模型数据库设计.md** - 原始详细设计文档
- **../危险化学品AI应用的数据结构设计.md** - 简化版设计
- **../数据库设计文档.md** - 完整技术文档

---

**最后更新**：2025-10-09  
**维护者**：AI助手  
**版本**：3.0（精简版）

🚀 **快速开始**：`mysql -u root -p` → `source .../init_database.sql`
