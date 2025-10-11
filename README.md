# 危化品数据库

> **版本**: 3.0 (中文版)  
> **更新日期**: 2025-10-09  
> **数据库名**: `危化品数据库`

---

## 📚 目录

- [快速开始](#-快速开始)
- [项目简介](#-项目简介)
- [数据库结构](#-数据库结构)
- [部署指南](#-部署指南)
- [统一查询功能](#-统一查询功能)
- [常用查询](#-常用查询)
- [数据录入](#-数据录入)
- [注意事项](#️-注意事项)
- [文档说明](#-文档说明)

---

## 🚀 快速开始

### 前置要求
- MySQL 8.0+
- 支持UTF-8的客户端工具（推荐 DataGrip、Navicat）
- **（可选）** Python 3.7+ + Flask（用于Web应用）

### 选择使用方式

#### 🌐 方式1：Web应用（推荐新手）

1. **安装Python依赖**：
```powershell
pip install Flask PyMySQL
```

2. **配置数据库密码**（编辑 `app.py`）：
```python
DB_CONFIG = {
    'password': '你的MySQL密码',  # 修改这里
    ...
}
```

3. **启动Web应用**：
```powershell
python app.py
```

4. **访问应用**：  
打开浏览器访问 http://localhost:5000

**详细说明**：查看 [`WEB应用使用指南.md`](WEB应用使用指南.md)

---

#### 💻 方式2：直接使用数据库

### 三步部署

#### 方法1：使用 source 命令（最推荐）⭐

```powershell
# 1. 连接MySQL
mysql -u root -p
```

在MySQL中执行：
```sql
-- 2. 初始化数据库
source C:/Users/Administrator.DESKTOP-URBQKM0/Desktop/huaxuepinshujuku/db/chinese/init_database.sql

-- 3. 切换到数据库
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

#### 方法2：使用 PowerShell

```powershell
cd C:\Users\Administrator.DESKTOP-URBQKM0\Desktop\huaxuepinshujuku

# 注意：必须使用 -Encoding UTF8 参数
Get-Content -Encoding UTF8 db\chinese\init_database.sql | mysql -u root -p
Get-Content -Encoding UTF8 db\chinese\sample_data.sql | mysql -u root -p 危化品数据库
Get-Content -Encoding UTF8 db\chinese\regulation_data.sql | mysql -u root -p 危化品数据库
Get-Content -Encoding UTF8 db\chinese\unified_query.sql | mysql -u root -p 危化品数据库
```

---

## 📖 项目简介

### 功能定位

本数据库为**危险化学品AI应用**提供数据支持，实现以下核心功能：

**输入**：化学品名称（如"甲醛"）

**输出**：
1. **管理要求** - 法律法规条款、文档链接
2. **使用要求** - 安全操作规程（SOP）
3. **识别与许可** - UN编号、运输分类、GHS分类、目录标识
4. **应急措施** - 急救、消防、泄漏处置
5. **辅助信息** - GHS象形图、H/P代码、理化特性

### 核心特性

- ✅ **18张数据表**：化学品、法规、MSDS、SOP、应急卡片等
- ✅ **中文表名列名**：更直观易懂
- ✅ **三类文档支持**：法律、法规、标准
- ✅ **版本化管理**：文档版本追踪
- ✅ **地域管辖**：支持国家/省/市三级
- ✅ **全文检索**：FULLTEXT索引支持
- ✅ **统一查询**：3个存储过程简化查询
- ✅ **引导词功能**：自动生成四类别按钮

---

## 🗂️ 数据库结构

### 18张数据表（5层架构）

#### 第1层：化学品主数据（5张表）

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| **化学品** | 化学品主表 | CAS号、中文名、英文名、分子式 |
| **化学品别名** | 别名和同义词 | 名称（含FULLTEXT索引）|
| **GHS分类** | GHS危害分类 | 象形图、H代码、P代码（JSON）|
| **运输分类** | UN运输信息 | UN编号、包装类别、运输名称 |
| **目录标识** | 危险品目录标识 | 各类目录是否列入 |

#### 第2层：文档与条款（5张表）

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| **法规机构** | 监管机构 | 机构名称、级别 |
| **文档** | 法规文档 | 文档类型（法律/法规/标准）、状态 |
| **文档版本** | 版本管理 | 版本号、是否当前版本、PDF链接 |
| **文档地域管辖** | 地域范围 | 国家/省/市 |
| **条款** | 法规条款内容 | 条款编号、标题、内容、维度分类 |

**条款维度分类（facet）**：
- `MANAGEMENT` - 管理要求
- `USE_SOP` - 使用要求
- `IDENTIFICATION_PERMIT` - 识别与许可
- `EMERGENCY` - 应急措施
- `OTHER` - 其他

#### 第3层：映射关系（1张表）

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| **化学品条款映射** | 化学品↔条款关联 | 相关度评分、标签 |

#### 第4层：操作与应急（4张表）

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| **操作规程** | SOP库 | 操作名称、风险评估 |
| **操作规程步骤** | SOP详细步骤 | 步骤序号、操作内容、注意事项 |
| **应急卡片** | 应急处置卡 | 卡片类型（急救/消防/泄漏）|

#### 第5层：MSDS数据（3张表）

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| **MSDS主表** | MSDS文档元数据 | 供应商、版本、日期 |
| **MSDS章节** | 16个章节内容 | 章节序号、标题、内容（含FULLTEXT）|
| **理化特性** | 物理化学性质 | 熔点、沸点、闪点、密度等 |

#### 第6层：NLP增强（2张表）

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| **自然语言维度** | 四大类别定义 | 维度键、显示名称、描述 |
| **自然语言模板** | 查询模板 | 意图、模板文本 |

### 索引策略

- **主键索引**：所有表自增主键
- **外键索引**：关联字段自动索引
- **FULLTEXT索引**：
  - `化学品别名.名称`
  - `MSDS章节.章节标题, 内容`
  - `条款.标题, 文本`
- **普通索引**：常用查询字段

---

## 🚀 部署指南

### 数据库文件

```
db/
└── chinese/                       # 中文版数据库脚本
    ├── init_database.sql          # 建表（18张表 + 4个维度初始化）
    ├── sample_data.sql            # 示例数据（甲醛、乙醇）
    ├── regulation_data.sql        # 法规条款（6条）
    ├── query_examples.sql         # 查询示例（8个场景）
    └── unified_query.sql          # 统一查询存储过程（3个）⭐
```

### ⚠️ PowerShell 注意事项

**问题1：重定向符号不支持**
- ❌ `mysql -u root -p < file.sql` （会报错）
- ✅ `Get-Content file.sql | mysql -u root -p`

**问题2：中文编码**
- ❌ `Get-Content file.sql | mysql` （中文乱码）
- ✅ `Get-Content -Encoding UTF8 file.sql | mysql`
- ✅ 使用 `source` 命令（最推荐，无编码问题）

### 完整部署命令

**推荐方式（source命令）**：
```sql
-- 在MySQL中执行
source C:/路径/db/chinese/init_database.sql
USE 危化品数据库;
source C:/路径/db/chinese/sample_data.sql
source C:/路径/db/chinese/regulation_data.sql
source C:/路径/db/chinese/unified_query.sql
```

**PowerShell方式**：
```powershell
Get-Content -Encoding UTF8 db\chinese\init_database.sql | mysql -u root -p
Get-Content -Encoding UTF8 db\chinese\sample_data.sql | mysql -u root -p 危化品数据库
Get-Content -Encoding UTF8 db\chinese\regulation_data.sql | mysql -u root -p 危化品数据库
Get-Content -Encoding UTF8 db\chinese\unified_query.sql | mysql -u root -p 危化品数据库
```

### DataGrip 连接配置

1. 新建MySQL连接
2. 配置参数：
   - **Database**: `危化品数据库`
   - **URL参数**: `characterEncoding=utf8mb4`
   - **高级设置** → **VM选项**: `-Dfile.encoding=UTF-8`

---

## ⚡ 统一查询功能

新增的 `unified_query.sql` 提供3个核心存储过程：

### 1. 获取化学品完整信息

```sql
CALL 获取化学品完整信息('甲醛');
```

**返回6个结果集**：

1. **基本信息** - CAS号、中文名、英文名、分子式等
2. **管理要求** - 法律法规条款 + PDF链接
   ```
   《危险化学品安全管理条例》
   第15条：安全技术说明书和标签要求
   PDF: http://example.com/regulations/hazmat_2013.pdf
   ```

3. **使用要求** - 安全操作规程
   ```
   甲醛溶液稀释操作规程
   步骤1：穿戴防护装备
   步骤2：在通风橱内操作
   ...
   ```

4. **识别与许可** - GHS + 运输 + 目录标识
   ```
   GHS分类：急性毒性2级、皮肤腐蚀1级
   UN编号：1198
   运输类别：3（易燃液体）
   重点监管：是
   ```

5. **应急措施** - 急救、消防、泄漏处置
   ```
   吸入：移至新鲜空气处...
   消防：用雾状水、干粉、二氧化碳...
   泄漏：隔离泄漏区，切断火源...
   ```

6. **别名信息** - 所有别名和同义词

### 2. 获取引导词（四类别按钮）

```sql
CALL 获取引导词('甲醛');
```

**返回示例**：
| 维度键 | 显示名称 | 描述 | 数量 |
|--------|---------|------|-----|
| MANAGEMENT | 管理要求 | 查看法律法规要求 | 3条 |
| USE_SOP | 使用要求 | 查看安全操作规程 | 2条 |
| IDENTIFICATION_PERMIT | 识别与许可 | 查看GHS分类、运输许可 | 3条 |
| EMERGENCY | 应急措施 | 查看应急预案和处置措施 | 3条 |

### 3. 按类别查询

```sql
-- 只查管理要求
CALL 按类别查询('甲醛', 'MANAGEMENT');

-- 只查使用要求
CALL 按类别查询('甲醛', 'USE_SOP');

-- 只查识别与许可
CALL 按类别查询('甲醛', 'IDENTIFICATION_PERMIT');

-- 只查应急措施
CALL 按类别查询('甲醛', 'EMERGENCY');
```

---

## 🔍 常用查询

### 基本查询

```sql
-- 通过CAS号查询
SELECT CAS号, 中文名, 英文名, 分子式 
FROM 化学品 
WHERE CAS号 = '50-00-0';

-- 通过中文名模糊查询
SELECT CAS号, 中文名, 英文名 
FROM 化学品 
WHERE 中文名 LIKE '%甲醛%';

-- 全文检索别名
SELECT c.CAS号, c.中文名, a.名称 AS 匹配别名
FROM 化学品 c
JOIN 化学品别名 a ON c.编号 = a.化学品编号
WHERE MATCH(a.名称) AGAINST('福尔马林' IN NATURAL LANGUAGE MODE);
```

### 获取法规条款

```sql
-- 获取甲醛的所有法规要求
SET @化学品编号 = (SELECT 编号 FROM 化学品 WHERE CAS号 = '50-00-0');

SELECT 
    d.标题 AS 法规名称,
    d.文档类型,
    c.条款编号,
    c.标题 AS 条款标题,
    c.内容,
    v.PDF链接,
    m.相关度评分
FROM 化学品条款映射 m
JOIN 条款 c ON c.编号 = m.条款编号
JOIN 文档版本 v ON v.编号 = c.版本编号
JOIN 文档 d ON d.编号 = v.文档编号
WHERE m.化学品编号 = @化学品编号
  AND c.维度 = 'MANAGEMENT'
ORDER BY m.相关度评分 DESC;
```

### 获取MSDS信息

```sql
-- 获取急救措施（第4部分）
SELECT 章节标题, 内容
FROM MSDS章节 s
JOIN MSDS主表 m ON m.编号 = s.文档编号
JOIN 化学品 c ON c.编号 = m.化学品编号
WHERE c.CAS号 = '50-00-0' 
  AND s.章节序号 = 4;

-- 获取理化特性
SELECT 外观, 熔点, 沸点, 闪点, 爆炸极限, 相对密度
FROM 理化特性 p
JOIN MSDS主表 m ON m.编号 = p.文档编号
JOIN 化学品 c ON c.编号 = m.化学品编号
WHERE c.CAS号 = '50-00-0';
```

### 获取操作规程

```sql
-- 获取甲醛的安全操作规程
SELECT 
    s.操作名称,
    s.适用范围,
    s.风险评估,
    st.步骤序号,
    st.步骤名称,
    st.操作内容,
    st.注意事项
FROM 操作规程 s
JOIN 操作规程步骤 st ON st.规程编号 = s.编号
JOIN 化学品 c ON c.编号 = s.化学品编号
WHERE c.CAS号 = '50-00-0'
ORDER BY st.步骤序号;
```

### 数据统计

```sql
-- 化学品数据完整性统计
SELECT 
    c.中文名,
    COUNT(DISTINCT a.编号) AS 别名数,
    COUNT(DISTINCT g.编号) AS GHS分类数,
    COUNT(DISTINCT ms.编号) AS MSDS章节数,
    COUNT(DISTINCT m.编号) AS 关联条款数,
    COUNT(DISTINCT s.编号) AS 操作规程数,
    COUNT(DISTINCT ec.编号) AS 应急卡片数
FROM 化学品 c
LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
LEFT JOIN GHS分类 g ON c.编号 = g.化学品编号
LEFT JOIN MSDS主表 md ON c.编号 = md.化学品编号
LEFT JOIN MSDS章节 ms ON md.编号 = ms.文档编号
LEFT JOIN 化学品条款映射 m ON c.编号 = m.化学品编号
LEFT JOIN 操作规程 s ON c.编号 = s.化学品编号
LEFT JOIN 应急卡片 ec ON c.编号 = ec.化学品编号
GROUP BY c.编号, c.中文名;
```

---

## 📝 数据录入

### 录入化学品

```sql
-- 1. 插入化学品基本信息
INSERT INTO 化学品 (CAS号, 中文名, 英文名, 分子式, EC号)
VALUES ('7664-93-9', '硫酸', 'Sulfuric acid', 'H2SO4', '231-639-5');

SET @化学品编号 = LAST_INSERT_ID();

-- 2. 添加别名
INSERT INTO 化学品别名 (化学品编号, 名称, 语言)
VALUES 
    (@化学品编号, '浓硫酸', '中文'),
    (@化学品编号, 'oil of vitriol', '英文');

-- 3. 添加GHS分类
INSERT INTO GHS分类 (化学品编号, 危害类别, 危害级别, 象形图, H代码, P代码)
VALUES (@化学品编号, 
    '皮肤腐蚀/刺激', 
    '1A', 
    '["GHS05"]',
    '["H314"]',
    '["P280","P305+P351+P338","P310"]'
);

-- 4. 添加运输分类
INSERT INTO 运输分类 (化学品编号, UN编号, 运输名称, 危险性类别, 包装类别)
VALUES (@化学品编号, '1830', '硫酸', '8', 'II');
```

### 录入法规条款

```sql
-- 1. 插入监管机构
INSERT INTO 法规机构 (机构名称, 机构级别, 官网)
VALUES ('应急管理部', '国家', 'https://www.mem.gov.cn');

SET @机构编号 = LAST_INSERT_ID();

-- 2. 插入法规文档
INSERT INTO 文档 (标题, 文档类型, 发布机构编号, 发布日期, 状态)
VALUES ('危险化学品安全管理条例', '法规', @机构编号, '2013-12-07', '有效');

SET @文档编号 = LAST_INSERT_ID();

-- 3. 插入文档版本
INSERT INTO 文档版本 (文档编号, 版本号, 是否当前版本, PDF链接)
VALUES (@文档编号, '2013年修订', 1, 'http://example.com/regulations.pdf');

SET @版本编号 = LAST_INSERT_ID();

-- 4. 插入条款
INSERT INTO 条款 (版本编号, 条款编号, 标题, 内容, 维度)
VALUES (@版本编号, 
    '第15条', 
    '安全技术说明书和标签要求',
    '生产危险化学品的，应当在危险化学品的包装上粘贴或者拴挂与包装内危险化学品相符的化学品安全标签...',
    'MANAGEMENT'
);

SET @条款编号 = LAST_INSERT_ID();

-- 5. 关联化学品与条款
INSERT INTO 化学品条款映射 (化学品编号, 条款编号, 相关度评分, 标签)
VALUES (@化学品编号, @条款编号, 0.95, '标签要求,MSDS');
```

### 录入操作规程

```sql
-- 1. 插入操作规程
INSERT INTO 操作规程 (化学品编号, 操作名称, 适用范围, 风险评估)
VALUES (@化学品编号, 
    '硫酸稀释操作规程',
    '实验室浓硫酸稀释操作',
    '高风险：强腐蚀性，稀释时会放热'
);

SET @规程编号 = LAST_INSERT_ID();

-- 2. 添加操作步骤
INSERT INTO 操作规程步骤 (规程编号, 步骤序号, 步骤名称, 操作内容, 注意事项)
VALUES 
    (@规程编号, 1, '准备工作', '穿戴防护服、防护眼镜、耐酸手套', '确保防护装备完好'),
    (@规程编号, 2, '稀释操作', '缓慢将浓硫酸加入水中，边加边搅拌', '❌ 严禁将水加入浓硫酸！'),
    (@规程编号, 3, '冷却静置', '待溶液冷却至室温后使用', '稀释过程会剧烈放热');
```

### 录入应急卡片

```sql
INSERT INTO 应急卡片 (化学品编号, 卡片类型, 标题, 内容, 紧急联系方式)
VALUES 
    (@化学品编号, '急救', '硫酸急救措施', '皮肤接触：立即脱去污染的衣着，用大量流动清水冲洗至少15分钟...', '120'),
    (@化学品编号, '消防', '硫酸消防措施', '灭火方法：用雾状水保持火场容器冷却...', '119'),
    (@化学品编号, '泄漏', '硫酸泄漏处理', '隔离泄漏污染区，限制出入。建议应急处理人员戴防毒面具...', '应急指挥中心');
```

---

## ⚠️ 注意事项

### 1. 字符集配置

确保MySQL配置正确：

```ini
# my.cnf 或 my.ini
[client]
default-character-set = utf8mb4

[mysql]
default-character-set = utf8mb4

[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_0900_ai_ci
```

### 2. 中文标识符使用

```sql
-- 推荐使用反引号（避免关键字冲突）
SELECT `CAS号`, `中文名` FROM `化学品`;

-- 大多数情况下也可以省略
SELECT CAS号, 中文名 FROM 化学品;
```

### 3. JSON 字段操作

```sql
-- 查询GHS分类的H代码
SELECT 
    c.中文名,
    g.H代码,
    JSON_EXTRACT(g.H代码, '$[0]') AS 第一个H代码
FROM 化学品 c
JOIN GHS分类 g ON c.编号 = g.化学品编号;

-- 查询包含特定H代码的化学品
SELECT c.中文名
FROM 化学品 c
JOIN GHS分类 g ON c.编号 = g.化学品编号
WHERE JSON_CONTAINS(g.H代码, '"H314"');
```

### 4. 全文检索使用

```sql
-- 自然语言模式（默认）
SELECT * FROM 化学品别名
WHERE MATCH(名称) AGAINST('福尔马林');

-- 布尔模式（支持运算符）
SELECT * FROM 条款
WHERE MATCH(标题, 文本) AGAINST('+危险 +储存 -运输' IN BOOLEAN MODE);
```

### 5. 数据一致性

- **外键约束**：删除主记录前需先删除关联记录（或使用 CASCADE）
- **唯一约束**：CAS号、文档版本等字段不允许重复
- **必填字段**：插入时必须提供 NOT NULL 字段的值

---

## 📊 示例数据

### 已录入化学品

| CAS号 | 中文名 | 英文名 | MSDS | 法规条款 | SOP | 应急卡片 |
|-------|--------|--------|------|----------|-----|---------|
| 50-00-0 | 甲醛 | Formaldehyde | 16/16 ✅ | 3条 | 2个 | 3个 |
| 64-17-5 | 乙醇 | Ethanol | 16/16 ✅ | 3条 | 2个 | 3个 |

### 已录入法规

- 《危险化学品安全管理条例》（2013年修订版）- 6条
  - 第15条：安全技术说明书和标签要求（MANAGEMENT）
  - 第20条：危险化学品储存单位要求（MANAGEMENT）
  - 第29条：危险化学品安全使用许可（USE_SOP）
  - 第38条：剧毒化学品购买要求（IDENTIFICATION_PERMIT）
  - 第47条：危险化学品道路运输企业要求（IDENTIFICATION_PERMIT）
  - 第78条：危险化学品事故应急救援要求（EMERGENCY）

---

## 📚 文档说明

### 设计文档

| 文档 | 说明 |
|------|------|
| **危化品大模型数据库设计.md** | 原始详细设计文档（550行）|
| **危险化学品AI应用的数据结构设计.md** | 简化版设计文档（308行）|
| **数据库设计文档.md** | 完整技术设计文档 |

### Web应用 ⭐ 新增

| 文件 | 说明 |
|------|------|
| **app.py** | Flask后端应用（API接口）|
| **templates/index.html** | 前端页面（美观UI）|
| **requirements.txt** | Python依赖列表 |
| **WEB应用使用指南.md** | Web应用完整使用文档 |

**功能特性**：
- ✅ 搜索框 + 自动补全
- ✅ 完整查询模式（一次性显示所有信息）
- ✅ 引导查询模式（四类别按钮）
- ✅ 美观的渐变UI设计
- ✅ 响应式布局（支持移动端）
- ✅ RESTful API接口

### 数据库脚本

| 文件 | 说明 | 位置 |
|------|------|------|
| `init_database.sql` | 建表脚本（18张表）| `db/chinese/` |
| `sample_data.sql` | 示例数据（2个化学品）| `db/chinese/` |
| `regulation_data.sql` | 法规条款（6条）| `db/chinese/` |
| `query_examples.sql` | 查询示例（8个场景）| `db/chinese/` |
| `unified_query.sql` | 统一查询存储过程（3个）⭐ | `db/chinese/` |

详细说明请查看：`db/README.md`

---

## 🎯 下一步计划

### 当前状态
- ✅ 数据库设计：100%完成
- ✅ 查询功能：100%完成（含统一查询）
- ⚠️ 数据内容：5%完成（需要大量补充）
- 📝 应用开发：待规划

### 后续工作

1. **数据补充**（优先级：高）
   - 录入100-500个常用化学品
   - 补充500-2000条法规条款
   - 编写对应的SOP和应急卡片

2. **API开发**（优先级：中）
   - Python Flask/FastAPI
   - 调用存储过程返回JSON
   - RESTful接口设计

3. **前端开发**（优先级：中）
   - 搜索框 + 自动补全
   - 四类别引导词按钮
   - 结果展示页面

4. **AI集成**（优先级：低）
   - 自然语言处理
   - 向量嵌入（RAG）
   - 智能问答

---

## 📞 技术支持

**版本**: 3.0 (中文版)  
**创建日期**: 2025-10-09  
**维护者**: AI助手

### 验证安装

```sql
-- 连接数据库
mysql -u root -p 危化品数据库

-- 查看所有表（应该有18张）
SHOW TABLES;

-- 查看化学品数量
SELECT COUNT(*) AS 化学品数量 FROM 化学品;

-- 测试统一查询
CALL 获取化学品完整信息('甲醛');
CALL 获取引导词('甲醛');
CALL 按类别查询('甲醛', 'MANAGEMENT');
```

---

**开始使用**: 
```bash
mysql -u root -p
source C:/路径/db/chinese/init_database.sql
```

🚀 **立即开始危化品数据管理！**
