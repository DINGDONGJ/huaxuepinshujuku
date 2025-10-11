# 危险化学品AI应用的数据结构设计

# 1. 项目背景与目标

本系统旨在构建一个基于危险化学品管理的智能问答平台：用户输入化学品名称（如“甲醛”），系统自动检索相关数据源并输出该化学品的安全管理和使用信息。信息来源包括化学品安全技术说明书(MSDS/SDS)与相关法规条文。具体地，系统要根据输入返回管理要求（相关法规条款、编号、原文及PDF链接）、使用要求（操作规程概要、个人防护装备）、识别/许可信息（UN编号、运输类别、是否剧毒/易制爆等）、应急处理建议（MSDS中第4-6部分内容提炼）、辅助信息（GHS象形图、危险说明语和理化性质）等内容。[1][2]中均指出MSDS包含化学品的燃爆性能、健康危害、安全操作及应急措施等十六大内容，是获取急救、防护、使用等信息的重要来源。

# 2. 数据结构总体设计

整个系统采用MySQL关系型数据库作为存储后端。数据来源主要有两类：MSDS数据和法规条款数据。MSDS数据按照国际标准共分16个章节（见[3][4]），系统需存储每份MSDS的文档信息及各章节内容；法规数据以“法规/条例/标准”类PDF文档形式存在，需抽取其中的条款索引和内容并存储，同时记录可跳转的PDF锚点链接。

总体来说，数据库表主要分为：化学品主表、MSDS文档表、MSDS章节表、GHS危害分类表、运输分类表、危险品目录标识表、法规条款表、化学品与条款映射表等。各表之间通过外键关联（如MSDS文档表关联到化学品表，化学品表关联到分类表和目录表等），实现不同数据源的整合。

# 3. 数据库表设计

- chemicals (化学品表): 存储化学品基本身份信息。  
- id (化学品 ID，主键)：整型，自增。用于表间关联。  
- cas_number (CAS号): VARCHAR, 来源于MSDS第1部分，用于唯一标识化学品。  
- name_cn (化学品中文名称):VARCHAR, 来自MSDS第1部分或用户输入。  
- name_en (英文名称): VARCHAR, 同样来自 MSDS 第 1 部分。  
- synonyms (同义名): TEXT, 从 MSDS 第 1 部分或数据库补充, 同义词用于扩展检索。  
- 说明：该表作为化学品主表，用于关联MSDS文档、分类、运输、法规等信息，是其他表的参照基础。  
- msds Documents (MSDS 文档表): 存储 MSDS 文档的元信息。

- id (MSDS 文档 ID，主键)。  
- chemical_id (化学品 ID，外键)：关联 chemicals.id。  
doc_title(文档标题):VARCHAR,如“SDS for 甲醛”。  
- language (语言): VARCHAR, 如 “中文” 或 “English”。  
version (版本号/日期):VARCHAR, 可记录 MSDS 版本或日期。  
- 说明：一份 MSDS 文档属于一个化学品，可能有多个语言或版本。此表记录 MSDS 文件的摘要信息，与章节表通过 ID 关联。  
- msds_sections (MSDS章节表): 存储MSDS的每章内容。  
- id（章节ID，主键）。  
- msds_id (MSDS 文档 ID, 外键): 关联 msds Documents.id。  
- section_number (章节号): INT, 1~16, 对应 MSDS 的 16 大部分。  
- title (章节标题):VARCHAR, 如“第4部分: 急救措施”。  
- content (章节内容): TEXT, 存放完整文本信息。  
- 来源：内容直接来自 MSDS 报告，每章节一段。如第 8 部分包含“个人防护措施”，第 14 部分包含“运输信息”等[4][5]。  
- 说明：按章节存储 MSDS 内容方便检索和结构化查询。与 msds Documents 表形成一对多关系，便于查询化学品对应的 MSDS 内容。  
- ghs_classifications (GHS 分类表): 存储化学品的 GHS 危害分类和对应声明。  
- id（分类ID，主键）。  
- chemical_id（化学品ID，外键）。  
- classification (危害分类):VARCHAR, 如“急性毒性（吸入）3类”、“致癌性1B类”等。来源MSDS第2部分或第三方数据库。  
- hazard_statement (H 语句): VARCHAR 或 TEXT, 存储对应的危险说明语代码（如“H350，H332”）及中文释义（可选）。  
- 说明：GHS 分类表用于体现化学品的危害类别，例如甲醛具有可燃液体和急性毒性分类，其相关 H 语句存于此表。该表与化学品表一对多关联（一个化学品可有多个分类/语句）。MSDS 第 2 部分通常给出分类和 H/P 语句[6]。  
- transport_classifications (运输分类表): 存储化学品的联合国编号及运输信息。  
- id (ID, 主键)。  
- chemical_id (化学品 ID，外键)。  
- un_number (UN编号): VARCHAR, 如“UN1198”。可来源于MSDS第14部分或运输部规定。  
- un_name (联合国运输名称): VARCHAR, 如 “Formalin” 或相应中文。

