# 📊 MSDS数据存储方案指南

> 如何将合规化学网爬取的16个部分数据存储到数据库中

---

## 🎯 三种存储方案对比

### 方案1：数据库结构化存储（推荐）⭐

**优点**：
- ✅ 查询速度快
- ✅ 支持全文搜索
- ✅ 数据结构化，易于分析
- ✅ 支持事务和并发
- ✅ 与其他表关联查询

**缺点**：
- ❌ 需要解析HTML
- ❌ 导入稍复杂

**适用场景**：
- 需要频繁查询MSDS内容
- 需要与法规、SOP等关联
- 需要AI大模型调用
- 生产环境使用

---

### 方案2：JSON文件存储 + 数据库索引

**优点**：
- ✅ 简单快速
- ✅ 保留原始格式
- ✅ 灵活性高

**缺点**：
- ❌ 查询效率低
- ❌ 不支持全文搜索
- ❌ 难以关联查询

**适用场景**：
- 临时存储
- 数据备份
- 原型开发

---

### 方案3：纯HTML文件存储

**优点**：
- ✅ 最简单
- ✅ 完整保留原格式

**缺点**：
- ❌ 无法查询
- ❌ 无法与数据库集成
- ❌ 难以维护

**适用场景**：
- 仅用于备份
- 人工查阅

---

## 📋 推荐方案详解：数据库存储

### 数据库表结构

你的数据库已经设计了专门的表结构：

```sql
-- MSDS文档头表
CREATE TABLE MSDS文档 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT,
    化学品编号 BIGINT NOT NULL UNIQUE,
    编制单位 VARCHAR(256),
    编制人 VARCHAR(256),
    编制日期 DATE,
    编制依据 VARCHAR(256),
    ...
);

-- MSDS章节表（存储16个部分）
CREATE TABLE MSDS章节 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT,
    文档编号 BIGINT NOT NULL,
    章节序号 TINYINT NOT NULL,        -- 1-16
    章节标题 VARCHAR(256) NOT NULL,   -- 如：急救措施
    内容 LONGTEXT,                    -- 纯文本内容
    结构化数据 JSON,                  -- 结构化JSON数据
    ...
    UNIQUE KEY 唯一键_文档章节 (文档编号, 章节序号)
);
```

---

## 🚀 完整工作流程

### 步骤1：爬取MSDS数据

```bash
# 使用智能爬虫爬取
python auto_scrape_msds.py "化学品链接"

# 输出：msds_甲苯/ 文件夹（16个HTML文件）
```

---

### 步骤2：导入数据库

#### 方法A：使用批处理文件（推荐）⭐

```bash
# 双击运行
导入MSDS到数据库.bat

# 按提示输入：
# 1. 文件夹名称：msds_甲苯
# 2. CAS号：108-88-3
# 3. 数据库密码：123456
```

#### 方法B：使用命令行

```bash
# 基本用法
python import_msds_to_db.py --folder msds_甲苯 --cas 108-88-3

# 指定密码
python import_msds_to_db.py -f msds_甲苯 -c 108-88-3 -p 你的密码

# 完整示例
python import_msds_to_db.py \
    --folder msds_乙醇无水 \
    --cas 64-17-5 \
    --password 123456
```

---

### 步骤3：验证导入结果

```sql
-- 查看MSDS文档
SELECT * FROM MSDS文档 WHERE 化学品编号 = 1;

-- 查看所有章节
SELECT 章节序号, 章节标题, 
       CHAR_LENGTH(内容) AS 内容长度 
FROM MSDS章节 
WHERE 文档编号 = 1 
ORDER BY 章节序号;

-- 查看特定章节内容
SELECT 章节标题, 内容 
FROM MSDS章节 
WHERE 文档编号 = 1 AND 章节序号 = 4;  -- 急救措施

-- 全文搜索
SELECT 章节序号, 章节标题 
FROM MSDS章节 
WHERE MATCH(章节标题, 内容) AGAINST('急救' IN NATURAL LANGUAGE MODE);
```

---

## 📊 导入脚本工作原理

### 1. 解析HTML文件

```python
def parse_html_content(html_path):
    """解析HTML，提取纯文本和结构化数据"""
    # 1. 读取HTML
    # 2. 移除script、style标签
    # 3. 提取纯文本
    # 4. 提取表格、列表等结构化数据
    # 5. 返回：(纯文本, JSON结构化数据)
```

### 2. 查找化学品

