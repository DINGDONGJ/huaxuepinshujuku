# 危险化学品MSDS数据库查询系统

## 📚 目录

- [系统概述](#系统概述)
- [系统架构](#系统架构)
- [核心功能原理](#核心功能原理)
  - [1. 爬虫系统原理](#1-爬虫系统原理)
  - [2. 搜索系统原理](#2-搜索系统原理)
  - [3. 法规智能匹配原理](#3-法规智能匹配原理)
  - [4. 法规内容索引原理](#4-法规内容索引原理)
- [数据库设计](#数据库设计)
- [安装部署](#安装部署)
- [使用教程](#使用教程)
- [API接口文档](#api接口文档)
- [项目统计](#项目统计)

---

## 系统概述

本系统是一个**全功能危险化学品安全数据管理平台**，集成了数据采集、存储、查询、法规合规性分析等功能，为化工企业EHS管理和科研机构提供专业的化学品安全信息查询服务。

### 核心特性

✅ **智能数据爬取** - 自动从合规化学网提取MSDS数据  
✅ **多维度搜索** - 支持中英文名、CAS号、别名模糊搜索  
✅ **实时自动补全** - 输入时即时显示匹配结果  
✅ **法规智能匹配** - 基于5层匹配逻辑自动推荐相关法规  
✅ **内容索引检索** - 475个法规文件全文索引  
✅ **现代化界面** - 响应式设计，支持移动端访问  

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                       用户界面层                              │
│        (index.html - 现代化Web界面 + 实时交互)               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      应用服务层                               │
│               (app.py - Flask REST API)                     │
│  ┌──────────────┬──────────────┬──────────────────────┐    │
│  │  搜索引擎    │  法规匹配    │   数据管理           │    │
│  │ (271-349行)  │ (645-936行)  │  (382-593行)         │    │
│  └──────────────┴──────────────┴──────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据处理层                               │
│  ┌──────────────────┬─────────────────────────────────┐    │
│  │   爬虫引擎        │   法规索引器                     │    │
│  │(scrape_to_json.py│(regulation_content_indexer.py)  │    │
│  │  43-376行)       │   (24-233行)                    │    │
│  └──────────────────┴─────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                               │
│  ┌──────────────┬──────────────────┬──────────────────┐    │
│  │ MySQL数据库  │  JSON文件存储    │  法规文档库      │    │
│  │  (4张表)     │   (253个文件)    │   (475个PDF)     │    │
│  └──────────────┴──────────────────┴──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心功能原理

### 1. 爬虫系统原理

#### 1.1 整体流程

爬虫系统采用**两阶段提取**策略：

**阶段1：化学品信息提取** (`scrape_to_json.py` 43-162行)

```python
# 核心函数：extract_chemical_info()
# 代码位置：scrape_to_json.py 43-162行
```

**执行步骤：**

1. **启动浏览器** (58-60行)
   ```python
   with sync_playwright() as p:
       browser = p.chromium.launch(headless=True)
       page = browser.new_page()
   ```

2. **访问目标页面** (64-66行)
   ```python
   page.goto(decrypt_url, timeout=30000)
   page.wait_for_timeout(1500)
   ```

3. **点击第一部分** (68-89行)
   - 尝试多种选择器定位元素
   - 选择器列表：`text=第一部分`, `text=化学品及企业标识`
   
4. **提取mid参数** (99-104行)
   ```python
   mid_match = re.search(r'[?&]mid=([^&]+)', current_url)
   if mid_match:
       mid = mid_match.group(1)
   ```

5. **解析HTML内容** (107-135行)
   - 查找 `class='maincondetail'` 的div标签
   - 提取标签-值对：
     - 中文名 (119-120行)
     - 英文名 (121-122行)
     - CAS号 (123-124行)
     - EC编号 (125-126行)
     - 分子式 (127-128行)
     - 别名 (129-134行) - 支持多种分隔符: `,，、|；;`

**阶段2：MSDS章节爬取** (`scrape_to_json.py` 198-266行)

```python
# 核心函数：scrape_msds_part()
# 代码位置：scrape_to_json.py 198-266行
```

**执行步骤：**

1. **构造URL** (201行)
   ```python
   url = f"http://www.hgmsds.com/weixin/msds-page-details?mid={mid}&type={part_num-1}&tid="
   ```
   注意：`type` 参数从0开始（第1部分=type 0）

2. **提取文本内容** (213-229行)
   - 优先查找 `class='maincontent'` 
   - 备用方案：查找所有 `class='maincondetail'`

3. **图片下载处理** (231-260行)
   - 只处理第2部分（危险性概述）和第14部分（运输信息）
   - 过滤logo、二维码等无关图片
   - 下载图片到本地 `images/` 目录
   - 排除最后一张图片（通常是二维码）

4. **图片元数据存储** (247-253行)
   ```python
   image_info = {
       "url": local_path,          # 本地路径
       "alt": img_alt,             # 图片描述
       "type": "ghs" or "transport", # 图片类型
       "original_url": img_src     # 原始URL
   }
   ```

#### 1.2 图片下载机制

**函数：** `download_image()` (165-196行)

**关键逻辑：**

1. **URL处理** (168-170行) - 相对路径转绝对路径
2. **文件命名** (178-180行) - 使用URL的MD5哈希（前12位）避免重复
3. **本地存储** (183-188行) - 保存到 `msds_json/images/` 目录

#### 1.3 数据导出与入库

**JSON导出** (`scrape_to_json.py` 324-375行)

数据结构：
```json
{
  "chemical_info": {
    "中文名": "...",
    "英文名": "...",
    "CAS号": "...",
    "分子式": "...",
    "EC编号": "..."
  },
  "aliases": ["别名1", "别名2"],
  "msds_meta": {
    "编制单位": "合规化学网",
    "编制日期": "2025-10-24",
    "编制依据": "GB/T 16483, GB/T 17519"
  },
  "msds_chapters": [
    {
      "章节序号": 1,
      "章节标题": "化学品及企业标识",
      "内容": "...",
      "图片": [...]  // 可选
    }
  ]
}
```

**数据库导入** (`scrape_to_json.py` 378-535行)

**事务处理流程：**

1. **检查化学品是否存在** (406-414行) - 通过CAS号或中文名
2. **插入/更新化学品** (416-450行)
3. **处理别名** (453-458行) - 先删除旧别名，再插入新别名
4. **处理MSDS文档** (461-491行)
5. **插入章节数据** (494-509行) - 包含图片JSON
6. **提交事务** (512行) - 成功则提交，失败则回滚

---

### 2. 搜索系统原理

#### 2.1 主搜索接口

**API路由：** `/api/search` (`app.py` 269-349行)

**搜索查询SQL** (283-294行)：

```sql
SELECT 编号 FROM 化学品 
WHERE 中文名 LIKE %keyword%
   OR 英文名 LIKE %keyword%
   OR CAS号 = keyword
   OR 编号 IN (
       SELECT 化学品编号 
       FROM 化学品别名 
       WHERE 别名 LIKE %keyword%
   )
LIMIT 1
```

**搜索优先级：**
1. 精确匹配 CAS号
2. 中文名模糊匹配
3. 英文名模糊匹配
4. 别名模糊匹配

**数据聚合查询** (306-337行)：

使用 `GROUP_CONCAT` 聚合别名：
```sql
SELECT 
    c.编号, c.CAS号, c.中文名, c.英文名, c.分子式,
    GROUP_CONCAT(a.别名 SEPARATOR '、') AS 所有别名
FROM 化学品 c
LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
WHERE c.编号 = ?
GROUP BY c.编号, c.CAS号, c.中文名, c.英文名, c.分子式
```

**MSDS章节查询** (323-336行)：
```sql
SELECT 
    s.章节序号, s.章节标题, s.内容, s.图片JSON,
    d.编制单位, d.编制依据, d.编制日期
FROM MSDS文档 d
JOIN MSDS章节 s ON d.编号 = s.文档编号
WHERE d.化学品编号 = ?
ORDER BY s.章节序号
```

#### 2.2 自动补全接口

**API路由：** `/api/autocomplete` (`app.py` 595-643行)

**智能排序SQL** (608-633行)：

```sql
SELECT DISTINCT 
    c.编号, c.CAS号, c.中文名, c.英文名
FROM 化学品 c
LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
WHERE c.中文名 LIKE %keyword%
   OR c.英文名 LIKE %keyword%
   OR c.CAS号 LIKE %keyword%
   OR a.别名 LIKE %keyword%
ORDER BY 
    CASE 
        WHEN c.中文名 = keyword THEN 1       -- 完全匹配
        WHEN c.中文名 LIKE keyword% THEN 2   -- 前缀匹配
        WHEN c.CAS号 = keyword THEN 3        -- CAS精确
        WHEN c.CAS号 LIKE keyword% THEN 4    -- CAS前缀
        ELSE 5                               -- 其他模糊匹配
    END,
    c.中文名
LIMIT 10
```

**排序优先级说明：**
- 优先级1：完全匹配（如搜索"甲醛"，完全匹配"甲醛"）
- 优先级2：前缀匹配（如搜索"甲"，匹配"甲醛"、"甲苯"等）
- 优先级3：CAS号精确匹配
- 优先级4：CAS号前缀匹配
- 优先级5：其他模糊匹配

#### 2.3 化学品列表接口

**API路由：** `/api/list` (`app.py` 351-380行)

**统计查询** (358-370行)：
```sql
SELECT 
    c.编号, c.CAS号, c.中文名, c.英文名,
    COUNT(DISTINCT s.编号) AS 章节数
FROM 化学品 c
LEFT JOIN MSDS文档 m ON c.编号 = m.化学品编号
LEFT JOIN MSDS章节 s ON m.编号 = s.文档编号
GROUP BY c.编号, c.CAS号, c.中文名, c.英文名
ORDER BY c.中文名
```

---

### 3. 法规智能匹配原理

#### 3.1 匹配架构

法规匹配采用**多层级智能匹配**策略，共5个匹配层次：

```
优先级1: 法规名录匹配 (regulation_catalog_mapping)
优先级2: GHS危险性匹配 (ghs_category_mapping)
优先级2: 运输分类匹配 (transport_class_mapping)
优先级2: 理化特性匹配 (flash_point, flammability)
优先级2: 毒理学匹配 (toxicity, aquatic_toxicity)
优先级3: 通用法规 (common_regulations)
优先级4: 内容智能匹配 (基于关键词索引)
```

**API路由：** `/api/regulations/<chemical_id>` (`app.py` 645-936行)

#### 3.2 第一层：法规名录匹配

**代码位置：** `app.py` 687-720行

**匹配逻辑：**

1. **从第15章提取法规信息** (688行)
   ```python
   chapter15 = next((ch for ch in chapters if ch['章节序号'] == 15), None)
   ```

2. **遍历法规配置** (693行)
   ```python
   for regulation_name, regulation_info in regulation_mapping['regulation_catalog_mapping'].items():
   ```

3. **检查法规名称** (695-696行)
   ```python
   clean_name = regulation_name.strip('《》')
   if clean_name in content:
   ```

4. **查找"列入"状态** (699-709行)
   - 分行查找
   - 在包含法规名称的行后5行内查找"列入"关键词
   - 确认该化学品确实列入该法规

**配置文件：** `regulation_mapping.json` 第2-50行

示例配置：
```json
"《危险化学品目录（2015年版）》": {
  "files": [
    "法律法规/危险化学品目录（2015版）.pdf"
  ],
  "priority": 1,
  "category": "法规名录"
}
```

#### 3.3 第二层：GHS危险性匹配

**代码位置：** `app.py` 722-742行

**匹配逻辑：**

1. **从第2章提取危险性信息** (722-723行)
   ```python
   chapter2 = next((ch for ch in chapters if ch['章节序号'] == 2), None)
   ```

2. **遍历GHS分类** (726行)
   ```python
   for ghs_name, ghs_info in regulation_mapping['ghs_category_mapping'].items():
   ```

3. **关键词匹配** (728-742行)
   - 获取关键词列表 (728行)
   - 逐个匹配关键词 (729-730行)
   - 添加匹配结果 (731-741行)

**配置文件：** `regulation_mapping.json` 第53-273行

支持的GHS分类（共20种）：
- 易燃液体、易燃气体、易燃固体
- 爆炸物、氧化性液体/固体/气体
- 自反应物质、自燃液体/固体、自热物质
- 遇水放出易燃气体、有机过氧化物
- 金属腐蚀物、急性毒性、皮肤腐蚀
- 严重眼损伤、呼吸道或皮肤致敏
- 生殖细胞致突变性、致癌性、生殖毒性
- 特异性靶器官毒性、吸入危害
- 对水生环境的危害、对臭氧层的危害

#### 3.4 第三层：运输分类匹配

**代码位置：** `app.py` 744-775行

**提取函数：** `extract_transport_class()` (82-120行)

**匹配步骤：**

1. **提取UN编号** (85-98行)
   ```python
   patterns = [
       r'UN\s*编号[：:]\s*(\d+)',
       r'联合国危险货物编号[：:]\s*(\d+)',
       r'UN\s+No\.\s*[：:]?\s*(\d+)'
   ]
   ```

2. **提取运输危险类别** (100-113行)
   ```python
   class_patterns = [
       r'运输危险类别[：:]\s*(\d+\.?\d*)',
       r'危险性类别[：:]\s*(\d+\.?\d*)',
       r'Class\s*[：:]?\s*(\d+\.?\d*)'
   ]
   ```

3. **检查海洋污染物** (115-118行)
   ```python
   if any(keyword in content for keyword in ['海洋污染物', 'Marine pollutant']):
       marine_pollutant = True
   ```

4. **匹配运输法规** (751-762行)
   ```python
   if transport_class in regulation_mapping['transport_class_mapping']:
       class_info = regulation_mapping['transport_class_mapping'][transport_class]
   ```

**配置文件：** `regulation_mapping.json` 第289-357行

支持的运输类别：
- 第1类：爆炸品
- 第2类：压缩气体和气体
- 第3类：易燃液体
- 第4类：易燃固体
- 第5类：氧化剂和有机过氧化物
- 第6类：有毒物质和感染性物质
- 第8类：腐蚀性物质

#### 3.5 第四层：理化特性匹配

**代码位置：** `app.py` 777-828行

**A. 闪点匹配**

**提取函数：** `extract_flash_point()` (122-138行)

```python
patterns = [
    r'闪点[：:]\s*(-?\d+\.?\d*)\s*[℃°C]',
    r'Flash\s+point\s*[：:]?\s*(-?\d+\.?\d*)\s*[℃°C]'
]
```

**范围匹配** (784-799行)：
```python
flash_point_mapping = {
    "low": {"max": 23, "name": "低闪点易燃液体"},
    "medium": {"min": 23, "max": 60, "name": "中闪点易燃液体"},
    "high": {"min": 60, "name": "高闪点可燃液体"}
}
```

**B. 易燃性匹配** (801-828行)

判断逻辑：
1. 检查内容是否包含"易燃"
2. 判断物态：
   - 液体/液态 → 易燃液体法规
   - 固体/固态/粉末 → 易燃固体法规

#### 3.6 第五层：毒理学匹配

**代码位置：** `app.py` 830-873行

**A. 急性毒性（LD50）匹配**

**提取函数：** `extract_ld50()` (140-157行)

```python
patterns = [
    r'LD50\s*[经纬]*口[^>]*?(\d+\.?\d*)\s*mg/kg',
    r'急性经口毒性.*?LD50[^>]*?(\d+\.?\d*)\s*mg/kg'
]
```

**毒性分级** (837-853行)：
```python
ld50_ranges = [
    {"max": 5, "name": "剧毒物质"},
    {"min": 5, "max": 50, "name": "高毒物质"},
    {"min": 50, "max": 300, "name": "中等毒性物质"}
]
```

**B. 水生生物毒性（LC50）匹配**

**提取函数：** `extract_aquatic_lc50()` (159-175行)

```python
patterns = [
    r'LC50.*?鱼.*?(\d+\.?\d*)\s*mg/L',
    r'对鱼类的急性毒性.*?LC50.*?(\d+\.?\d*)\s*mg/L'
]
```

**毒性分级** (857-873行)：
```python
lc50_ranges = [
    {"max": 1, "name": "对水生生物极毒"},
    {"min": 1, "max": 10, "name": "对水生生物高毒"}
]
```

#### 3.7 第六层：通用法规

**代码位置：** `app.py` 875-885行

**配置文件：** `regulation_mapping.json` 第276-287行

通用法规列表：
- 危险化学品安全管理条例
- 化学品安全技术说明书 内容和项目顺序
- 化学品安全标签编写规定
- 基于GHS的化学品标签规范
- 常用化学危险品贮存通则

#### 3.8 第七层：内容智能匹配

**代码位置：** `app.py` 887-915行

**关键词提取函数：** `extract_keywords_from_msds()` (177-254行)

**提取步骤：**

1. **化学品基本信息** (183-192行)
   - 化学品名称
   - CAS号

2. **第2章：危险性概述** (200-216行)
   - GHS分类关键词（易燃、有毒、腐蚀等）
   - 类别信息（类别1、类别2等）

3. **第9章：理化特性** (219-223行)
   - 物态关键词（液体、固体、气体）
   - 特性关键词（易燃、可燃）

4. **第11章：毒理学信息** (226-230行)
   - 毒性等级关键词（剧毒、高毒、中等毒性等）

5. **第14章：运输信息** (233-243行)
   - UN编号
   - 运输类别
   - 海洋污染物

6. **第15章：法规信息** (246-249行)
   - 法规名称（书名号内容）

**索引搜索** (898行)：
```python
content_matches = regulation_indexer.search_by_keywords(keywords, max_results=10)
```

**结果整合** (901-912行)：
- 避免重复添加已匹配的法规
- 设置优先级为4（最低）
- 保留匹配分数

#### 3.9 结果排序与分类

**排序** (918行)：
```python
matched_regulations.sort(key=lambda x: x['priority'])
```

**分类汇总** (921-926行)：
```python
regulations_by_category = {}
for reg in matched_regulations:
    category = reg['category']
    if category not in regulations_by_category:
        regulations_by_category[category] = []
    regulations_by_category[category].append(reg)
```

---

### 4. 法规内容索引原理

#### 4.1 索引构建

**类定义：** `RegulationContentIndexer` (`regulation_content_indexer.py` 12-233行)

**索引结构：**
```python
self.index = {
    'metadata': {},        # 文件元数据
    'keyword_index': {},   # 关键词倒排索引
    'stats': {}           # 统计信息
}
```

#### 4.2 索引构建流程

**主函数：** `build_index()` (24-42行)

1. **扫描MD文件** (29-31行)
   ```python
   md_files = list(Path(self.md_folder).rglob('*.md'))
   ```

2. **逐个索引文件** (33-37行)
   ```python
   for idx, md_path in enumerate(md_files, 1):
       self._index_file(md_path)
   ```

3. **保存索引** (40行)

#### 4.3 文件索引逻辑

**函数：** `_index_file()` (44-76行)

**处理步骤：**

1. **读取文件内容** (47-49行)

2. **生成PDF路径映射** (52-56行)
   ```python
   rel_path = os.path.relpath(md_path, self.md_folder)
   rel_path = rel_path.replace('\\', '/')  # 统一使用正斜杠
   pdf_path = rel_path.replace('.md', '.pdf')
   ```

3. **提取标题** (58行)
   ```python
   title = os.path.basename(md_path).replace('.md', '')
   ```

4. **存储元数据** (61-66行)
   ```python
   self.index['metadata'][pdf_path] = {
       'title': title,
       'md_path': str(md_path),
       'size': len(content),
       'category': self._get_category(rel_path)
   }
   ```

5. **建立倒排索引** (69-73行)
   ```python
   keywords = self._extract_keywords(content, title)
   for keyword in keywords:
       if keyword not in self.index['keyword_index']:
           self.index['keyword_index'][keyword] = []
       self.index['keyword_index'][keyword].append(pdf_path)
   ```

#### 4.4 关键词提取策略

**函数：** `_extract_keywords()` (78-156行)

**提取类别：**

1. **标题关键词** (83-98行)
   - 按空格、斜杠、冒号分割
   - 提取"第X部分"
   - 提取标准编号（GB、HG/T、SN/T）

2. **危险性关键词** (100-110行)
   ```python
   hazard_patterns = [
       r'(易燃|易爆|有毒|腐蚀|氧化|爆炸)',
       r'(急性毒性|慢性毒性|皮肤腐蚀)',
       r'(类别\s*[1-4A-E])'
   ]
   ```

3. **GHS分类关键词** (112-125行)
   - 29种GHS危险性分类

4. **运输分类关键词** (127-137行)
   ```python
   transport_patterns = [
       r'UN\s*(\d{4})',
       r'运输危险类别\s*[：:]\s*(\d)',
       r'(海洋污染物)'
   ]
   ```

5. **理化特性关键词** (139-142行)
   - 闪点、沸点、熔点、爆炸极限等

6. **法规名称关键词** (144-154行)
   ```python
   regulation_patterns = [
       r'《(.+?)》',              # 书名号内容
       r'GB\s*\d+[.\-\d]*',       # 国标
       r'HG/T\s*\d+',             # 行标
       r'SN/T\s*\d+'              # 进出口标准
   ]
   ```

#### 4.5 索引搜索算法

**函数：** `search_by_keywords()` (200-233行)

**搜索策略：**

1. **精确匹配** (206-209行)
   ```python
   if keyword in self.index['keyword_index']:
       for pdf_path in self.index['keyword_index'][keyword]:
           file_scores[pdf_path] += 1  # 精确匹配+1分
   ```

2. **模糊匹配** (211-215行)
   ```python
   for idx_keyword in self.index['keyword_index']:
       if keyword in idx_keyword or idx_keyword in keyword:
           for pdf_path in self.index['keyword_index'][idx_keyword]:
               file_scores[pdf_path] += 0.5  # 模糊匹配+0.5分
   ```

3. **分数排序** (218行)
   ```python
   sorted_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)
   ```

4. **过滤结果** (221-232行)
   - 只返回分数≥1的结果
   - 限制最多返回 `max_results` 个结果

---

### 5. PDF自动搜索化学品功能

#### 5.1 功能概述

当用户在MSDS第15章（法规信息）中点击法规PDF链接时，系统会自动在PDF中搜索当前化学品的**CAS号、中文名称和所有别名**，并高亮显示匹配结果，帮助用户快速定位化学品相关内容。

#### 5.2 实现架构

```
用户搜索化学品
    ↓
系统保存化学品信息（CAS号、名称、别名）
    ↓
用户查看第15章法规信息
    ↓
点击法规PDF链接
    ↓
打开PDF查看器 + 异步执行智能搜索
    ↓
按优先级搜索：CAS号 → 名称 → 别名
    ↓
显示所有匹配项 + 自动跳转第一个匹配页
```

#### 5.3 关键实现步骤

**步骤1：保存化学品信息** (`index.html` 2672-2677行)

当用户搜索到化学品后，系统立即保存化学品信息到全局变量：

```javascript
// 保存当前化学品信息供PDF搜索使用
currentChemicalInfo = {
    cas: basic.CAS号 || '',          // "50-00-0"
    name: basic.中文名 || '',         // "甲醛"
    aliases: basic.所有别名 || ''     // "蚁醛、福尔马林"
};
```

**全局变量定义** (`index.html` 4850-4855行)：
```javascript
let currentChemicalInfo = {
    cas: '',
    name: '',
    aliases: ''
};
```

**步骤2：渲染可点击的法规链接** (`index.html` 4093-4100行)

在第15章中，将法规名称渲染为可点击链接：

```javascript
// 可点击的法规名称 - 自动搜索当前化学品（包括CAS号、名称、别名）
html += `<div class="msds-field-label regulation-link" 
              style="margin-top: 10px; margin-bottom: 8px; cursor: pointer;" 
              onclick="openPdfViewerWithSearch('${pdfFile}', '${escapedLine}')"
              title="点击查看PDF文件并自动搜索该化学品（含别名）">
            ${line} <i class="fas fa-file-pdf"></i>
        </div>`;
```

**显示效果：**
- 法规名称带有PDF图标 📄
- 鼠标悬停显示提示："点击查看PDF文件并自动搜索该化学品（含别名）"
- 点击触发 `openPdfViewerWithSearch()` 函数

**步骤3：打开PDF并准备搜索关键词** (`index.html` 4871-4892行)

```javascript
async function openPdfViewerWithSearch(pdfFileName, title = '法规文件') {
    // 构建分组的搜索关键词对象
    const keywordGroups = {
        cas: currentChemicalInfo.cas || '',
        name: currentChemicalInfo.name || '',
        aliases: []
    };
    
    if (currentChemicalInfo.aliases) {
        // 别名可能是多个，用逗号、分号或顿号分隔
        keywordGroups.aliases = currentChemicalInfo.aliases
            .split(/[,，;；、\s]+/)  // 支持多种分隔符
            .filter(a => {
                const trimmed = a.trim();
                // 过滤空字符串和"-"（表示无别名）
                return trimmed && trimmed !== '-';
            });
    }
    
    // 调用PDF查看器，传入分组的关键词对象
    await openPdfViewer(pdfFileName, 1, title, keywordGroups);
}
```

**关键词分组示例：**
```javascript
// 对于"甲醛"
keywordGroups = {
    cas: "50-00-0",
    name: "甲醛",
    aliases: ["蚁醛", "福尔马林", "甲醛溶液"]
}
```

**步骤4：加载PDF并异步搜索** (`index.html` 4894-4949行)

```javascript
async function openPdfViewer(pdfFileName, pageNumber = 1, title = '法规文件', searchKeyword = '') {
    try {
        showNotification('正在加载PDF文件...', 'info');
        
        // 加载PDF（配置CMap支持中文）
        const loadingTask = pdfjsLib.getDocument({
            url: pdfPath,
            cMapUrl: 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/',
            cMapPacked: true
        });
        pdfDoc = await loadingTask.promise;
        totalPagesCount = pdfDoc.numPages;
        
        // 保存搜索关键词
        currentSearchKeyword = searchKeyword;
        
        // 始终显示第1页（不等待搜索）
        currentPageNum = 1;
        await renderPage(currentPageNum);
        
        // 立即显示查看器（优化UX：不阻塞界面）
        document.getElementById('pdfViewerOverlay').classList.add('show');
        showNotification('PDF加载成功', 'success');
        
        // 如果提供了搜索关键词，在后台异步执行搜索
        if (searchKeyword) {
            setTimeout(async () => {
                await searchInPdf(searchKeyword);  // ← 核心搜索函数
            }, 50);  // 延迟50ms，让PDF先显示
        }
    } catch (error) {
        showNotification('PDF加载失败：' + error.message, 'error');
    }
}
```

**UX优化要点：**
- PDF立即显示，不等待搜索完成
- 搜索在后台异步执行
- 用户可以立即浏览PDF，同时系统在后台搜索

**步骤5：智能搜索算法** (`index.html` 5056-5200行)

```javascript
async function searchInPdf(keywords) {
    if (!pdfDoc || !keywords) return 0;
    
    searchResults = [];
    
    // 构建搜索队列：按优先级排列
    const searchQueue = [];
    
    if (typeof keywords === 'object' && !Array.isArray(keywords)) {
        // 1. CAS号（包含匹配）- 最高优先级
        if (keywords.cas && keywords.cas.trim()) {
            searchQueue.push({
                keyword: keywords.cas.trim(),
                matchType: 'contains',  // 包含匹配（如"50-00-0"可匹配"CAS: 50-00-0"）
                type: 'CAS号'
            });
        }
        
        // 2. 化学品名称（全字匹配）
        if (keywords.name && keywords.name.trim()) {
            searchQueue.push({
                keyword: keywords.name.trim(),
                matchType: 'exact',  // 精确匹配
                type: '化学品名称'
            });
        }
        
        // 3. 别名（全字匹配）
        if (keywords.aliases && keywords.aliases.length > 0) {
            keywords.aliases.forEach(alias => {
                if (alias && alias.trim()) {
                    searchQueue.push({
                        keyword: alias.trim(),
                        matchType: 'exact',
                        type: '别名'
                    });
                }
            });
        }
    }
    
    // 配置参数
    const BATCH_SIZE = hasCache ? 100 : 50;  // 有缓存时加大批次
    
    // 按优先级分组搜索
    for (const group of ['CAS号', '化学品名称', '别名', '关键词']) {
        const groupKeywords = searchQueue.filter(k => k.type === group);
        if (groupKeywords.length === 0) continue;
        
        // 分批并行处理（性能优化）
        for (let startPage = 1; startPage <= totalPagesCount; startPage += BATCH_SIZE) {
            const endPage = Math.min(startPage + BATCH_SIZE - 1, totalPagesCount);
            
            // 创建并行任务数组
            const tasks = [];
            for (let pageNum = startPage; pageNum <= endPage; pageNum++) {
                tasks.push(searchPageForKeywords(pageNum, groupKeywords, group));
            }
            
            // 并行执行这一批搜索
            await Promise.all(tasks);
            
            // 更新进度
            searchedPages = endPage;
            const progress = Math.round((searchedPages / totalPagesCount) * 100);
            searchingNotif.textContent = `搜索进度：${searchedPages}/${totalPagesCount} 页 (${progress}%)`;
        }
        
        // 如果找到匹配，跳转到第一个匹配项
        if (searchResults.length > 0 && firstPage === 0) {
            firstPage = searchResults[0].pageNum;
            break;  // 找到后立即停止搜索其他组
        }
    }
    
    // 显示搜索结果
    displaySearchResults();
    
    // 自动跳转到第一个匹配页
    if (firstPage > 0) {
        await goToPage(firstPage);
    }
    
    return searchResults.length;
}
```

**搜索策略说明：**

1. **优先级搜索**：
   - 优先级1：CAS号（包含匹配）
   - 优先级2：化学品名称（精确匹配）
   - 优先级3：别名（精确匹配）
   - 找到任意一个匹配后立即停止搜索其他组

2. **匹配类型**：
   - **包含匹配**（contains）：适用于CAS号，因为PDF中可能写成"CAS No.: 50-00-0"
   - **精确匹配**（exact）：适用于名称和别名，避免误匹配（如"甲醛"不会匹配"聚甲醛"）

3. **性能优化**：
   - **文本缓存**：首次搜索后缓存每页文本，后续搜索无需重复提取
   - **批量并行**：50-100页为一批并行搜索，大幅提升速度
   - **早停机制**：找到匹配后立即停止搜索其他优先级组

4. **搜索结果展示**：
   - 侧边栏显示所有匹配项（页码、关键词类型、上下文）
   - 自动跳转到第一个匹配页
   - 在PDF页面上高亮显示匹配内容

#### 5.4 使用示例

**场景：用户搜索"甲醛"**

1. 系统保存化学品信息：
   ```javascript
   currentChemicalInfo = {
       cas: "50-00-0",
       name: "甲醛",
       aliases: "蚁醛、福尔马林、甲醛溶液"
   }
   ```

2. 用户查看第15章，看到法规链接：
   ```
   《危险化学品目录（2015版）》 📄
   ```

3. 点击链接，系统：
   - 打开PDF查看器，显示第1页
   - 后台搜索4个关键词：
     - "50-00-0" (CAS号，包含匹配)
     - "甲醛" (名称，精确匹配)
     - "蚁醛" (别名1，精确匹配)
     - "福尔马林" (别名2，精确匹配)

4. 搜索结果：
   ```
   ✅ 在第58页找到 "50-00-0" (CAS号)
   ✅ 在第58页找到 "甲醛" (化学品名称)
   ✅ 在第195页找到 "福尔马林" (别名)
   
   → 自动跳转到第58页（第一个匹配）
   → 侧边栏显示3个匹配项
   ```

#### 5.5 代码位置汇总

| 功能模块 | 文件 | 行数 | 说明 |
|---------|------|------|------|
| 全局变量定义 | `index.html` | 4850-4855 | 定义 `currentChemicalInfo` |
| 保存化学品信息 | `index.html` | 2672-2677 | 搜索结果展示时保存 |
| 渲染可点击链接 | `index.html` | 4093-4100 | 第15章法规链接渲染 |
| 打开PDF入口 | `index.html` | 4871-4892 | `openPdfViewerWithSearch()` |
| PDF加载函数 | `index.html` | 4894-4949 | `openPdfViewer()` |
| 智能搜索算法 | `index.html` | 5056-5200 | `searchInPdf()` |

#### 5.6 技术亮点

1. **用户体验优化**
   - PDF立即显示，搜索不阻塞界面
   - 实时进度提示
   - 自动跳转到第一个匹配项
   - 支持侧边栏浏览所有匹配结果

2. **性能优化**
   - 文本缓存机制（避免重复提取）
   - 批量并行搜索（50-100页/批）
   - 早停机制（找到即停）
   - 智能缓存策略（Map结构存储）

3. **智能匹配**
   - 优先级搜索（CAS号 > 名称 > 别名）
   - 双重匹配模式（包含/精确）
   - 自动过滤无效别名（空字符串、"-"）
   - 支持多种别名分隔符

4. **健壮性**
   - 异常处理机制
   - 兼容旧格式搜索
   - 支持中文PDF（CMap配置）
   - 避免重复搜索同一组

---

## 数据库设计

### 表结构

#### 1. 化学品表 (28-42行)

```sql
CREATE TABLE 化学品 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT,
    CAS号 VARCHAR(32) UNIQUE,
    中文名 VARCHAR(256) NOT NULL,
    英文名 VARCHAR(256),
    分子式 VARCHAR(64),
    EC编号 VARCHAR(64),
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX 索引_CAS号 (CAS号),
    INDEX 索引_中文名 (中文名(191)),
    INDEX 索引_英文名 (英文名(191)),
    FULLTEXT INDEX 全文索引_名称 (中文名, 英文名)
)
```

**索引说明：**
- `索引_CAS号`：加速CAS号查询
- `索引_中文名`、`索引_英文名`：加速名称模糊查询
- `全文索引_名称`：支持全文检索

#### 2. 化学品别名表 (47-57行)

```sql
CREATE TABLE 化学品别名 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT,
    化学品编号 BIGINT NOT NULL,
    别名 VARCHAR(256) NOT NULL,
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX 索引_化学品 (化学品编号),
    FULLTEXT INDEX 全文索引_别名 (别名),
    CONSTRAINT 外键_别名_化学品 FOREIGN KEY (化学品编号) 
        REFERENCES 化学品(编号) ON DELETE CASCADE
)
```

**级联删除：**当化学品被删除时，其所有别名自动删除。

#### 3. MSDS文档表 (62-74行)

```sql
CREATE TABLE MSDS文档 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT,
    化学品编号 BIGINT NOT NULL UNIQUE,  -- 一对一关系
    编制单位 VARCHAR(256),
    编制依据 VARCHAR(256),
    编制日期 DATE,
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX 索引_化学品 (化学品编号),
    CONSTRAINT 外键_MSDS_化学品 FOREIGN KEY (化学品编号) 
        REFERENCES 化学品(编号) ON DELETE CASCADE
)
```

**关系说明：**化学品与MSDS文档为一对一关系。

#### 4. MSDS章节表 (79-94行)

```sql
CREATE TABLE MSDS章节 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT,
    文档编号 BIGINT NOT NULL,
    章节序号 TINYINT NOT NULL,  -- 1-16
    章节标题 VARCHAR(256) NOT NULL,
    内容 LONGTEXT,
    图片JSON JSON,  -- 存储图片元数据
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY 唯一键_文档章节 (文档编号, 章节序号),
    INDEX 索引_章节序号 (章节序号),
    FULLTEXT INDEX 全文索引_内容 (章节标题, 内容),
    CONSTRAINT 外键_章节_文档 FOREIGN KEY (文档编号) 
        REFERENCES MSDS文档(编号) ON DELETE CASCADE
)
```

**图片JSON格式：**
```json
[
  {
    "url": "images/abc123.jpg",
    "alt": "GHS象形图",
    "type": "ghs",
    "original_url": "http://..."
  }
]
```

### 存储过程

**查询存储过程** (106-155行)

```sql
CALL 查询化学品('甲醛');
CALL 查询化学品('50-00-0');
CALL 查询化学品('Formaldehyde');
```

---

## 安装部署

### 环境要求

- **Python**: 3.7+
- **MySQL**: 8.0+
- **浏览器**: Chrome/Edge（用于爬虫）
- **操作系统**: Windows/Linux/MacOS

### 安装步骤

#### 1. 安装Python依赖

**方式A：使用批处理文件（Windows）**
```batch
# 双击运行
install_deps.bat
```

**方式B：手动安装**
```bash
pip install flask pymysql playwright beautifulsoup4 requests

# 安装Playwright浏览器
python -m playwright install chromium
```

**依赖说明：**
- `flask`: Web框架
- `pymysql`: MySQL数据库驱动
- `playwright`: 浏览器自动化（用于爬虫）
- `beautifulsoup4`: HTML解析
- `requests`: HTTP请求

#### 2. 配置MySQL数据库

**创建数据库：**
```bash
# 登录MySQL
mysql -u root -p

# 执行初始化脚本
source init_simple_db.sql
```

或使用MySQL客户端工具（如Navicat、DBeaver）导入 `init_simple_db.sql`

**修改数据库密码：**

编辑 `app.py` 第34-40行：
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',  # ← 修改为你的MySQL密码
    'database': '危化品简化数据库',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
```

#### 3. 构建法规索引（可选但推荐）

```bash
python regulation_content_indexer.py
```

**说明：**
- 首次运行需要3-5分钟
- 生成 `regulation_content_index.json` 文件（约2MB）
- 如果跳过此步骤，法规内容匹配功能将不可用

---

## 使用教程

### 1. 启动Web应用

**方式A：使用批处理文件（Windows）**
```batch
# 双击运行
start_web.bat
```

**方式B：命令行启动**
```bash
python app.py
```

**访问地址：**
```
http://localhost:5001
```

### 2. 搜索化学品

#### 2.1 基础搜索

在搜索框输入以下任意信息：
- **中文名**：甲醛、乙醇、硫酸
- **英文名**：Formaldehyde、Ethanol
- **CAS号**：50-00-0、64-17-5
- **别名**：蚁醛、酒精

**自动补全：**
- 输入2个字符后，系统自动显示匹配结果
- 使用方向键上下选择
- 按 `Enter` 或鼠标点击确认

#### 2.2 查看MSDS

搜索结果展示：
1. **化学品基本信息**
   - 中文名、英文名
   - CAS号、EC编号、分子式
   - 所有别名

2. **MSDS 16个章节**
   - 章节1：化学品及企业标识
   - 章节2：危险性概述（含GHS象形图）
   - 章节3：成分/组成信息
   - 章节4：急救措施
   - 章节5：消防措施
   - 章节6：泄漏应急处理
   - 章节7：操作处置与储存
   - 章节8：接触控制/个体防护
   - 章节9：理化特性
   - 章节10：稳定性和反应性
   - 章节11：毒理学信息
   - 章节12：生态学信息
   - 章节13：废弃处置
   - 章节14：运输信息（含运输标签）
   - 章节15：法规信息
   - 章节16：其他信息

#### 2.3 查看相关法规

点击"查看相关法规"按钮，系统自动分析并推荐法规：

**法规分类：**
- 🏛️ **法规名录**：危险化学品目录、重点监管名录
- ⚠️ **GHS标准**：易燃液体、急性毒性、皮肤腐蚀等
- 🚚 **运输标准**：UN分类、危险货物包装
- 🧪 **测试标准**：闪点测定、毒性试验
- 📜 **通用法规**：安全管理条例、MSDS编写规范
- 💡 **内容推荐**：基于内容相似度推荐

**操作：**
- 点击法规名称查看PDF（需要PDF文件存在）
- 查看匹配原因说明
- 按分类浏览

### 3. 导入化学品数据

#### 3.1 从JSON导入

1. 点击"导入数据"按钮
2. 选择JSON文件（必须符合系统格式）
3. 点击"上传并导入"
4. 等待导入完成

**JSON格式要求：** 参见第1.3节"数据导出与入库"

#### 3.2 使用爬虫采集

**方式A：使用批处理文件（Windows）**
```batch
# 双击运行
run_scraper.bat

# 选择模式
[1] 仅保存JSON
[2] 爬取并导入数据库
```

**方式B：命令行**

```bash
# 仅保存JSON
python scrape_to_json.py "http://www.hgmsds.com/msds/show?decrypt=xxx"

# 直接导入数据库
python scrape_to_json.py "http://www.hgmsds.com/msds/show?decrypt=xxx" --import

# 指定数据库密码
python scrape_to_json.py "URL" --import --password yourpass

# 自定义输出目录
python scrape_to_json.py "URL" --output my_data
```

**获取URL：**
1. 访问 http://www.hgmsds.com
2. 搜索化学品
3. 点击查看MSDS
4. 复制完整URL（包含decrypt参数）

**爬取过程：**
```
========================================================
🔍 正在分析链接...
========================================================
✅ 化学品名称: 甲醛
✅ CAS号: 50-00-0
✅ MID: 123456

========================================================
📥 开始爬取MSDS数据...
========================================================
正在爬取: 第1部分 - 化学品及企业标识... ✅
正在爬取: 第2部分 - 危险性概述... ✅ (3张图片)
...
正在爬取: 第16部分 - 其他信息... ✅

========================================================
💾 正在保存JSON文件...
========================================================
✅ JSON文件已保存: msds_json/甲醛_50-00-0.json

🎉 爬取完成！
```

### 4. 管理化学品

#### 4.1 查看化学品列表

界面自动加载所有化学品列表，显示：
- 化学品名称
- CAS号
- MSDS章节完整度

#### 4.2 删除化学品

1. 搜索要删除的化学品
2. 点击"删除"按钮
3. 确认删除
4. 系统自动删除：
   - 化学品基本信息
   - 所有别名
   - MSDS文档
   - 所有章节数据

**注意：**删除操作不可恢复！

---

## API接口文档

### 基础信息

- **Base URL**: `http://localhost:5001`
- **Content-Type**: `application/json`
- **字符编码**: `UTF-8`

### 接口列表

#### 1. 搜索化学品

**接口：** `POST /api/search`

**代码位置：** `app.py` 269-349行

**请求体：**
```json
{
  "keyword": "甲醛"
}
```

**成功响应：**
```json
{
  "basic_info": {
    "编号": 1,
    "CAS号": "50-00-0",
    "中文名": "甲醛",
    "英文名": "Formaldehyde",
    "分子式": "CH2O",
    "所有别名": "蚁醛、甲醛溶液"
  },
  "msds_chapters": [
    {
      "章节序号": 1,
      "章节标题": "化学品及企业标识",
      "内容": "...",
      "图片JSON": null,
      "编制单位": "合规化学网",
      "编制依据": "GB/T 16483",
      "编制日期": "2025-10-24"
    }
  ]
}
```

**错误响应：**
```json
{
  "error": "未找到该化学品"
}
```

#### 2. 自动补全

**接口：** `GET /api/autocomplete?keyword=甲`

**代码位置：** `app.py` 595-643行

**成功响应：**
```json
{
  "suggestions": [
    {
      "编号": 1,
      "CAS号": "50-00-0",
      "中文名": "甲醛",
      "英文名": "Formaldehyde"
    },
    {
      "编号": 2,
      "CAS号": "108-88-3",
      "中文名": "甲苯",
      "英文名": "Toluene"
    }
  ]
}
```

#### 3. 化学品列表

**接口：** `GET /api/list`

**代码位置：** `app.py` 351-380行

**成功响应：**
```json
{
  "chemicals": [
    {
      "编号": 1,
      "CAS号": "50-00-0",
      "中文名": "甲醛",
      "英文名": "Formaldehyde",
      "章节数": 16
    }
  ]
}
```

#### 4. 获取相关法规

**接口：** `GET /api/regulations/<chemical_id>`

**代码位置：** `app.py` 645-936行

**示例：** `GET /api/regulations/1`

**成功响应：**
```json
{
  "chemical": {
    "编号": 1,
    "CAS号": "50-00-0",
    "中文名": "甲醛",
    "英文名": "Formaldehyde"
  },
  "total": 15,
  "regulations": [
    {
      "file": "法律法规/危险化学品目录（2015版）.pdf",
      "name": "危险化学品目录（2015版）",
      "reason": "MSDS数据显示可能涉及《危险化学品目录（2015年版）》",
      "priority": 1,
      "category": "法规名录"
    }
  ],
  "by_category": {
    "法规名录": [...],
    "GHS标准": [...],
    "运输标准": [...]
  }
}
```

#### 5. 导入JSON数据

**接口：** `POST /api/import`

**代码位置：** `app.py` 382-537行

**请求：** `multipart/form-data`

**请求参数：**
- `file`: JSON文件

**成功响应：**
```json
{
  "success": true,
  "message": "成功导入化学品: 甲醛",
  "data": {
    "化学品ID": 1,
    "化学品名称": "甲醛",
    "CAS号": "50-00-0",
    "章节数": 16,
    "别名数": 2
  }
}
```

#### 6. 删除化学品

**接口：** `POST /api/delete`

**代码位置：** `app.py` 539-593行

**请求体：**
```json
{
  "chemical_id": 1
}
```

**成功响应：**
```json
{
  "success": true,
  "message": "成功删除化学品: 甲醛",
  "data": {
    "化学品名称": "甲醛",
    "CAS号": "50-00-0"
  }
}
```

#### 7. 访问PDF文件

**接口：** `GET /regulation-pdf/<path:filepath>`

**代码位置：** `app.py` 938-946行

**示例：** `GET /regulation-pdf/国家标准/化学品安全技术说明书 内容和项目顺序.pdf`

---

## 项目统计

### 代码统计

| 文件 | 行数 | 功能 |
|------|------|------|
| `app.py` | 964 | Flask Web应用 |
| `scrape_to_json.py` | 613 | 爬虫系统 |
| `regulation_content_indexer.py` | 244 | 法规索引器 |
| `init_simple_db.sql` | 167 | 数据库初始化 |
| `index.html` | 5901 | 前端界面 |
| **总计** | **7889** | |

### 数据统计

| 类型 | 数量 |
|------|------|
| 化学品MSDS | 253个 |
| 法规PDF文件 | 475个 |
| 法规MD文件 | 474个 |
| 数据库表 | 4张 |
| API接口 | 8个 |
| 批处理脚本 | 3个 |

### 法规文档分类

| 分类 | 数量 |
|------|------|
| 国家标准 | 224个 |
| 行业标准 | 86个 |
| 法律法规 | 160个 |
| 团体标准 | 5个 |

### GHS分类支持

系统支持完整的29种GHS危险性分类：

**物理危害（17种）：**
- 爆炸物、易燃气体、气溶胶、氧化性气体
- 加压气体、易燃液体、易燃固体
- 自反应物质、自燃液体、自燃固体
- 自热物质、遇水放出易燃气体
- 氧化性液体、氧化性固体、有机过氧化物
- 金属腐蚀物、退敏爆炸物

**健康危害（10种）：**
- 急性毒性、皮肤腐蚀/刺激
- 严重眼损伤/眼刺激、呼吸道或皮肤致敏
- 生殖细胞致突变性、致癌性、生殖毒性
- 特异性靶器官毒性-一次接触
- 特异性靶器官毒性-反复接触
- 吸入危害

**环境危害（2种）：**
- 对水生环境的危害
- 对臭氧层的危害

---

## 常见问题

### Q1: 爬虫启动失败

**现象：** 提示 `playwright not found`

**解决：**
```bash
python -m playwright install chromium
```

### Q2: 数据库连接失败

**现象：** `Can't connect to MySQL server`

**检查：**
1. MySQL服务是否启动
2. 密码是否正确（`app.py` 第36行）
3. 数据库名称是否正确

### Q3: 法规内容匹配不工作

**现象：** 只显示前3层匹配，没有内容推荐

**解决：**
```bash
python regulation_content_indexer.py
```

### Q4: 中文乱码

**检查：**
1. 数据库字符集是否为 `utf8mb4`
2. 文件编码是否为 `UTF-8`
3. MySQL连接是否指定 `charset='utf8mb4'`

---

## 许可证

本项目仅供学习和研究使用。

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- **项目位置**: `C:\Users\Administrator.DESKTOP-URBQKM0\Desktop\huaxuepinshujuku`
- **数据库**: 危化品简化数据库
- **访问地址**: http://localhost:5001

---

**最后更新**: 2025-10-24  
**版本**: 1.0  
**作者**: Chemical Safety Database Team