- hazard_class (危险类别):VARCHAR, 如“3类易燃液体”, 来源MSDS第14部分或法规。  
- packing_group (包装类别):VARCHAR, 如“II”、“III”。  
- marine POLLUTANT (海洋污染): BOOL, 是否为海洋污染物。  
- special (特殊运输说明): TEXT, 可存特殊要求或标志。  
- 来源：主要来自 MSDS 第 14 部分[5]或中国交通运输部《危险货物运输规则》。  
• 说明：用于检索运输许可和标志信息，与化学品表一对一或一对多关联。示例：甲醛水溶液 UN 编号为 1198，类别 3 类易燃液体[7]。  
- hazard_catalog_flags (危险目录标志表): 记录化学品在国家危险品目录中的标志。  
- id (ID, 主键)。  
- chemical_id (化学品 ID，外键)。  
- flag_name (标志名称): VARCHAR, 如 “剧毒化学品”、“易制爆物质”、“易制毒物质”、“易燃液体”等。  
- 说明：用于标识化学品是否属于特定监管目录。比如甲醇标记“易燃液体”，某些化学品标记“剧毒”。此表与化学品表一对多关联（一个化学品可有多个标志）。标志信息来自国家目录或法规，便于快速判断是否需要特许或限制。  
- clauses (法规条款表): 存储法规/条例/标准的条款索引和内容。  
- id（条款ID，主键）。  
- law_name (法规名称):VARCHAR, 如“《危险化学品安全管理条例》”。  
- clause_number (条文编号): VARCHAR, 如 “第 29 条”。  
- clause_text (条文原文): TEXT, 存储具体规定内容。  
- pdf_link (PDF链接/锚点):VARCHAR, 存储对应法规PDF文件的URL或定位信息。  
• 说明：该表用于保存各法律法规的条款内容和索引，方便关联查询。每条记录对应一条法规规定（如[8]中的第29条），其中pdf_link用于跳转到官方PDF的具体页（可存储如“文件名.pdf#page=12”）。  
- chem_clause_map (化学品-条款映射表): 关联化学品与适用法规条款。  
- chemical_id（化学品ID，外键）。  
- clause_id (条款ID，外键)。  
• 说明：多对多映射表，记录哪些条款适用于哪些化学品。例如根据法规，涉及甲醛的使用许可、生产要求等条款在此关联。查询时可以快速定位某化学品关联的法规条款。

各表通过如上外键紧密关联：msds Documents. chemical_id  $\rightarrow$  chemicals.id,

msds_sections.msds_id  $\rightarrow$  msds_documents.id,

ghs_classifications. chemical_id  $\rightarrow$  chemicals.id 等，形成完整的化学品安全信息体系。

# 4. “快速建库工具”模块设计

