# 开发者指南 👨‍💻

> 深度定制和扩展危化品智能数据库系统

---

## 📚 目录

- [架构设计](#架构设计)
- [核心模块](#核心模块)
- [API文档](#api文档)
- [数据库设计](#数据库设计)
- [前端架构](#前端架构)
- [扩展开发](#扩展开发)
- [性能优化](#性能优化)
- [调试技巧](#调试技巧)

---

## 🏗️ 架构设计

### 整体架构
```
┌─────────────────────────────────────────────┐
│              浏览器客户端                    │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐ │
│  │  UI层     │  │ PDF渲染  │  │ 缓存管理 │ │
│  │(HTML/CSS) │  │ (PDF.js) │  │ (Map)    │ │
│  └───────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────┘
                    ↕ HTTP/JSON
┌─────────────────────────────────────────────┐
│              Flask后端服务                   │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐ │
│  │  路由层   │  │ 业务逻辑 │  │ 数据访问 │ │
│  │ (Routes)  │  │ (Logic)  │  │ (DAO)    │ │
│  └───────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────┘
                    ↕ PyMySQL
┌─────────────────────────────────────────────┐
│              MySQL数据库                     │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 化学品表  │  │  索引    │  │  关系    │ │
│  └───────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────┘
```

### 设计模式

#### 1. MVC模式
- **Model (模型)**：MySQL数据库 + `app.py`数据访问层
- **View (视图)**：`templates/index.html`
- **Controller (控制器)**：`app.py`路由和业务逻辑

#### 2. 前后端分离
- 前端通过Fetch API调用后端RESTful接口
- 后端返回JSON格式数据
- 前端负责渲染和交互

#### 3. 缓存模式
- **客户端缓存**：浏览器端PDF文本缓存
- **数据库缓存**：连接池复用
- **文件缓存**：静态文件由Flask直接服务

---

## 🔧 核心模块

### 后端模块 (`app.py`)

#### 1. 数据库连接模块
```python
def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

# 使用示例
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM 化学品表")
results = cursor.fetchall()
conn.close()
```

**最佳实践**：
- ✅ 使用上下文管理器自动关闭连接
- ✅ 使用连接池管理连接
- ✅ 捕获并处理异常

优化后的代码：
```python
from contextlib import contextmanager

@contextmanager
def get_db():
    """上下文管理器：自动关闭连接"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# 使用示例
with get_db() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM 化学品表")
    results = cursor.fetchall()
```

#### 2. 数据处理模块
```python
def process_results(results):
    """处理查询结果，转换特殊类型"""
    # 处理Decimal、datetime、JSON等类型
    # 返回可序列化为JSON的数据
```

**关键功能**：
- Decimal → float
- datetime → ISO字符串
- None → null
- JSON字符串 → dict/list

#### 3. 路由模块
```python
@app.route('/search')
def search():
    """搜索化学品"""
    query = request.args.get('q', '')
    # 执行搜索逻辑
    return jsonify(results)

@app.route('/chemical/<int:id>')
def get_chemical(id):
    """获取化学品详情"""
    # 查询数据库
    return jsonify(chemical)
```

### 前端模块 (`templates/index.html`)

#### 1. 搜索模块
```javascript
// 核心函数
async function searchChemicals(query) {
    const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
    const data = await response.json();
    displayResults(data);
}

// 显示结果
function displayResults(results) {
    // DOM操作，渲染化学品卡片
}
```

#### 2. PDF渲染模块
```javascript
// 核心函数
async function openPdfViewer(pdfFileName, pageNumber, title, searchKeyword) {
    // 1. 加载PDF
    const loadingTask = pdfjsLib.getDocument({url, cMapUrl, cMapPacked});
    pdfDoc = await loadingTask.promise;
    
    // 2. 渲染页面
    await renderPage(1);
    
    // 3. 后台搜索
    if (searchKeyword) {
        setTimeout(() => searchInPdf(searchKeyword), 50);
    }
}

// 页面渲染
async function renderPage(pageNum) {
    const page = await pdfDoc.getPage(pageNum);
    const viewport = page.getViewport({scale: currentScale});
    
    // 渲染到Canvas
    await page.render({canvasContext, viewport}).promise;
}
```

#### 3. 缓存模块
```javascript
// 缓存结构
let pdfTextCache = new Map();  // Map<fileName, Map<pageNum, text>>

// 获取页面文本（带缓存）
async function getPageText(pageNum) {
    // 1. 检查缓存
    if (缓存存在) return 缓存内容;
    
    // 2. 加载并缓存
    const page = await pdfDoc.getPage(pageNum);
    const textContent = await page.getTextContent();
    const pageText = textContent.items.map(item => item.str).join('');
    
    // 3. 存入缓存
    缓存.set(pageNum, pageText);
    
    return pageText;
}
```

#### 4. 搜索模块
```javascript
// 主搜索函数
async function searchInPdf(keywords) {
    // 1. 构建搜索队列（按优先级）
    const searchQueue = [CAS号, 名称, 别名];
    
    // 2. 批量并行搜索
    for (let group of ['CAS号', '化学品名称', '别名']) {
        for (let batch of 分批(totalPages, BATCH_SIZE)) {
            await Promise.all(batch.map(page => searchPageForKeywords(page, keywords)));
        }
    }
    
    // 3. 渲染结果
    renderSearchResults();
}

// 单页搜索
async function searchPageForKeywords(pageNum, keywordList, keywordType) {
    const pageText = await getPageText(pageNum);  // 使用缓存
    
    // 遍历关键词，查找匹配
    for (const {keyword, matchType} of keywordList) {
        if (matchType === 'exact') {
            // 全字匹配：检查边界
        } else {
            // 包含匹配：indexOf
        }
    }
}
```

---

## 📡 API文档

### 1. 搜索化学品
```http
GET /search?q={query}
```

**参数**：
- `q` (string, required): 搜索关键词

**响应**：
```json
[
    {
        "ID": 1,
        "CAS号": "64-17-5",
        "中文名": "乙醇",
        "英文名": "Ethanol",
        "分子式": "C2H6O",
        "别名": "酒精",
        "危险类别": "易燃液体"
    },
    ...
]
```

### 2. 获取化学品详情
```http
GET /chemical/<id>
```

**参数**：
- `id` (integer, required): 化学品ID

**响应**：
```json
{
    "ID": 1,
    "CAS号": "64-17-5",
    "中文名": "乙醇",
    "MSDS各板块": {
        "01_化学品及企业标识": "...",
        "02_危险性概述": "...",
        ...
    },
    "图片JSON": ["image1.jpg", "image2.jpg"]
}
```

### 3. 上传JSON文件
```http
POST /upload_json
Content-Type: multipart/form-data
```

**参数**：
- `file` (file, required): JSON文件

**响应**：
```json
{
    "success": true,
    "message": "成功导入化学品：乙醇 (CAS: 64-17-5)"
}
```

### 4. 获取PDF文件
```http
GET /pdf/<filename>
```

**参数**：
- `filename` (string, required): PDF文件名

**响应**：PDF文件流

### 5. 获取JSON列表
```http
GET /json_files
```

**响应**：
```json
[
    "乙醇[无水]_64-17-5.json",
    "甲苯_108-88-3.json",
    ...
]
```

---

## 🗄️ 数据库设计

### 化学品表结构
```sql
CREATE TABLE 化学品表 (
    ID INT PRIMARY KEY AUTO_INCREMENT,
    CAS号 VARCHAR(20),
    中文名 VARCHAR(255),
    英文名 VARCHAR(255),
    分子式 VARCHAR(100),
    别名 TEXT,
    危险类别 VARCHAR(100),
    
    -- MSDS各板块（16个字段）
    化学品及企业标识 TEXT,
    危险性概述 TEXT,
    成分组分信息 TEXT,
    急救措施 TEXT,
    消防措施 TEXT,
    泄漏应急处理 TEXT,
    操作处置和储存 TEXT,
    接触控制个体防护 TEXT,
    理化特性 TEXT,
    稳定性和反应性 TEXT,
    毒理学信息 TEXT,
    生态学信息 TEXT,
    废弃处置 TEXT,
    运输信息 TEXT,
    法规信息 TEXT,
    其他信息 TEXT,
    
    图片JSON TEXT,
    
    -- 索引
    INDEX idx_cas (CAS号),
    INDEX idx_name (中文名, 英文名),
    FULLTEXT idx_fulltext (中文名, 英文名, 别名)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 查询优化建议

#### 1. 使用索引
```sql
-- 精确查询（走索引）
SELECT * FROM 化学品表 WHERE CAS号 = '64-17-5';

-- 前缀匹配（走索引）
SELECT * FROM 化学品表 WHERE 中文名 LIKE '甲%';

-- 全文检索（走全文索引）
SELECT * FROM 化学品表 
WHERE MATCH(中文名, 英文名, 别名) AGAINST('乙醇');
```

#### 2. 避免全表扫描
```sql
-- 不好：中间匹配，全表扫描
SELECT * FROM 化学品表 WHERE 中文名 LIKE '%醇%';

-- 好：前缀匹配，走索引
SELECT * FROM 化学品表 WHERE 中文名 LIKE '乙醇%';

-- 更好：全文检索
SELECT * FROM 化学品表 
WHERE MATCH(中文名, 英文名, 别名) AGAINST('醇' IN BOOLEAN MODE);
```

#### 3. 分页查询
```sql
-- 使用LIMIT限制返回数量
SELECT * FROM 化学品表 
WHERE 中文名 LIKE '甲%' 
LIMIT 100 OFFSET 0;
```

---

## 🎨 前端架构

### JavaScript模块划分

#### 1. 全局状态管理
```javascript
// PDF查看器状态
let pdfDoc = null;
let currentPageNum = 1;
let totalPagesCount = 0;
let currentScale = 1.5;
let searchResults = [];

// 缓存状态
let pdfTextCache = new Map();
let currentPdfFileName = '';

// 当前化学品信息
let currentChemicalInfo = {
    cas: '',
    name: '',
    aliases: ''
};
```

#### 2. 事件处理
```javascript
// DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    // 初始化事件监听器
    setupEventListeners();
});

// 搜索按钮点击
document.getElementById('searchBtn').addEventListener('click', async function() {
    const query = document.getElementById('searchInput').value;
    await searchChemicals(query);
});

// 键盘事件
document.addEventListener('keydown', function(e) {
    if (PDF查看器打开) {
        if (e.key === 'ArrowLeft') previousPage();
        if (e.key === 'ArrowRight') nextPage();
    }
});
```

#### 3. 工具函数
```javascript
// 防抖
function debounce(func, delay) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => func.apply(this, args), delay);
    };
}

// 节流
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 通知系统
function showNotification(message, type = 'success', duration = 2000) {
    // 创建通知元素
    // 自动消失
}
```

---

## 🚀 扩展开发

### 示例1：添加化学品收藏功能

#### 前端实现
```javascript
// 1. 添加收藏按钮
function addFavoriteButton(chemicalId) {
    const btn = document.createElement('button');
    btn.textContent = '⭐ 收藏';
    btn.onclick = () => toggleFavorite(chemicalId);
    return btn;
}

// 2. 收藏逻辑（使用LocalStorage）
function toggleFavorite(chemicalId) {
    const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    const index = favorites.indexOf(chemicalId);
    
    if (index === -1) {
        favorites.push(chemicalId);
        showNotification('已添加到收藏', 'success');
    } else {
        favorites.splice(index, 1);
        showNotification('已取消收藏', 'info');
    }
    
    localStorage.setItem('favorites', JSON.stringify(favorites));
}

// 3. 显示收藏列表
function showFavorites() {
    const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    // 批量查询收藏的化学品
    const promises = favorites.map(id => 
        fetch(`/chemical/${id}`).then(r => r.json())
    );
    Promise.all(promises).then(chemicals => {
        displayResults(chemicals);
    });
}
```

### 示例2：添加导出Excel功能

#### 后端实现
```python
from openpyxl import Workbook

@app.route('/export_excel')
def export_excel():
    """导出化学品数据为Excel"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM 化学品表")
    results = cursor.fetchall()
    conn.close()
    
    # 创建Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "化学品数据"
    
    # 写入表头
    headers = ['ID', 'CAS号', '中文名', '英文名', '分子式', '别名']
    ws.append(headers)
    
    # 写入数据
    for row in results:
        ws.append([row[h] for h in headers])
    
    # 保存
    filename = 'chemicals.xlsx'
    wb.save(filename)
    
    return send_file(filename, as_attachment=True)
```

#### 前端调用
```javascript
function exportToExcel() {
    window.location.href = '/export_excel';
    showNotification('正在导出Excel...', 'info');
}
```

### 示例3：添加批量比较功能

```javascript
// 1. 选择多个化学品
let selectedChemicals = new Set();

function toggleSelection(chemicalId) {
    if (selectedChemicals.has(chemicalId)) {
        selectedChemicals.delete(chemicalId);
    } else {
        selectedChemicals.add(chemicalId);
    }
    updateCompareButton();
}

// 2. 显示比较界面
async function compareChemicals() {
    const ids = Array.from(selectedChemicals);
    const chemicals = await Promise.all(
        ids.map(id => fetch(`/chemical/${id}`).then(r => r.json()))
    );
    
    // 创建对比表格
    const table = document.createElement('table');
    table.className = 'comparison-table';
    
    // 表头
    const headerRow = table.insertRow();
    headerRow.insertCell().textContent = '属性';
    chemicals.forEach(c => {
        headerRow.insertCell().textContent = c.中文名;
    });
    
    // 数据行
    const properties = ['CAS号', '分子式', '危险类别', '闪点', '沸点'];
    properties.forEach(prop => {
        const row = table.insertRow();
        row.insertCell().textContent = prop;
        chemicals.forEach(c => {
            row.insertCell().textContent = c[prop] || '-';
        });
    });
    
    // 显示表格
    document.getElementById('comparisonArea').appendChild(table);
}
```

---

## ⚡ 性能优化

### 前端优化技巧

#### 1. 虚拟滚动（大列表）
```javascript
class VirtualScroll {
    constructor(container, items, rowHeight) {
        this.container = container;
        this.items = items;
        this.rowHeight = rowHeight;
        this.visibleCount = Math.ceil(container.clientHeight / rowHeight);
        this.startIndex = 0;
        
        this.render();
        this.container.addEventListener('scroll', () => this.onScroll());
    }
    
    render() {
        const endIndex = this.startIndex + this.visibleCount;
        const visibleItems = this.items.slice(this.startIndex, endIndex);
        
        this.container.innerHTML = '';
        visibleItems.forEach((item, index) => {
            const row = this.createRow(item);
            row.style.position = 'absolute';
            row.style.top = `${(this.startIndex + index) * this.rowHeight}px`;
            this.container.appendChild(row);
        });
    }
    
    onScroll() {
        const scrollTop = this.container.scrollTop;
        const newStartIndex = Math.floor(scrollTop / this.rowHeight);
        if (newStartIndex !== this.startIndex) {
            this.startIndex = newStartIndex;
            this.render();
        }
    }
}
```

#### 2. 图片懒加载
```javascript
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}
```

#### 3. 请求合并（批量查询）
```javascript
class RequestBatcher {
    constructor(batchFn, delay = 50) {
        this.batchFn = batchFn;
        this.delay = delay;
        this.queue = [];
        this.timer = null;
    }
    
    add(id) {
        return new Promise((resolve, reject) => {
            this.queue.push({id, resolve, reject});
            this.scheduleBatch();
        });
    }
    
    scheduleBatch() {
        if (this.timer) clearTimeout(this.timer);
        this.timer = setTimeout(() => this.flush(), this.delay);
    }
    
    async flush() {
        if (this.queue.length === 0) return;
        
        const batch = this.queue.splice(0);
        const ids = batch.map(item => item.id);
        
        try {
            const results = await this.batchFn(ids);
            batch.forEach((item, index) => {
                item.resolve(results[index]);
            });
        } catch (error) {
            batch.forEach(item => item.reject(error));
        }
    }
}

// 使用示例
const chemicalBatcher = new RequestBatcher(async (ids) => {
    const response = await fetch(`/chemicals/batch?ids=${ids.join(',')}`);
    return response.json();
});

// 自动合并请求
const chemical1 = await chemicalBatcher.add(1);
const chemical2 = await chemicalBatcher.add(2);
const chemical3 = await chemicalBatcher.add(3);
```

### 后端优化技巧

#### 1. 数据库连接池
```python
from dbutils.pooled_db import PooledDB

# 创建连接池
db_pool = PooledDB(
    creator=pymysql,
    maxconnections=10,  # 最大连接数
    mincached=2,        # 初始化连接数
    maxcached=5,        # 最大缓存连接数
    blocking=True,      # 连接池满时阻塞等待
    **DB_CONFIG
)

def get_db_connection():
    return db_pool.connection()
```

#### 2. 查询结果缓存
```python
from functools import lru_cache
from datetime import datetime, timedelta

# 简单缓存
@lru_cache(maxsize=100)
def get_chemical_by_cas(cas):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM 化学品表 WHERE CAS号 = %s", (cas,))
    result = cursor.fetchone()
    conn.close()
    return result

# 带过期时间的缓存
cache_store = {}
CACHE_TTL = timedelta(minutes=10)

def cached_query(cache_key):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if cache_key in cache_store:
                data, timestamp = cache_store[cache_key]
                if datetime.now() - timestamp < CACHE_TTL:
                    return data
            
            result = func(*args, **kwargs)
            cache_store[cache_key] = (result, datetime.now())
            return result
        return wrapper
    return decorator

@cached_query('all_chemicals')
def get_all_chemicals():
    # 查询数据库
    pass
```

#### 3. 异步处理
```python
from threading import Thread

def async_task(func):
    """装饰器：异步执行函数"""
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

@async_task
def send_email(to, subject, content):
    # 发送邮件（耗时操作）
    pass

# 使用
@app.route('/submit')
def submit():
    # 处理请求
    send_email('user@example.com', '提交成功', '...')  # 异步执行
    return jsonify({'success': True})  # 立即返回
```

---

## 🐛 调试技巧

### 前端调试

#### 1. 使用Console API
```javascript
// 分组日志
console.group('PDF搜索');
console.log('搜索关键词:', keywords);
console.log('搜索结果数:', results.length);
console.groupEnd();

// 表格显示
console.table(searchResults);

// 计时
console.time('PDF加载');
await loadPdf();
console.timeEnd('PDF加载');

// 断言
console.assert(results.length > 0, '搜索结果为空！');
```

#### 2. 使用Debugger
```javascript
// 设置断点
function searchInPdf(keywords) {
    debugger;  // 代码会在这里暂停
    // 在Chrome DevTools中可以单步调试
}

// 条件断点（在Chrome DevTools中设置）
// 右键断点 → Edit breakpoint → 输入条件
// 例如：pageNum === 38
```

#### 3. 网络监控
```javascript
// 监控所有Fetch请求
const originalFetch = window.fetch;
window.fetch = function(...args) {
    console.log('Fetch请求:', args[0]);
    return originalFetch.apply(this, args)
        .then(response => {
            console.log('Fetch响应:', response.status, response.statusText);
            return response;
        });
};
```

### 后端调试

#### 1. 启用调试模式
```python
# 开发环境
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

#### 2. 添加日志
```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# 使用日志
@app.route('/search')
def search():
    query = request.args.get('q', '')
    app.logger.info(f'搜索请求: {query}')
    
    try:
        results = perform_search(query)
        app.logger.debug(f'搜索结果数: {len(results)}')
        return jsonify(results)
    except Exception as e:
        app.logger.error(f'搜索失败: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500
```

#### 3. SQL查询日志
```python
def execute_query(sql, params=None):
    """执行SQL并记录日志"""
    logger.debug(f'SQL: {sql}')
    logger.debug(f'参数: {params}')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    start_time = time.time()
    cursor.execute(sql, params)
    elapsed = time.time() - start_time
    
    logger.debug(f'执行时间: {elapsed:.3f}秒')
    
    results = cursor.fetchall()
    logger.debug(f'返回行数: {len(results)}')
    
    conn.close()
    return results
```

---

## 📦 部署指南

### 开发环境
```bash
# 启动开发服务器
python app.py
```

### 生产环境

#### 使用Gunicorn
```bash
# 安装Gunicorn
pip install gunicorn

# 启动（4个工作进程）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### 使用Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static {
        alias /path/to/your/static;
    }
    
    location /pdf {
        alias /path/to/your/pdf;
    }
}
```

#### Docker部署
```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
# 构建镜像
docker build -t chemical-db .

# 运行容器
docker run -d -p 5000:5000 chemical-db
```

---

## 📚 推荐资源

### 官方文档
- [Flask文档](https://flask.palletsprojects.com/)
- [PDF.js文档](https://mozilla.github.io/pdf.js/)
- [MySQL文档](https://dev.mysql.com/doc/)
- [PyMySQL文档](https://pymysql.readthedocs.io/)

### 学习资源
- [JavaScript高级程序设计](https://book.douban.com/subject/35175321/)
- [Flask Web开发实战](https://book.douban.com/subject/30310340/)
- [高性能MySQL](https://book.douban.com/subject/23008813/)

---

## 🤝 贡献代码

1. Fork项目
2. 创建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送到分支：`git push origin feature/AmazingFeature`
5. 提交Pull Request

### 代码规范
- Python代码遵循PEP 8
- JavaScript代码使用ES6+语法
- 添加必要的注释和文档
- 编写单元测试

---

**Happy Coding! 🎉**