```python
# 根据CAS号查找化学品ID
SELECT 编号 FROM 化学品 WHERE CAS号 = '108-88-3';
```

### 3. 创建MSDS文档

```python
# 如果不存在，创建MSDS文档记录
INSERT INTO MSDS文档 (化学品编号, 编制单位, 编制依据) 
VALUES (1, '合规化学网', 'GB/T 16483, GB/T 17519');
```

### 4. 插入16个章节

```python
# 对每个HTML文件
for chapter_num in range(1, 17):
    # 解析HTML
    content, json_data = parse_html_content(html_file)
    
    # 插入数据库
    INSERT INTO MSDS章节 
    (文档编号, 章节序号, 章节标题, 内容, 结构化数据) 
    VALUES (doc_id, chapter_num, title, content, json_data);
```

---

## 💡 数据结构示例

### 纯文本内容（`内容`字段）

```
急救措施

皮肤接触：
立即脱去污染的衣着，用大量流动清水冲洗至少15分钟...

眼睛接触：
立即提起眼睑，用大量流动清水或生理盐水彻底冲洗至少15分钟...

吸入：
迅速脱离现场至空气新鲜处。保持呼吸道通畅...

食入：
饮足量温水，催吐。就医...
```

### 结构化JSON数据（`结构化数据`字段）

```json
{
  "tables": [
    [
      ["接触途径", "急救措施"],
      ["皮肤接触", "立即脱去污染的衣着，用大量流动清水冲洗..."],
      ["眼睛接触", "立即提起眼睑，用大量流动清水或生理盐水..."],
      ["吸入", "迅速脱离现场至空气新鲜处..."],
      ["食入", "饮足量温水，催吐。就医"]
    ]
  ],
  "lists": [
    ["保持呼吸道通畅", "如呼吸困难，给输氧", "如呼吸停止，立即进行人工呼吸", "就医"]
  ],
  "original_html": "..."
}
```

---

## 🔍 查询示例

### 示例1：查询化学品的所有MSDS章节

```sql
SELECT 
    c.章节序号,
    c.章节标题,
    SUBSTRING(c.内容, 1, 100) AS 内容摘要
FROM 化学品 p
JOIN MSDS文档 m ON p.编号 = m.化学品编号
JOIN MSDS章节 c ON m.编号 = c.文档编号
WHERE p.CAS号 = '108-88-3'
ORDER BY c.章节序号;
```

### 示例2：查询急救措施

```sql
SELECT 内容
FROM MSDS章节
WHERE 文档编号 = 1 
  AND 章节序号 = 4;  -- 第4部分：急救措施
```

### 示例3：全文搜索"储存"相关信息

```sql
SELECT 
    p.中文名,
    c.章节标题,
    c.内容
FROM 化学品 p
JOIN MSDS文档 m ON p.编号 = m.化学品编号
JOIN MSDS章节 c ON m.编号 = c.文档编号
WHERE MATCH(c.章节标题, c.内容) 
      AGAINST('储存 温度' IN BOOLEAN MODE);
```

### 示例4：查询特定化学品的理化特性

```sql
-- 方法1：从MSDS章节表查询（包含完整描述）
SELECT 内容
FROM MSDS章节
WHERE 文档编号 = 1 
  AND 章节序号 = 9;  -- 第9部分：理化特性

-- 方法2：从MSDS理化特性表查询（结构化数据）
SELECT 外观, pH值, 熔点, 沸点, 闪点, 爆炸极限, 溶解性
FROM MSDS理化特性
WHERE 文档编号 = 1;
```

---

## ⚙️ 批量导入

### 批量脚本示例

创建 `batch_import.bat`：

```batch
@echo off
echo 开始批量导入MSDS数据...

REM 导入甲苯
python import_msds_to_db.py -f msds_甲苯 -c 108-88-3

REM 导入乙醇
python import_msds_to_db.py -f msds_乙醇无水 -c 64-17-5

REM 导入丙酮
python import_msds_to_db.py -f msds_丙酮 -c 67-64-1

echo 全部导入完成！
pause
```

### Python批量脚本

创建 `batch_import.py`：

```python
#!/usr/bin/env python3
from import_msds_to_db import import_msds_folder

# 定义要导入的数据列表
IMPORT_LIST = [
    {'folder': 'msds_甲苯', 'cas': '108-88-3'},
    {'folder': 'msds_乙醇无水', 'cas': '64-17-5'},
    {'folder': 'msds_丙酮', 'cas': '67-64-1'},
]

for item in IMPORT_LIST:
    print(f"\n导入 {item['folder']}...")
    success = import_msds_folder(item['folder'], item['cas'])
    
    if success:
        print(f"✓ {item['folder']} 导入成功")
    else:
        print(f"✗ {item['folder']} 导入失败")

print("\n批量导入完成！")
```