- 功能说明：  
- MSDS 导入：用户从合规化学平台复制一个化学品的 MSDS 页面内容，按章节粘贴到系统提供的文本框内（每个章节对应一个输入框）。例如将第 1 节粘贴到“物质与厂商信息”框，第 4 节粘贴到“急救措施”框等。  
- 法规PDF导入：用户上传包含法规条款的PDF文件。系统自动提取PDF文本，识别条款编号和内容，生成可点击的索引与条款链接。  
- 信息处理流程：  
- 数据输入：用户将 MSDS 各章节文本或法规 PDF 上传至系统。  
- 文本解析：系统对 MSDS 文本采用自然语言处理或正则匹配，提取关键信息（如 CAS 号、化学品名称、成分、危害声明、应急操作指导等），并自动填充到对应字段；对法规 PDF 使用 PDF 解析库（如 PyMuPDF）提取文本和页码，根据段落层次识别条款（例如匹配“第×条”），生成条款记录和 PDF 锚点。  
- 入库存储：解析后的结构化数据写入数据库各表：MSDS 章节存入 msdsSections，提取的化学品基础信息存入 chemicals，GHS 分类存入 ghs classifications，法规条款存入 clauses，并建立必要的映射关系。  
- 人工校对：系统可提供简单界面让用户核对自动抽取结果并修正错误，确保数据准确。  
- 简单Web界面示例（HTML结构）：

```html
<!DOCTYPE html>   
<html>   
<head><title>快速建库工具</title></head>   
<body>   
<h2>MSDS 文档导入</h2>   
<form id="msdsForm">   
<label>第1节 化学品与厂商信息：</label><br>   
<textarea name  $=$  "section1" rows  $=$  "4" cols  $=$  "80"> </textarea><br>   
<label>第2节 危害辨识：</label><br>   
<textarea name  $=$  "section2" rows  $=$  "4" cols  $=$  "80"> </textarea><br>   
<!--中间略-->   
<label>第16节 其他信息：</label><br>   
<textarea name  $=$  "section16" rows  $=$  "4" cols  $=$  "80"> </textarea><br>   
<button type  $=$  "button" onclick  $=$  "submitMSDS())">解析并保存</button>   
</form>
```

```txt
<h2>法规条款导入</h2>
<form id="lawForm" enctype="multipart/form-data">
    <label>上传法规PDF：</label>
    <input type="file" name="law(pdf" accept="application/pdf"><br><br>
        <button type="button" onclick="uploadPDF()">上传解析</button>
    </form>
</body>
</html>
```

以上界面示例仅为 HTML 结构，实际部署时会配合 JavaScript 或后端处理完成文本解析与数据提交。

# 5. 示例数据与输出示例

以用户输入“甲醛”为例，系统查询并返回如下结构化信息：

- 管理要求（关联法规条款）：  
- 《危险化学品安全管理条例》第29条：“使用危险化学品从事生产并且使用量达到规定数量的化工企业，应当取得危险化学品安全使用许可证”[8]。例如，若单位甲醛使用量高于标准，必须办理安全使用许可证。  
- （可扩展）其它相关条款：如第15条规定“危险化学品生产企业应当提供符合本单位危险化学品的安全技术说明书”[9]。每条均附原文和PDF跳转链接。  
- 使用要求：  
- 操作注意：MSDS 建议“密闭操作，提供充分的局部排风”，“操作人员必须接受培训，严格遵守操作规程”[10]。  
- PPE防护：建议操作人员佩戴自给过滤式防毒面具（全面罩）、穿戴橡胶耐酸碱服、戴橡胶手套等[11]；工作场所应使用防爆通风设备，禁止烟火。  
- 识别/许可信息：  
- UN编号：UN 1198[7]，属于联合国3类易燃液体。  
- 运输类别：CLASS 3，Packing Group III[7]，按规定需要危险品标志和相关运输许可。  
- 剧毒/易制爆标志：甲醛不属于国家剧毒化学品或易制爆化学品目录，无需相关特许；但其具有毒性和刺激性，应注意通风防护。  
- 应急处理建议（提炼自MSDS第4-6部分）：  
- 急救措施：如皮肤接触，用大量水冲洗至少15分钟并就医；吸入后立即移至空气新鲜处，必要时进行人工呼吸[12]。

