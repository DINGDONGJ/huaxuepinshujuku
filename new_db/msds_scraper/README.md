# MSDS智能爬虫工具

一键爬取化学品MSDS数据，支持保存为JSON或直接导入数据库。

---

## 📦 功能特点

- ✅ **智能提取** - 自动提取化学品名称、CAS号、英文名、分子式、别名等
- ✅ **完整爬取** - 爬取MSDS全部16个章节
- ✅ **图片下载** - 自动下载GHS危险标识和运输标志图片
- ✅ **两种模式** - 支持仅保存JSON或直接导入数据库
- ✅ **交互友好** - 批处理脚本提供菜单式操作
- ✅ **错误处理** - 详细的日志输出和错误提示

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装Python依赖包
pip install -r requirements.txt

# 下载Chromium浏览器驱动（约170MB）
playwright install chromium
```

### 2. 运行工具

#### **Windows用户（推荐）**

双击运行 `run_scraper.bat`，然后按照菜单提示操作：

```
========================================================
MSDS Scraper and Database Import Tool
========================================================

Please select mode:
[1] Scrape only (save as JSON)
[2] Scrape and import to database
[0] Exit
========================================================
```

#### **命令行用户**

```bash
# 模式1：只爬取，保存为JSON
python scrape_to_json.py "你的MSDS_URL"

# 模式2：爬取并导入数据库
python scrape_to_json.py "你的MSDS_URL" --import --password 你的数据库密码
```

---

## 📋 依赖说明

| 依赖包 | 版本要求 | 用途 |
|--------|---------|------|
| **requests** | ≥2.31.0 | HTTP请求 |
| **beautifulsoup4** | ≥4.12.0 | HTML解析 |
| **pymysql** | ≥1.1.0 | MySQL数据库连接 |
| **playwright** | ≥1.40.0 | 浏览器自动化 |

---

## 💾 输出文件结构

爬取成功后会生成以下文件：

```
msds_json/
├── 甲醛_50-00-0.json          # 化学品JSON数据
├── images/                     # 图片文件夹
│   ├── abc123def456.png       # GHS危险标识
│   └── xyz789ghi012.png       # 运输标志
└── ...
```

### JSON文件格式

```json
{
  "chemical_info": {
    "中文名": "甲醛",
    "英文名": "Formaldehyde",
    "CAS号": "50-00-0",
    "分子式": "CH2O",
    "EC编号": "200-001-8"
  },
  "aliases": ["福尔马林", "蚁醛"],
  "msds_meta": {
    "编制单位": "合规化学网",
    "编制日期": "2024-12-05",
    "编制依据": "GB/T 16483, GB/T 17519"
  },
  "msds_chapters": [
    {
      "章节序号": 1,
      "章节标题": "化学品及企业标识",
      "内容": "..."
    },
    ...
  ]
}
```

---

## 🗄️ 数据库导入

如果选择直接导入数据库（模式2），需要确保：

1. **MySQL/MariaDB已运行**
2. **数据库已创建** - 运行 `init_simple_db.sql` 创建数据库结构
3. **密码正确** - 默认密码为 `1234`，可通过 `--password` 参数修改

导入成功后，数据会保存到以下表：
- `化学品` - 基本信息
- `化学品别名` - 别名列表
- `MSDS文档` - 文档元数据
- `MSDS章节` - 16个章节内容

---

## 🔧 命令行参数

```bash
python scrape_to_json.py [URL] [OPTIONS]

参数:
  URL                    MSDS页面URL（必需）
  --import               爬取后直接导入数据库
  --password, -p         数据库密码（默认：1234）
  --output, -o           JSON输出目录（默认：msds_json）
  
示例:
  python scrape_to_json.py "http://example.com/msds?decrypt=xxx"
  python scrape_to_json.py "http://example.com/msds?decrypt=xxx" --import
  python scrape_to_json.py "http://example.com/msds?decrypt=xxx" --import -p mypass
```

---

## ⚠️ 常见问题

### 1. Playwright安装失败

**问题**：`playwright install chromium` 下载失败

**解决**：
```bash
# 设置国内镜像
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
playwright install chromium
```

### 2. 数据库连接失败

**问题**：`Database error: (2003, "Can't connect to MySQL server")`

**解决**：
1. 确保MySQL/MariaDB服务已启动
2. 检查数据库密码是否正确
3. 确认数据库名称为 `危化品简化数据库`

### 3. 爬取失败

**问题**：部分章节返回错误

**解决**：
1. 检查网络连接
2. 确认URL格式正确（需要包含 `decrypt` 参数）
3. 网站可能临时不可用，稍后重试

---

## 📞 技术支持

如有问题，请检查：
1. Python版本 ≥ 3.7
2. 所有依赖已正确安装
3. 网络连接正常
4. URL格式正确

---

## 📄 许可证

本工具仅供学习和研究使用，请遵守目标网站的使用条款。
