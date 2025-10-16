# 危化品智能数据库系统 🧪

> 一个功能完善、性能卓越的危险化学品信息管理与查询系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![PDF.js](https://img.shields.io/badge/PDF.js-3.11-red.svg)](https://mozilla.github.io/pdf.js/)

---

## 📋 目录

- [项目简介](#项目简介)
- [核心功能](#核心功能)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [二次开发指南](#二次开发指南)
- [性能优化](#性能优化)
- [常见问题](#常见问题)
- [技术栈](#技术栈)

---

## 🎯 项目简介

这是一个专业的危险化学品信息管理系统，集成了**MSDS数据管理**、**法规文件检索**、**智能爬虫采集**等功能。系统经过深度性能优化，提供流畅的用户体验。

### 适用场景
- 🏭 **企业安全管理**：快速查询化学品安全信息
- 📚 **科研教学**：查阅化学品的理化性质和安全数据
- 🔍 **合规检查**：查询化学品在各类法规中的管控状态
- 📊 **数据分析**：批量处理和分析化学品数据

### 核心优势
- ⚡ **极速响应**：PDF秒开，搜索速度提升10倍+
- 🎯 **智能搜索**：支持CAS号、化学品名称、别名多维度搜索
- 💾 **智能缓存**：文本内容自动缓存，重复搜索飞快
- 📱 **现代UI**：美观的渐变设计，流畅的动画效果
- 🔧 **易于扩展**：模块化设计，方便二次开发

---

## 🚀 核心功能

### 1. 化学品信息查询
- **多维度搜索**：支持CAS号、中文名、英文名、分子式搜索
- **详细信息展示**：理化性质、危险特性、安全措施等16个板块
- **图片支持**：MSDS中的表格、图表以图片形式展示
- **别名管理**：自动识别和搜索化学品的多个别名

### 2. PDF法规文档检索 ⭐
#### 核心特性
- **秒开PDF**：优化后的PDF加载速度提升60-80%
- **智能搜索**：
  - CAS号：包含匹配
  - 化学品名称：全字匹配
  - 别名：全字匹配
- **搜索缓存**：
  - 首次搜索：建立文本缓存（~15秒/800页）
  - 后续搜索：使用缓存，速度提升**10-20倍**（~1.5秒）
- **分组显示**：搜索结果按类型分组，可展开/收起
- **实时进度**：显示搜索进度和缓存状态

#### 支持的法规文档
- 危险化学品目录
- 重点监管的危险化学品名录
- 易制爆危险化学品名录
- 高毒物品目录
- 中国严格限制的有毒化学品名录
- ...等10+种法规文件

### 3. 智能爬虫系统
- **自动爬取**：从化工网站自动爬取MSDS数据
- **结构化存储**：解析HTML，提取关键信息为JSON
- **图片处理**：自动下载和保存MSDS中的图片
- **批量导入**：支持批量爬取和导入数据库

### 4. 数据管理
- **JSON格式存储**：灵活的MSDS数据格式
- **数据库持久化**：MySQL存储，支持复杂查询
- **数据导入导出**：支持JSON文件导入数据库
- **样例数据**：提供多个化学品的完整MSDS数据

---

## 🏗️ 系统架构

```
危化品智能数据库系统
│
├── 前端层 (Frontend)
│   ├── HTML/CSS/JavaScript
│   ├── PDF.js (PDF渲染引擎)
│   ├── 智能缓存系统
│   └── 响应式UI设计
│
├── 后端层 (Backend)
│   ├── Flask Web框架
│   ├── RESTful API接口
│   ├── 数据库连接池
│   └── 文件服务
│
├── 数据层 (Data)
│   ├── MySQL 8.0+ 数据库
│   ├── JSON数据文件
│   └── PDF法规文档
│
└── 工具层 (Tools)
    ├── 网页爬虫 (Playwright)
    ├── PDF分析工具
    └── 数据导入脚本
```

### 核心技术架构
- **前后端分离**：Flask提供API，前端异步调用
- **缓存优化**：浏览器端智能文本缓存
- **并行处理**：批量并行搜索，充分利用CPU
- **Worker优化**：PDF.js Web Worker，不阻塞主线程

---

## 🎬 快速开始

### 环境要求
- **Python**：3.8 或更高版本
- **MySQL**：8.0 或更高版本
- **浏览器**：Chrome/Edge/Firefox（推荐Chrome）
- **操作系统**：Windows/Linux/macOS

### 安装步骤

#### 1. 安装MySQL数据库
1. 下载并安装MySQL 8.0+
2. 创建数据库：
```sql
CREATE DATABASE 危化品简化数据库 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 2. 初始化数据库
在MySQL中执行初始化脚本：
```bash
mysql -u root -p 危化品简化数据库 < init_simple_db.sql
```

可选：导入样例数据
```bash
mysql -u root -p 危化品简化数据库 < sample_data.sql
```

#### 3. 安装Python依赖
**方法A：使用批处理文件（Windows推荐）**
```bash
双击运行 install_deps.bat
```

**方法B：手动安装**
```bash
pip install -r requirements.txt
```

依赖包包括：
- Flask：Web框架
- PyMySQL：MySQL数据库驱动
- Playwright：网页爬虫
- BeautifulSoup4：HTML解析

#### 4. 配置数据库连接
编辑 `app.py`，修改数据库配置：
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '你的密码',  # 修改为你的MySQL密码
    'database': '危化品简化数据库',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
```

#### 5. 启动应用
**方法A：使用批处理文件（Windows推荐）**
```bash
双击运行 start_web.bat
```

**方法B：手动启动**
```bash
python app.py
```

#### 6. 访问系统
打开浏览器访问：`http://localhost:5000`

---

## 📖 使用指南

### 1. 化学品查询

#### 基本搜索
1. 在搜索框输入化学品信息（CAS号、名称、分子式等）
2. 点击"搜索"按钮或按Enter键
3. 系统返回匹配的化学品列表
4. 点击化学品卡片查看详细信息

#### 高级技巧
- **精确搜索**：输入完整CAS号（如 `64-17-5`）
- **模糊搜索**：输入部分名称（如 `甲`）
- **英文搜索**：输入英文名（如 `Ethanol`）
- **分子式搜索**：输入分子式（如 `C2H6O`）

### 2. PDF法规查询

#### 打开PDF
1. 在化学品详情页，向下滚动到"法规文件链接"
2. 点击任意PDF链接（如"危险化学品目录.pdf"）
3. **PDF会秒开**，同时自动在后台搜索该化学品

#### 查看搜索结果
- 右侧侧边栏显示所有匹配结果
- 结果按类型分组：
  - 🔢 **CAS号**：包含该CAS号的所有位置
  - 🧪 **化学品名称**：完整匹配化学品名称
  - 📝 **别名**：匹配任意别名
- 点击分组标题可展开/收起

#### 浏览PDF
- **翻页**：点击上一页/下一页按钮，或使用左右箭头键
- **缩放**：点击放大/缩小按钮，或使用 `Ctrl + 鼠标滚轮`
- **跳转**：点击搜索结果可直接跳转到该页

#### 性能提示
- ⚡ **首次搜索**：需要加载并缓存PDF文本（约15秒）
- 🚀 **后续搜索**：直接使用缓存，速度飞快（约1.5秒）
- 💡 **建议**：打开PDF后，可以多搜索几个化学品体验缓存带来的速度提升

### 3. 数据爬取

#### 使用爬虫
1. 双击运行 `run_scraper.bat`
2. 按提示输入化学品名称或CAS号
3. 爬虫自动访问网站，解析并保存MSDS数据
4. 数据保存在 `msds_json/` 目录

#### 导入数据库
爬取完成后，数据会自动保存为JSON格式。如需导入数据库：
```bash
python scrape_to_json.py
```

然后在Web界面使用JSON上传功能导入。

### 4. 数据导入

#### JSON文件导入
1. 在主页点击"上传JSON"按钮
2. 选择 `msds_json/` 目录下的JSON文件
3. 系统自动解析并导入数据库
4. 导入成功后可立即搜索

---

## 🔧 二次开发指南

### 项目结构
```
new_db/
├── app.py                      # Flask主应用
├── scrape_to_json.py          # 爬虫脚本
├── init_simple_db.sql         # 数据库初始化脚本
├── requirements.txt           # Python依赖
├── templates/
│   └── index.html             # 前端页面（4096行）
├── msds_json/                 # MSDS数据（JSON格式）
│   ├── 乙醇[无水]_64-17-5.json
│   ├── 甲苯_108-88-3.json
│   └── images/                # MSDS图片
├── pdf/                       # 法规PDF文档
│   ├── 危险化学品目录.pdf
│   └── ...
└── uploads/                   # 用户上传文件目录
```

### 核心代码模块

#### 1. 前端架构 (`templates/index.html`)

**主要功能模块**：
```javascript
// === 化学品搜索模块 ===
async function searchChemicals(query)          // 搜索化学品
function displayResults(results)               // 显示搜索结果
async function showChemicalDetail(id)          // 显示化学品详情

// === PDF查看器模块 ===
async function openPdfViewer(pdfFileName, ...)  // 打开PDF
async function renderPage(pageNum)              // 渲染PDF页面
async function getPageText(pageNum)             // 获取页面文本（带缓存）

// === PDF搜索模块 ===
async function searchInPdf(keywords)            // 在PDF中搜索
async function searchPageForKeywords(...)       // 搜索单页
function renderSearchResults()                  // 显示搜索结果

// === 缓存系统 ===
let pdfTextCache = new Map()                    // 文本缓存
let currentPdfFileName = ''                     // 当前PDF文件名
```

**关键优化点**：
- `getPageText()`：智能缓存函数，避免重复加载
- `renderPage()`：只渲染Canvas，不渲染文本图层
- `searchInPdf()`：批量并行搜索，实时更新进度

#### 2. 后端架构 (`app.py`)

**主要API接口**：
```python
@app.route('/')                          # 主页
@app.route('/search')                    # 搜索化学品API
@app.route('/chemical/<int:id>')         # 获取化学品详情API
@app.route('/pdf/<path:filename>')       # 提供PDF文件
@app.route('/upload_json', methods=['POST'])  # 上传JSON文件
```

**数据库操作**：
```python
def get_db_connection()                  # 获取数据库连接
def process_results(results)             # 处理查询结果
def insert_chemical(conn, data)          # 插入化学品数据
```

### 添加新功能

#### 示例1：添加新的搜索条件
修改 `app.py` 中的搜索API：
```python
@app.route('/search')
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')  # 新增：搜索类型
    
    # 根据search_type构建不同的SQL查询
    if search_type == 'cas':
        sql = "SELECT * FROM 化学品表 WHERE CAS号 LIKE %s"
    elif search_type == 'name':
        sql = "SELECT * FROM 化学品表 WHERE 中文名 LIKE %s OR 英文名 LIKE %s"
    # ... 更多条件
```

#### 示例2：添加新的PDF功能
修改 `templates/index.html` 中的PDF模块：
```javascript
// 添加PDF书签功能
function addBookmark(pageNum) {
    const bookmarks = JSON.parse(localStorage.getItem('pdfBookmarks') || '{}');
    if (!bookmarks[currentPdfFileName]) {
        bookmarks[currentPdfFileName] = [];
    }
    bookmarks[currentPdfFileName].push({
        page: pageNum,
        time: new Date().toISOString()
    });
    localStorage.setItem('pdfBookmarks', JSON.stringify(bookmarks));
    showNotification('📌 书签已添加', 'success');
}
```

#### 示例3：自定义数据源
修改 `scrape_to_json.py` 以支持新的数据源：
```python
async def scrape_from_new_source(chemical_name):
    """从新数据源爬取MSDS"""
    # 1. 构建URL
    url = f"https://new-source.com/msds?q={chemical_name}"
    
    # 2. 访问页面
    page = await browser.new_page()
    await page.goto(url)
    
    # 3. 解析数据
    data = {
        'cas': await page.locator('.cas').text_content(),
        'name': await page.locator('.name').text_content(),
        # ... 更多字段
    }
    
    return data
```

### 性能优化技巧

#### 1. 前端优化
- **使用缓存**：已实现PDF文本缓存，可扩展到图片缓存
- **延迟加载**：大型列表使用虚拟滚动
- **批量处理**：使用 `Promise.all()` 并行处理
- **Web Worker**：将重计算移到Worker线程

#### 2. 后端优化
- **数据库索引**：为常用查询字段添加索引
```sql
CREATE INDEX idx_cas ON 化学品表(CAS号);
CREATE INDEX idx_name ON 化学品表(中文名, 英文名);
```

- **连接池**：使用连接池管理数据库连接
```python
from dbutils.pooled_db import PooledDB
pool = PooledDB(pymysql, maxconnections=10, **DB_CONFIG)
```

- **查询优化**：使用LIMIT限制返回数量
```python
sql = "SELECT * FROM 化学品表 WHERE 中文名 LIKE %s LIMIT 100"
```

### 调试技巧

#### 前端调试
1. 打开Chrome开发者工具（F12）
2. **Console**：查看JavaScript错误和日志
3. **Network**：检查API请求和响应
4. **Performance**：分析性能瓶颈
5. **Application → Storage**：查看缓存数据

#### 后端调试
1. 使用Flask调试模式：
```python
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

2. 添加日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
app.logger.debug('调试信息')
```

3. 使用Python调试器：
```python
import pdb
pdb.set_trace()  # 设置断点
```

---

## ⚡ 性能优化

### 已实施的优化

#### 1. PDF加载优化（提升60-80%）
- **移除文本图层渲染**：只渲染Canvas，跳过DOM文本层
- **Web Worker**：使用PDF.js Worker，不阻塞主线程
- **先显示后搜索**：用户立即看到PDF，搜索在后台执行

**效果**：
- PDF打开：2-3秒 → **0.5-1秒**
- 翻页：0.5-1秒 → **0.1-0.2秒**

#### 2. PDF搜索优化（提升10-20倍）
- **智能文本缓存**：页面文本一次加载，永久缓存
- **批量并行搜索**：使用 `Promise.all()` 并行处理多页
- **智能批次调整**：有缓存时100页/批，无缓存时50页/批

**效果**（800页PDF）：
- 首次搜索：~15秒（建立缓存）
- 第2次搜索：~20秒 → **~1.5秒** ⚡⚡⚡
- 速度提升：**13倍**

#### 3. 搜索精度优化
- **优先级搜索**：CAS号 → 名称 → 别名
- **全字匹配**：严格的汉字边界判断
- **特殊字符处理**：允许"特"字作为边界（PDF特殊标记）

**效果**：
- 搜索准确率：**95%+**
- 误匹配率：**<5%**

### 缓存机制详解

#### 缓存结构
```javascript
pdfTextCache: Map {
  "危险化学品目录.pdf" => Map {
    1 => "第1页的文本内容...",
    2 => "第2页的文本内容...",
    ...
    800 => "第800页的文本内容..."
  },
  "易制爆危险化学品名录.pdf" => Map {
    ...
  }
}
```

#### 缓存工作流程
1. **检查缓存**：`pdfTextCache.has(filename) && pageCache.has(pageNum)`
2. **缓存命中**：直接返回文本，耗时 < 1ms
3. **缓存未命中**：
   - 调用 `page.getTextContent()`
   - 解析文本内容
   - 存入缓存
   - 返回文本

#### 缓存优势
- ✅ **跨化学品共享**：同一PDF的所有化学品搜索都使用同一缓存
- ✅ **内存友好**：800页PDF约1-2MB内存
- ✅ **自动管理**：关闭标签页自动清除

### 未来优化方向

#### 1. IndexedDB持久化缓存
将缓存保存到浏览器的IndexedDB，关闭标签页后依然有效：
```javascript
// 保存缓存
async function saveCacheToIndexedDB() {
    const db = await openDB('pdfCache', 1);
    for (const [fileName, pageMap] of pdfTextCache) {
        await db.put('cache', Array.from(pageMap), fileName);
    }
}

// 加载缓存
async function loadCacheFromIndexedDB() {
    const db = await openDB('pdfCache', 1);
    const keys = await db.getAllKeys('cache');
    for (const fileName of keys) {
        const pages = await db.get('cache', fileName);
        pdfTextCache.set(fileName, new Map(pages));
    }
}
```

#### 2. 服务端缓存
在服务器端预处理PDF，将文本索引存入数据库：
```python
# 预处理PDF并存入数据库
def index_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        # 存入数据库
        cursor.execute(
            "INSERT INTO pdf_index (file_name, page_num, text) VALUES (%s, %s, %s)",
            (pdf_path, page_num, text)
        )
```

#### 3. 全文检索引擎
使用Elasticsearch等全文检索引擎：
```python
from elasticsearch import Elasticsearch
es = Elasticsearch(['localhost:9200'])

# 索引PDF内容
es.index(index='pdfs', body={
    'file_name': '危险化学品目录.pdf',
    'page': 1,
    'content': 'PDF页面内容...'
})

# 搜索
results = es.search(index='pdfs', body={
    'query': {'match': {'content': '甲苯'}}
})
```

---

## ❓ 常见问题

### 安装与配置

**Q1: 安装依赖时报错怎么办？**

A: 尝试以下解决方案：
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 如果Playwright安装失败，单独安装
playwright install chromium
```

**Q2: 数据库连接失败？**

A: 检查以下几点：
1. MySQL服务是否启动
2. 数据库名称是否正确（`危化品简化数据库`）
3. 用户名和密码是否正确
4. 端口号是否为3306

**Q3: 启动应用后访问不了？**

A: 
- 检查Flask是否正常启动（看控制台输出）
- 确认访问地址：`http://localhost:5000`（不是 `127.0.0.1`）
- 检查防火墙是否阻止端口5000
- 尝试更换端口：修改 `app.py` 中的 `app.run(port=5000)` 为其他端口

### 使用问题

**Q4: 搜索不到化学品？**

A: 
- 确认数据库中有该化学品数据
- 尝试使用CAS号搜索（最准确）
- 检查是否有拼写错误
- 尝试使用部分关键词搜索

**Q5: PDF打开很慢？**

A: 
- 首次打开需要加载文件，属于正常现象
- 确保PDF文件大小合理（<50MB）
- 检查网络连接（如果使用远程服务器）
- 查看浏览器控制台是否有错误

**Q6: PDF搜索不到结果？**

A: 
- 首次搜索需要建立缓存（约15秒），请耐心等待
- 确认PDF中确实包含该化学品
- 检查化学品名称的拼写
- 尝试使用CAS号或别名搜索

**Q7: 第二次搜索还是很慢？**

A: 
- 刷新页面会清除缓存，需要重新建立
- 切换到其他PDF也需要重新建立缓存
- 确认看到"⚡ 使用缓存加速"提示
- 检查浏览器是否禁用了JavaScript

### 开发问题

**Q8: 如何添加新的PDF文档？**

A: 
1. 将PDF文件复制到 `pdf/` 目录
2. 在前端HTML中添加链接：
```javascript
const pdfLinks = [
    { name: '新法规文件.pdf', title: '新法规文件' },
    // ... 其他文件
];
```

**Q9: 如何修改数据库结构？**

A: 
1. 修改 `init_simple_db.sql` 文件
2. 删除现有数据库（注意备份数据！）
3. 重新创建数据库并执行SQL脚本
4. 修改 `app.py` 中的相关代码

**Q10: 如何自定义搜索逻辑？**

A: 修改 `templates/index.html` 中的搜索函数：
```javascript
async function searchPageForKeywords(pageNum, keywordList, keywordType) {
    // 在这里修改匹配逻辑
    // 例如：改为正则表达式匹配
    const regex = new RegExp(keyword, 'gi');
    const matches = pageText.match(regex);
    // ...
}
```

### 性能问题

**Q11: 如何提高搜索速度？**

A: 
- 确保使用缓存（第二次搜索会快很多）
- 调整批次大小：修改 `BATCH_SIZE`（当前：有缓存100页，无缓存50页）
- 考虑使用服务端预索引（见未来优化方向）

**Q12: 内存占用过大？**

A: 
- 缓存会占用内存，可以清除不常用PDF的缓存：
```javascript
// 清除指定PDF的缓存
pdfTextCache.delete('不常用的PDF.pdf');

// 清除所有缓存
pdfTextCache.clear();
```

**Q13: 如何限制缓存大小？**

A: 实现LRU缓存策略：
```javascript
const MAX_CACHE_SIZE = 5; // 最多缓存5个PDF

function addToCache(fileName, pageMap) {
    if (pdfTextCache.size >= MAX_CACHE_SIZE) {
        // 删除最早添加的项
        const firstKey = pdfTextCache.keys().next().value;
        pdfTextCache.delete(firstKey);
    }
    pdfTextCache.set(fileName, pageMap);
}
```

---

## 🛠️ 技术栈

### 后端技术
- **Flask 2.0+**：轻量级Web框架
- **PyMySQL**：Python MySQL客户端
- **Playwright**：现代化网页自动化工具
- **BeautifulSoup4**：HTML/XML解析库

### 前端技术
- **原生JavaScript (ES6+)**：无框架依赖，性能卓越
- **PDF.js 3.11**：Mozilla开源PDF渲染库
- **CSS3**：现代渐变、动画效果
- **Fetch API**：异步HTTP请求

### 数据库
- **MySQL 8.0+**：关系型数据库
- **UTF8MB4**：完整Unicode支持（包括Emoji）
- **InnoDB引擎**：支持事务和外键

### 开发工具
- **Git**：版本控制
- **Chrome DevTools**：前端调试
- **MySQL Workbench**：数据库管理
- **VS Code**：推荐的代码编辑器

---

## 📄 许可证

本项目采用 MIT 许可证。

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 贡献指南
1. Fork本项目
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送到分支：`git push origin feature/AmazingFeature`
5. 提交Pull Request

---

## 📞 联系方式

如有问题或建议，欢迎联系。

---

## 🙏 致谢

- Mozilla PDF.js团队
- Flask开发团队
- MySQL社区
- 所有贡献者

---

## 📚 更新日志

### v2.0.0 (2025-10-16) - 性能革命版 🚀
- ⚡ **重大性能提升**：
  - PDF打开速度提升60-80%
  - 搜索速度提升10-20倍（缓存生效后）
  - 翻页和缩放响应速度提升80%+
- 🎯 **功能增强**：
  - 实现智能文本缓存系统
  - 添加搜索进度显示
  - 优化搜索结果分组显示
  - 改进全字匹配逻辑
- 🐛 **问题修复**：
  - 修复PDF高亮不准确问题
  - 修复搜索结果跳转错误
  - 修复PDF.js警告信息
  - 修复搜索结果数量限制

### v1.0.0 (2025-01) - 初始版本
- 基础化学品查询功能
- PDF文档查看功能
- MSDS数据爬虫
- 数据库管理功能

---

**🌟 如果觉得项目有帮助，请给个Star！**