- 灭火措施：甲醛遇明火会燃烧爆炸（闪点  $37 \%$  浓度时约  $50^{\circ} \mathrm{C}[13]$ ），火灾时应使用水雾、抗溶性泡沫、干粉或二氧化碳灭火[14]；消防人员需穿戴自给式呼吸器和防护服。  
- 泄漏处理：泄漏时应立即疏散并隔离现场，禁止火种进入。清理人员应戴正压呼吸器、穿防酸碱服，优先切断泄漏源；少量泄漏可用砂土或其它惰性物质覆盖，大量泄漏应构筑围堤收容，再用泡沫覆盖并降温[15]。  
辅助信息：  
• GHS 象形图: 甲醛属于急性毒性和健康危害类别, 应挂骷髅与交叉骨 (急毒)和人体象形（健康危害）图标。  
- 危险说明语（H/P 语句）：常见 H 语句包括 H350 “可能致癌”、H332 “吸入有害”等[6]（对应中文解释“可能致癌”、“吸入有害”）。  
- 理化特性: 无色有刺激性气体 (通常以水溶液形式存在); 熔点  $-92^{\circ} \mathrm{C}$ , 沸点  $-19.4^{\circ} \mathrm{C}[16] ; 37 \%$  水溶液闪点  $50^{\circ} \mathrm{C}[13] ;$  蒸气压高  $(13.3 \mathrm{kPa} @ -57^{\circ} \mathrm{C})$ ,易燃易形成爆炸性混合物。以上参数用于评价泄漏危害和储存安全[17][13]。

# 6. 数据库初始化 SQL 脚本 (init_msd.sql)

-- 建表：化学品基本信息

```sql
CREATE TABLE chemicals (
id INT AUTO_INCREMENT PRIMARY KEY,
cas_numberVARCHAR(20) NOT NULL, -- CAS号
name_cnVARCHAR(100) NOT NULL, -- 中文名称
name_enVARCHAR(100), -- 英文名称
synonyms TEXT -- 同义名称
);
```

-- 建表：MSDS 文档信息

```sql
CREATE TABLE msds Documents (
id INT AUTO_INCREMENT PRIMARY KEY,
chemical_id INT NOT NULL, -- 关联化学品
doc_titleVARCHAR(200), -- 文档标题
languageVARCHAR(20), -- 文档语言
versionVARCHAR(50), -- 版本/日期
FOREIGN KEY (chemical_id) REFERENCES chemicals(id);
);
```

-- 建表：MSDS各章节内容

```txt
CREATE TABLE msdsSections (
id INT AUTO_INCREMENT PRIMARY KEY,
msds_id INT NOT NULL,
section_number INT NOT NULL,
titleVARCHAR(100),
```

```sql
content TEXT, --章节内容  
FOREIGN KEY (msds_id) REFERENCES msds/documents(id);
```

# -- 建表：GHS 危害分类

```sql
CREATE TABLE ghs classifications ( id INT AUTO_INCREMENT PRIMARY KEY, chemical_id INT NOT NULL, classificationVARCHAR(100), --危害分类（如“急性毒性3类”） hazard_statementssVARCHAR(255), --危险说明语代码（如"H350,H332") FOREIGN KEY (chemical_id) REFERENCES chemicals(id);
```

# --建表：运输分类信息

```sql
CREATE TABLE transport_classifications (
id INT AUTO_INCREMENT PRIMARY KEY,
chemical_id INT NOT NULL,
un_numberVARCHAR(10), -- UN编号（如"UN1198")
un_nameVARCHAR(100), -- UN运输名称
hazard_class VARCHAR(50), -- 危险类别（如"3类易燃液体")
packing_group VARCHAR(10), -- 包装类别(I, II, III)
marine POLLUTANT BOOLEAN, -- 海洋污染物
special TEXT, -- 特殊运输说明
FOREIGN KEY (chemical_id) REFERENCES chemicals(id);
);
```

# --建表：危险目录标志

```sql
CREATE TABLE hazard_catalog_flags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chemical_id INT NOT NULL,
    flag_nameVARCHAR(50), -- 标志名（如"易燃液体","剧毒化学品")
    FOREIGN KEY (chemical_id) REFERENCES chemicals(id);
);
```

# -- 建表：法规条款

