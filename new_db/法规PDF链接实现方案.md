# 法规PDF链接实现方案

## 📋 需求分析

在MSDS第15部分"法规信息"中，为每个"列入"的法规生成可点击链接，点击后：
1. 弹出PDF查看器
2. 自动跳转到该化学品在PDF中的页码
3. （可选）高亮显示化学品名称

---

## 🗂️ 数据库设计

### 1. 法规文件表
```sql
CREATE TABLE 法规文件 (
    编号 INT PRIMARY KEY AUTO_INCREMENT,
    法规名称 VARCHAR(255) NOT NULL,  -- 完整名称
    法规简称 VARCHAR(100),           -- 用于匹配的简称
    PDF文件名 VARCHAR(255),          -- 如：易制爆危险化学品名录.pdf
    发布单位 VARCHAR(200),
    发布年份 INT,
    备注 TEXT,
    创建时间 DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2. 化学品-法规-页码映射表
```sql
CREATE TABLE 化学品法规页码映射 (
    编号 INT PRIMARY KEY AUTO_INCREMENT,
    化学品编号 INT,
    法规文件编号 INT,
    PDF页码 INT,              -- 该化学品在PDF中的页码
    列入状态 ENUM('列入', '未列入') DEFAULT '列入',
    备注 TEXT,
    创建时间 DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (化学品编号) REFERENCES 化学品(编号) ON DELETE CASCADE,
    FOREIGN KEY (法规文件编号) REFERENCES 法规文件(编号) ON DELETE CASCADE,
    INDEX idx_chemical (化学品编号),
    INDEX idx_regulation (法规文件编号)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 🔄 实现流程

### 阶段一：数据准备（需人工或脚本完成）

#### 1. 插入法规文件信息
```sql
INSERT INTO 法规文件 (法规名称, 法规简称, PDF文件名, 发布单位, 发布年份) VALUES
('危险化学品目录（2015年版）', '危险化学品目录', '危险化学品目录2015.pdf', '安监总局', 2015),
('易制爆危险化学品名录（2011年版）', '易制爆危险化学品名录', '易制爆危险化学品名录.pdf', '公安部', 2011),
('高毒物品目录', '高毒物品目录', '高毒物品目录.pdf', '卫生部', 2003);
-- ... 其他法规
```

#### 2. 建立化学品-页码映射

**方法A：使用提供的Python脚本自动提取**
```python
# 已生成：pdf/易制爆危险化学品名录_analysis.json
# 包含了每个CAS号对应的PDF页码
```

**方法B：手工录入重点化学品**
```sql
-- 示例：乙酸乙酯在"易制爆危险化学品名录"中
INSERT INTO 化学品法规页码映射 (化学品编号, 法规文件编号, PDF页码, 列入状态)
SELECT c.编号, r.编号, 2, '列入'
FROM 化学品 c, 法规文件 r
WHERE c.CAS号 = '141-78-6' AND r.法规简称 = '易制爆危险化学品名录';
```

---

### 阶段二：后端API开发

#### 1. 获取化学品的法规信息（带PDF页码）

在 `app.py` 中添加新接口：

```python
@app.route('/api/regulations/<int:chemical_id>', methods=['GET'])
def get_regulations(chemical_id):
    """获取化学品的法规信息及PDF页码"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute("""
            SELECT 
                r.法规名称,
                r.法规简称,
                r.PDF文件名,
                m.PDF页码,
                m.列入状态
            FROM 化学品法规页码映射 m
            JOIN 法规文件 r ON m.法规文件编号 = r.编号
            WHERE m.化学品编号 = %s
            ORDER BY r.发布年份 DESC
        """, (chemical_id,))
        
        regulations = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'regulations': regulations
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
```

---

### 阶段三：前端实现

#### 1. 引入PDF.js库

在 `index.html` 的 `<head>` 中添加：

```html
<!-- PDF.js -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js"></script>
```

#### 2. 添加PDF查看器UI

```html
<!-- PDF查看器模态框 -->
<div id="pdfViewerOverlay" class="pdf-viewer-overlay">
    <div class="pdf-viewer-container">
        <div class="pdf-viewer-header">
            <h3 id="pdfViewerTitle">法规文件</h3>
            <button onclick="closePdfViewer()" class="close-btn">✕</button>
        </div>
        <div class="pdf-viewer-controls">
            <button onclick="previousPage()">上一页</button>
            <span>第 <span id="currentPage">1</span> / <span id="totalPages">1</span> 页</span>
            <button onclick="nextPage()">下一页</button>
            <button onclick="zoomIn()">放大</button>
            <button onclick="zoomOut()">缩小</button>
        </div>
        <div class="pdf-viewer-content">
            <canvas id="pdfCanvas"></canvas>
        </div>
    </div>
</div>
```

#### 3. PDF查看器样式

```css
.pdf-viewer-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    z-index: 10000;
    justify-content: center;
    align-items: center;
}

.pdf-viewer-overlay.show {
    display: flex;
}

.pdf-viewer-container {
    background: white;
    border-radius: 10px;
    width: 90%;
    height: 90%;
    display: flex;
    flex-direction: column;
}

.pdf-viewer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    border-bottom: 1px solid #e9ecef;
}

.pdf-viewer-controls {
    display: flex;
    gap: 10px;
    padding: 10px 20px;
    background: #f8f9fa;
    border-bottom: 1px solid #e9ecef;
    align-items: center;
}

.pdf-viewer-content {
    flex: 1;
    overflow: auto;
    padding: 20px;
    background: #525659;
    display: flex;
    justify-content: center;
    align-items: flex-start;
}

#pdfCanvas {
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
```

#### 4. JavaScript逻辑

```javascript
// PDF查看器状态
let pdfDoc = null;
let currentPageNum = 1;
let totalPagesCount = 0;
let currentScale = 1.5;

// 打开PDF并跳转到指定页码
async function openPdfViewer(pdfFileName, pageNumber = 1, title = '法规文件') {
    try {
        const pdfPath = `/pdf/${pdfFileName}`;
        
        // 加载PDF
        const loadingTask = pdfjsLib.getDocument(pdfPath);
        pdfDoc = await loadingTask.promise;
        totalPagesCount = pdfDoc.numPages;
        
        // 更新标题
        document.getElementById('pdfViewerTitle').textContent = title;
        document.getElementById('totalPages').textContent = totalPagesCount;
        
        // 跳转到指定页
        currentPageNum = pageNumber;
        await renderPage(currentPageNum);
        
        // 显示查看器
        document.getElementById('pdfViewerOverlay').classList.add('show');
        
    } catch (error) {
        console.error('PDF加载失败:', error);
        showNotification('PDF加载失败：' + error.message, 'error');
    }
}

// 渲染PDF页面
async function renderPage(pageNum) {
    const page = await pdfDoc.getPage(pageNum);
    const canvas = document.getElementById('pdfCanvas');
    const context = canvas.getContext('2d');
    
    const viewport = page.getViewport({ scale: currentScale });
    canvas.height = viewport.height;
    canvas.width = viewport.width;
    
    const renderContext = {
        canvasContext: context,
        viewport: viewport
    };
    
    await page.render(renderContext).promise;
    document.getElementById('currentPage').textContent = pageNum;
}

// 翻页功能
function previousPage() {
    if (currentPageNum <= 1) return;
    currentPageNum--;
    renderPage(currentPageNum);
}

function nextPage() {
    if (currentPageNum >= totalPagesCount) return;
    currentPageNum++;
    renderPage(currentPageNum);
}

// 缩放功能
function zoomIn() {
    currentScale += 0.25;
    renderPage(currentPageNum);
}

function zoomOut() {
    if (currentScale <= 0.5) return;
    currentScale -= 0.25;
    renderPage(currentPageNum);
}

// 关闭查看器
function closePdfViewer() {
    document.getElementById('pdfViewerOverlay').classList.remove('show');
    pdfDoc = null;
}
```

#### 5. 在第15章格式化中添加链接

修改 `formatFifteenthChapter` 函数，为"列入"添加点击事件：

```javascript
// 在格式化第15章时，添加data属性存储PDF信息
function formatFifteenthChapter(text) {
    // ... 原有代码 ...
    
    // 当检测到"列入"时
    if (line === '列入') {
        // 从前面的行中提取法规名称
        const regulationName = lines[i-1]; // 假设法规名称在上一行
        
        html += `<div class="regulation-status-link" 
                      data-regulation="${regulationName}" 
                      onclick="handleRegulationClick(this, ${currentChemicalId})">
                    ${line} <span style="color: #007bff;">📄</span>
                </div>`;
    }
    
    // ... 原有代码 ...
}

// 处理法规点击
async function handleRegulationClick(element, chemicalId) {
    const regulationName = element.getAttribute('data-regulation');
    
    try {
        // 从后端获取PDF信息
        const response = await fetch(`/api/regulations/${chemicalId}`);
        const data = await response.json();
        
        if (data.success) {
            const regulation = data.regulations.find(r => 
                regulationName.includes(r.法规简称)
            );
            
            if (regulation && regulation.PDF文件名) {
                openPdfViewer(
                    regulation.PDF文件名, 
                    regulation.PDF页码 || 1,
                    regulation.法规名称
                );
            } else {
                showNotification('未找到对应的PDF文件', 'warning');
            }
        }
    } catch (error) {
        console.error('获取法规信息失败:', error);
        showNotification('获取法规信息失败', 'error');
    }
}
```

---

## 📊 数据导入工具

创建一个脚本，自动将PDF分析结果导入数据库：

```python
# import_regulation_data.py
import json
import pymysql

def import_regulation_mapping(analysis_file, regulation_name):
    """导入法规-化学品页码映射"""
    
    # 读取分析结果
    with open(analysis_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        database='chemical_msds',
        charset='utf8mb4'
    )
    
    cursor = conn.cursor()
    
    # 获取法规文件ID
    cursor.execute("SELECT 编号 FROM 法规文件 WHERE 法规简称 = %s", (regulation_name,))
    regulation_id = cursor.fetchone()[0]
    
    # 导入映射
    for item in data['chemicals']:
        cas = item['cas']
        page = item['page']
        
        # 查找化学品ID
        cursor.execute("SELECT 编号 FROM 化学品 WHERE CAS号 = %s", (cas,))
        result = cursor.fetchone()
        
        if result:
            chemical_id = result[0]
            
            # 插入或更新映射
            cursor.execute("""
                INSERT INTO 化学品法规页码映射 
                (化学品编号, 法规文件编号, PDF页码, 列入状态)
                VALUES (%s, %s, %s, '列入')
                ON DUPLICATE KEY UPDATE PDF页码 = %s
            """, (chemical_id, regulation_id, page, page))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ 导入完成：{len(data['chemicals'])} 条记录")

if __name__ == '__main__':
    import_regulation_mapping(
        'pdf/易制爆危险化学品名录_analysis.json',
        '易制爆危险化学品名录'
    )
```

---

## 🎯 实施步骤

### 第1步：数据库准备
1. 执行SQL创建两个新表
2. 插入法规文件基础信息

### 第2步：PDF数据提取
1. 运行 `analyze_pdf.py` 分析所有PDF
2. 运行 `import_regulation_data.py` 导入页码映射

### 第3步：后端开发
1. 添加 `/api/regulations` 接口
2. 修改现有接口，返回化学品的法规信息

### 第4步：前端开发
1. 引入PDF.js库
2. 添加PDF查看器UI
3. 修改第15章格式化函数
4. 实现点击跳转逻辑

### 第5步：测试
1. 测试PDF打开和翻页
2. 测试页码跳转准确性
3. 测试多个法规文件切换

---

## 💡 优化建议

### 1. 性能优化
- PDF文件使用CDN加速
- 首次加载时预加载常用PDF
- 使用缓存避免重复加载

### 2. 用户体验
- 添加搜索高亮功能
- 支持键盘快捷键（方向键翻页）
- 添加书签功能
- 支持全屏模式

### 3. 数据完善
- 定期更新法规文件
- 使用OCR技术自动识别化学品位置
- 添加法规变更历史记录

---

## 🔍 技术栈

- **前端**: PDF.js, JavaScript, HTML5 Canvas
- **后端**: Flask, Python
- **数据处理**: PyPDF2, 正则表达式
- **数据库**: MySQL

---

## ⚠️ 注意事项

1. **PDF文件大小**：单个PDF不宜超过50MB，否则加载慢
2. **页码准确性**：需要人工抽查验证自动提取的页码
3. **法规更新**：法规文件更新时需要重新分析和导入
4. **浏览器兼容性**：PDF.js需要现代浏览器支持
5. **版权问题**：确保有权使用和分发这些法规PDF文件

---

## 📝 后续扩展

1. 支持PDF文字复制和注释
2. 支持导出化学品的法规合规报告
3. 添加法规对比功能
4. 支持移动端查看
5. 添加法规更新提醒功能

