# 🧪 危化品MSDS查询系统

专业化学品安全数据查询平台 - 极简设计，高效查询

---

## 🚀 快速开始

### 步骤1：安装依赖

```bash
cd new_db
双击运行：install_deps.bat
```

这将自动安装：
- Python依赖包（Flask, PyMySQL, requests等）
- Playwright浏览器（用于智能爬取）

### 步骤2：创建数据库

在MySQL命令行中执行：

```sql
mysql -u root -p1234

source C:\Users\Administrator.DESKTOP-URBQKM0\Desktop\huaxuepinshujuku\new_db\init_simple_db.sql
source C:\Users\Administrator.DESKTOP-URBQKM0\Desktop\huaxuepinshujuku\new_db\sample_data.sql

exit
```

### 步骤3：爬取化学品数据

```bash
双击运行：run_scraper.bat
```

选择模式：
- **[1]** 只爬取，保存为JSON
- **[2]** 爬取并直接导入数据库 ⭐ 推荐

输入URL示例：
```
http://www.hgmsds.com/weixin/msds-list-details?decrypt=3MIzS2IzVB%2BvKQnkqocW%2Fg%3D%3D
```

### 步骤4：启动Web查询

```bash
双击运行：start_web.bat
```

然后访问：**http://localhost:5001**

---

## 📦 文件说明

| 文件 | 用途 |
|------|------|
| `scrape_to_json.py` | 智能爬虫（从第一部分提取完整信息）|
| `run_scraper.bat` | 爬虫启动器 |
| `app.py` | Web应用后端 |
| `start_web.bat` | Web应用启动器 |
| `install_deps.bat` | 依赖安装工具 |
| `init_simple_db.sql` | 数据库初始化脚本 |

---

## 💡 使用技巧

### 命令行模式（高级用户）

```bash
# 只爬取
python scrape_to_json.py "URL"

# 爬取并导入
python scrape_to_json.py "URL" --import

# 指定数据库密码
python scrape_to_json.py "URL" --import --password yourpass
```

### 批量导入

创建一个PowerShell脚本：

```powershell
$urls = @(
    "http://www.hgmsds.com/weixin/msds-list-details?decrypt=xxx1",
    "http://www.hgmsds.com/weixin/msds-list-details?decrypt=xxx2"
)

foreach ($url in $urls) {
    python scrape_to_json.py "$url" --import
    Start-Sleep -Seconds 2
}
```

---

## 📊 数据库结构

### 4个核心表

1. **化学品** - 基本信息（CAS号、中文名、英文名、分子式、EC编号）
2. **化学品别名** - 别名和同义词
3. **MSDS文档** - 元数据（编制单位、日期、依据）
4. **MSDS章节** - 16个部分的完整内容

### 存储过程

```sql
CALL 查询化学品('甲醛');        -- 中文名
CALL 查询化学品('50-00-0');     -- CAS号
CALL 查询化学品('福尔马林');    -- 别名
```

---

## 🎨 功能特点

✅ **智能爬取** - 自动提取CAS号、别名、EC编号、分子式  
✅ **完整MSDS** - 16个部分全部爬取  
✅ **一键导入** - 爬取后直接导入数据库  
✅ **Web查询** - 专业界面，支持中文名/英文名/CAS号/别名  
✅ **折叠展示** - MSDS章节点击展开，节省空间  
✅ **JSON导入** - 支持Web界面上传JSON文件

---

## 🔧 常见问题

**Q: 爬取失败怎么办？**  
A: 检查网络连接，确保Playwright浏览器已安装（运行`install_deps.bat`）

**Q: 数据库导入报错？**  
A: 确保数据库已创建（执行`init_simple_db.sql`）且密码正确

**Q: CAS号显示"未找到"？**  
A: 某些化学品页面可能没有CAS号，系统会用中文名作为索引

**Q: 如何更新已有化学品？**  
A: 重新爬取相同CAS号的化学品，系统会自动更新数据

---

## 📚 技术栈

- **后端**: Python 3.x + Flask + PyMySQL
- **前端**: HTML5 + CSS3 + JavaScript
- **爬虫**: Playwright + BeautifulSoup4 + Requests
- **数据库**: MySQL 8.0+

---

## 📝 更新日志

### v2.0 (优化版)
- ✅ 从第一部分提取完整信息（CAS、别名、EC、分子式）
- ✅ 修复URL格式（msds-page-details, type=0-15）
- ✅ CAS号允许为空
- ✅ 批处理文件改为英文避免编码问题

### v1.0 (初版)
- ✅ 基础爬虫功能
- ✅ JSON数据导出
- ✅ Web查询界面

---

**祝使用愉快！** 🎉