```sql
CREATE TABLE clauses (
id INT AUTO_INCREMENT PRIMARY KEY,
law_nameVARCHAR(100), --法规名称
clause_numberVARCHAR(20), --条款编号（如"第29条")
clause_text TEXT, --条款原文
pdf_linkVARCHAR(255) --PDF文件链接或锚点
);
```

# -- 建表：化学品与法规条款映射

```sql
CREATE TABLE chem_clause_map (
    chemical_id INT NOT NULL,
    clause_id INT NOT NULL,
    PRIMARY KEY (chemical_id, clause_id),
    FOREIGN KEY (chemical_id) REFERENCES chemicals(id),
    FOREIGN KEY (clause_id) REFERENCES clauses(id);
);
```

# -- 示例数据插入

-- 化学品示例：1=乙醇，2=甲醛

```sql
INSERT INTO chemicals (cas_number, name_cn, name_en, synonyms) VALUES ('64-17-5', '乙醇', 'Ethanol', '酒精;无水乙醇'), ('50-00-0', '甲醛', 'Formaldehyde', '福尔马林;蚁醛');
```

# -- MSDS 文档示例

INSERT INTO msds Documents (chemical_id, doc_title, language, version) VALUES

(1, '乙醇 安全数据表', '中文', '2024版'),  
(2, ‘甲醛 安全数据表’, ‘中文’, ‘2024版’);

-- MSDS 章节示例（只插入第 1 节和第 14 节作为示例）

INSERT INTO msdsSections (msds_id, section_number, title, content) VALUES

(1，1，‘化学品与厂商信息’，‘化学品名称：乙醇；CAS号：64-17-5；供货商：XXX公司；’），

(1, 14, '运输信息', 'UN编号: 1170; 联合国运输名称: ETHANOL; 运输类别: 3类易燃液体; 包装类别 II; ')),  
(2，1，‘化学品与厂商信息’，‘化学品名称：甲醛；CAS号：50-00-0；供货商：YYY公司；’)，  
(2, 14, '运输信息', 'UN编号: 1198; 联合国运输名称: Formalin; 运输类别: 3类易燃液体; 包装类别 III; )；

# -- GHS分类示例

INSERT INTO ghs classifications (chemical_id, classification, hazard_statement s) VALUES

(1, '易燃液体 2 类', 'H225'),  
(2, '急性毒性 3 类 (口服)', 'H302, H314');

# -- 运输分类示例

INSERT INTO transport_classifications (chemical_id, un_number, un_name, hazard_class, packing_group, marine POLLUTANT) VALUES

(1，'UN1170'，'ETHANOL'，'3类易燃液体'，'II'，FALSE)，  
(2, 'UN1198', 'Formalin', '3 类 易燃液体', 'III', FALSE);

# - 危险目录标志示例

INSERT INTO hazard_catalog_flags (chemical_id, flag_name) VALUES

(1, '易燃液体'),  
(2，‘易燃液体’）；

# -- 法规条款示例

INSERT INTO clauses (law_name, clause_number, clause_text, pdf_link) VALUES ('危险化学品安全管理条例', '第十五条',

'危险化学品生产企业应当提供与其生产的危险化学品相符的化学品安全技术说明书，并在包装上粘贴标签。',  
'http://www.gov.cn/gongbao/2011/content/2011-03/02/content_1825120.htm#p100'), ('危险化学品安全管理条例', '第二十九条',  
’使用危险化学品从事生产并且使用量达到规定数量的化工企业（不包括生产企业）应当取得危险化学品安全使用许可证。’，

' http://www.gov.cn/gongbao/2011/content/2011-03/02/content_1825120.htm#p159');

# -- 化学品与条款映射示例

INSERT INTO chem_clause_map (chemical_id, clause_id) VALUES

(1, 1), -- 乙醇关联条例第 15 条  
(2, 2); -- 甲醛关联条例第 29 条

以上 SQL 脚本创建了各表结构并插入了部分示例数据（乙醇和甲醛），用于初始测试和开发参考。各字段和表间关系对照前述设计，能够支持 MSDS 内容和法规条款的综合查询。