---

## ❓ 常见问题

### Q1: 提示"化学品不存在"

**A**: 需要先在`化学品`表中添加基本信息：

```sql
-- 添加化学品基本信息
INSERT INTO 化学品 (CAS号, 中文名, 英文名, 分子式) 
VALUES ('108-88-3', '甲苯', 'Toluene', 'C7H8');

-- 然后再导入MSDS
python import_msds_to_db.py -f msds_甲苯 -c 108-88-3
```

---

### Q2: 导入后如何更新数据？

**A**: 脚本支持自动更新，再次运行即可：

```bash
# 如果MSDS数据已存在，会自动更新
python import_msds_to_db.py -f msds_甲苯 -c 108-88-3
```

---

### Q3: 如何查看导入的数据？

**A**: 使用DataGrip或MySQL命令行：

```sql
-- 查看有多少化学品有MSDS
SELECT COUNT(*) FROM MSDS文档;

-- 查看每个MSDS有多少章节
SELECT 
    m.编号,
    p.中文名,
    COUNT(c.编号) AS 章节数
FROM MSDS文档 m
JOIN 化学品 p ON m.化学品编号 = p.编号
LEFT JOIN MSDS章节 c ON m.编号 = c.文档编号
GROUP BY m.编号, p.中文名;
```

---

### Q4: JSON数据格式不对怎么办？

**A**: 检查HTML文件是否完整，或修改`parse_html_content`函数：

```python
# 如果不需要结构化数据，可以简化
def parse_html_content(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    
    # 返回空JSON
    return text, '{}'
```

---

### Q5: 如何删除已导入的MSDS？

**A**: 删除会级联删除所有章节：

```sql
-- 删除特定化学品的MSDS（会自动删除所有章节）
DELETE FROM MSDS文档 
WHERE 化学品编号 = (SELECT 编号 FROM 化学品 WHERE CAS号 = '108-88-3');
```

---

## 🎯 最佳实践

### 1. 完整工作流

```
1. 爬取数据
   智能爬虫.bat → msds_甲苯/

2. 添加化学品基本信息（如果不存在）
   INSERT INTO 化学品 ...

3. 导入MSDS
   导入MSDS到数据库.bat

4. 验证数据
   SELECT * FROM MSDS章节 ...

5. 使用Web应用查询
   启动Web应用.bat → 浏览器访问
```

---

### 2. 数据维护

```sql
-- 定期检查数据完整性
SELECT 
    p.中文名,
    COUNT(DISTINCT c.章节序号) AS 已有章节数
FROM 化学品 p
JOIN MSDS文档 m ON p.编号 = m.化学品编号
JOIN MSDS章节 c ON m.编号 = c.文档编号
GROUP BY p.编号, p.中文名
HAVING 已有章节数 < 16;
```

---

### 3. 性能优化

```sql
-- 为常用查询添加索引（已在表结构中定义）
-- 全文索引
FULLTEXT INDEX 全文索引_内容 (章节标题, 内容)

-- 复合索引
UNIQUE KEY 唯一键_文档章节 (文档编号, 章节序号)
```

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `auto_scrape_msds.py` | 智能爬虫（第1步） |
| `import_msds_to_db.py` | 数据导入脚本（第2步） |
| `导入MSDS到数据库.bat` | 图形化导入工具 |
| `db/chinese/init_database.sql` | 数据库表结构定义 |
| `app.py` | Web应用（数据查询） |

---

## 🎊 总结

### 推荐流程

```
智能爬虫 → 导入数据库 → Web应用查询
   ↓            ↓              ↓
爬取HTML    解析入库      AI大模型调用
```

### 核心优势

✅ **自动化**：从爬取到入库，全程自动化  
✅ **结构化**：HTML转换为可查询的结构化数据  
✅ **集成性**：与法规、SOP等数据关联  
✅ **可扩展**：支持全文搜索、AI调用等高级功能

---

**开始使用吧！** 🚀

1. 双击：`智能爬虫.bat` → 爬取数据
2. 双击：`导入MSDS到数据库.bat` → 导入数据
3. 双击：`启动Web应用.bat` → 查询数据

就这么简单！

