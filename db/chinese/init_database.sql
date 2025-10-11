-- ============================================================================
-- 危化品大模型数据库 - 中文版初始化脚本
-- ============================================================================
-- 版本: 2.0 (中文表名和列名)
-- 创建时间: 2025-10-09
-- 数据库: MySQL 8.0+
-- 字符集: utf8mb4_0900_ai_ci
-- ============================================================================

-- ============================================================================
-- 1. 数据库创建与配置
-- ============================================================================

-- 删除已存在的数据库（谨慎使用）
-- DROP DATABASE IF EXISTS 危化品数据库;

-- 创建数据库
CREATE DATABASE IF NOT EXISTS 危化品数据库
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

-- 使用数据库
USE 危化品数据库;

-- 设置时区为UTC
SET time_zone = '+00:00';

-- ============================================================================
-- 2. A层：化学品主数据表
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2.1 化学品主表
-- ----------------------------------------------------------------------------
CREATE TABLE 化学品 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '化学品ID',
    CAS号 VARCHAR(32) NOT NULL UNIQUE COMMENT 'CAS号，如 64-17-5',
    中文名 VARCHAR(256) NOT NULL COMMENT '中文名称（主显示名）',
    英文名 VARCHAR(256) COMMENT '英文主名',
    分子式 VARCHAR(64) COMMENT '分子式',
    EC编号 VARCHAR(64) COMMENT 'EC编号',
    是否有效 TINYINT DEFAULT 1 COMMENT '是否有效：1=有效，0=无效',
    备注 TEXT COMMENT '备注信息',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    创建人 VARCHAR(128) COMMENT '创建人',
    更新人 VARCHAR(128) COMMENT '更新人',
    INDEX 索引_中文名 (中文名(191)),
    INDEX 索引_英文名 (英文名(191)),
    INDEX 索引_有效状态 (是否有效)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='化学品主数据表';

-- ----------------------------------------------------------------------------
-- 2.2 化学品别名表
-- ----------------------------------------------------------------------------
CREATE TABLE 化学品别名 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '别名ID',
    化学品编号 BIGINT NOT NULL COMMENT '化学品ID',
    名称 VARCHAR(256) NOT NULL COMMENT '别名/同义词（中英混合）',
    语言 ENUM('中文','英文','其他') DEFAULT '中文' COMMENT '语言类型',
    是否主要名称 TINYINT DEFAULT 0 COMMENT '是否主要名称：1=是，0=否',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX 索引_化学品 (化学品编号),
    FULLTEXT INDEX 全文索引_名称 (名称) COMMENT '名称全文索引',
    CONSTRAINT 外键_别名_化学品 FOREIGN KEY (化学品编号) REFERENCES 化学品(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='化学品别名表';

-- ----------------------------------------------------------------------------
-- 2.3 GHS危害分类表
-- ----------------------------------------------------------------------------
CREATE TABLE GHS分类 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'GHS分类ID',
    化学品编号 BIGINT NOT NULL COMMENT '化学品ID',
    危害类别 VARCHAR(128) NOT NULL COMMENT '危害类别，如：易燃液体',
    类别编号 VARCHAR(64) COMMENT '类别编号，如：类别2、类别3',
    信号词 VARCHAR(32) COMMENT '信号词：危险/警告',
    象形图 JSON COMMENT '象形图代码数组，如：["GHS02","GHS07"]',
    H代码 JSON COMMENT 'H语句代码数组，如：["H225","H319"]',
    P代码 JSON COMMENT 'P语句代码数组，如：["P210","P233"]',
    数据来源 VARCHAR(128) COMMENT '数据来源，如：MSDS、标准',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX 索引_化学品 (化学品编号),
    CONSTRAINT 外键_GHS_化学品 FOREIGN KEY (化学品编号) REFERENCES 化学品(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='GHS危害分类表';

-- ----------------------------------------------------------------------------
-- 2.4 运输分类表
-- ----------------------------------------------------------------------------
CREATE TABLE 运输分类 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '运输分类ID',
    化学品编号 BIGINT NOT NULL COMMENT '化学品ID',
    UN编号 VARCHAR(16) COMMENT 'UN编号，如：UN1170',
    UN运输名称 VARCHAR(256) COMMENT 'UN运输正式名称',
    主要危险类别 VARCHAR(64) COMMENT '主要危险类别，如：3（易燃液体）',
    次要危险类别 VARCHAR(64) COMMENT '次要危险类别',
    包装类别 VARCHAR(8) COMMENT '包装类别：I/II/III',
    是否海洋污染物 TINYINT COMMENT '是否海洋污染物：1=是，0=否',
    运输注意事项 TEXT COMMENT '运输注意事项摘要',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX 索引_化学品 (化学品编号),
    INDEX 索引_UN编号 (UN编号),
    CONSTRAINT 外键_运输_化学品 FOREIGN KEY (化学品编号) REFERENCES 化学品(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='运输分类表';

-- ----------------------------------------------------------------------------
-- 2.5 危险品目录标识表
-- ----------------------------------------------------------------------------
CREATE TABLE 危险品目录标识 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '目录标识ID',
    化学品编号 BIGINT NOT NULL COMMENT '化学品ID',
    目录名称 VARCHAR(128) NOT NULL COMMENT '目录标识，如：危化品目录2015、易制爆2011、重点监管',
    是否列入 TINYINT NOT NULL COMMENT '是否列入：1=列入，0=未列入',
    参考文号 VARCHAR(256) COMMENT '公告/文号',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX 索引_化学品 (化学品编号),
    UNIQUE KEY 唯一键_目录 (化学品编号, 目录名称),
    CONSTRAINT 外键_目录_化学品 FOREIGN KEY (化学品编号) REFERENCES 化学品(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='危险品目录标识表';

-- ============================================================================
-- 3. B层：文档与条款管理表
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 监管机构表
-- ----------------------------------------------------------------------------
CREATE TABLE 监管机构 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '机构ID',
    名称 VARCHAR(256) NOT NULL COMMENT '监管/标准制定机构名称',
    国家地区 VARCHAR(128) COMMENT '国家/地区',
    网址 VARCHAR(512) COMMENT '官方网站',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX 索引_机构名称 (名称(191))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='监管机构表';

-- ----------------------------------------------------------------------------
-- 3.2 法规文档表
-- ----------------------------------------------------------------------------
CREATE TABLE 法规文档 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '文档ID',
    文档类型 ENUM('法律','法规','标准') NOT NULL COMMENT '文档类型',
    标题 VARCHAR(512) NOT NULL COMMENT '文档标题',
    简称 VARCHAR(256) COMMENT '简称',
    发布机构编号 BIGINT COMMENT '发布机构ID',
    发布日期 DATE COMMENT '发布日期',
    生效日期 DATE COMMENT '生效日期',
    状态 ENUM('草稿','有效','废止') DEFAULT '有效' COMMENT '状态',
    官方链接 VARCHAR(1024) COMMENT '官方链接',
    文件地址 VARCHAR(1024) COMMENT '文件存储地址',
    校验值 VARCHAR(128) COMMENT '文件校验值',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    创建人 VARCHAR(128) COMMENT '创建人',
    更新人 VARCHAR(128) COMMENT '更新人',
    INDEX 索引_文档类型日期 (文档类型, 生效日期),
    INDEX 索引_标题 (标题(191)),
    INDEX 索引_状态 (状态),
    CONSTRAINT 外键_文档_机构 FOREIGN KEY (发布机构编号) REFERENCES 监管机构(编号) 
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='法规文档表';

-- ----------------------------------------------------------------------------
-- 3.3 文档地域管辖表
-- ----------------------------------------------------------------------------
CREATE TABLE 文档地域管辖 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '地域管辖ID',
    文档编号 BIGINT NOT NULL COMMENT '文档ID',
    国家 VARCHAR(128) NOT NULL COMMENT '国家',
    省份 VARCHAR(128) COMMENT '省份',
    城市 VARCHAR(128) COMMENT '城市',
    适用范围说明 VARCHAR(256) COMMENT '适用范围说明',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX 索引_文档 (文档编号),
    INDEX 索引_地域 (国家, 省份, 城市),
    CONSTRAINT 外键_地域_文档 FOREIGN KEY (文档编号) REFERENCES 法规文档(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='文档地域管辖表';

-- ----------------------------------------------------------------------------
-- 3.4 文档版本表
-- ----------------------------------------------------------------------------
CREATE TABLE 文档版本 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '版本ID',
    文档编号 BIGINT NOT NULL COMMENT '文档ID',
    版本标签 VARCHAR(64) NOT NULL COMMENT '版本标签，如：2023修订、v2.0',
    发布日期 DATE COMMENT '发布日期',
    是否当前版本 TINYINT DEFAULT 1 COMMENT '是否当前版本：1=是，0=否',
    变更日志 TEXT COMMENT '变更日志',
    文件地址 VARCHAR(1024) COMMENT '文件存储地址',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX 索引_文档 (文档编号),
    INDEX 索引_当前版本 (是否当前版本),
    CONSTRAINT 外键_版本_文档 FOREIGN KEY (文档编号) REFERENCES 法规文档(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='文档版本表';

-- ----------------------------------------------------------------------------
-- 3.5 法规条款表
-- ----------------------------------------------------------------------------
CREATE TABLE 法规条款 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '条款ID',
    版本编号 BIGINT NOT NULL COMMENT '文档版本ID',
    条款编号 VARCHAR(64) COMMENT '条/款/项编号',
    标题 VARCHAR(512) COMMENT '条款标题',
    内容 LONGTEXT NOT NULL COMMENT '条文全文',
    分类 ENUM('管理要求','使用要求','识别许可','应急措施','其他') 
        DEFAULT '其他' COMMENT '条款分类',
    链接 VARCHAR(1024) COMMENT '条款锚点链接',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    创建人 VARCHAR(128) COMMENT '创建人',
    更新人 VARCHAR(128) COMMENT '更新人',
    INDEX 索引_版本 (版本编号),
    INDEX 索引_分类 (分类),
    FULLTEXT INDEX 全文索引_条款 (标题, 内容),
    CONSTRAINT 外键_条款_版本 FOREIGN KEY (版本编号) REFERENCES 文档版本(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='法规条款表';

-- ============================================================================
-- 4. C层：映射与可拼装单元
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 4.1 化学品条款映射表（核心！）
-- ----------------------------------------------------------------------------
CREATE TABLE 化学品条款映射 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '映射ID',
    化学品编号 BIGINT NOT NULL COMMENT '化学品ID',
    条款编号 BIGINT NOT NULL COMMENT '条款ID',
    相关度评分 DECIMAL(5,2) DEFAULT 1.00 COMMENT '相关度评分，范围0.00-99.99',
    标签 VARCHAR(64) COMMENT '标签，如：许可、储存、运输、限量',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY 唯一键_化学品条款 (化学品编号, 条款编号),
    INDEX 索引_化学品 (化学品编号),
    INDEX 索引_条款 (条款编号),
    INDEX 索引_评分 (相关度评分 DESC),
    CONSTRAINT 外键_映射_化学品 FOREIGN KEY (化学品编号) REFERENCES 化学品(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT 外键_映射_条款 FOREIGN KEY (条款编号) REFERENCES 法规条款(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='化学品条款映射表';

-- ----------------------------------------------------------------------------
-- 4.2 操作规程库
-- ----------------------------------------------------------------------------
CREATE TABLE 操作规程库 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '操作规程ID',
    标题 VARCHAR(256) NOT NULL COMMENT '操作规程名称',
    化学品编号 BIGINT COMMENT '化学品ID，为NULL表示通用规程',
    适用范围 ENUM('储存','操作','处置','防护','通风','其他') NOT NULL 
        COMMENT '适用范围',
    版本标签 VARCHAR(64) COMMENT '版本号',
    正文 LONGTEXT COMMENT '操作规程正文',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX 索引_化学品 (化学品编号),
    INDEX 索引_范围 (适用范围),
    CONSTRAINT 外键_规程_化学品 FOREIGN KEY (化学品编号) REFERENCES 化学品(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='操作规程库';

-- ----------------------------------------------------------------------------
-- 4.3 操作规程步骤表
-- ----------------------------------------------------------------------------
CREATE TABLE 操作规程步骤 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '步骤ID',
    规程编号 BIGINT NOT NULL COMMENT '操作规程ID',
    步骤序号 INT NOT NULL COMMENT '步骤序号',
    步骤内容 TEXT NOT NULL COMMENT '步骤内容',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX 索引_规程步骤 (规程编号, 步骤序号),
    CONSTRAINT 外键_步骤_规程 FOREIGN KEY (规程编号) REFERENCES 操作规程库(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='操作规程步骤表';

-- ----------------------------------------------------------------------------
-- 4.4 应急卡片表
-- ----------------------------------------------------------------------------
CREATE TABLE 应急卡片 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '应急卡片ID',
    化学品编号 BIGINT COMMENT '化学品ID，为NULL表示通用应急卡',
    类型 ENUM('急救措施','消防措施','泄漏处置') NOT NULL COMMENT '应急类型',
    内容 LONGTEXT NOT NULL COMMENT '应急措施内容',
    版本标签 VARCHAR(64) COMMENT '版本号',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX 索引_化学品 (化学品编号),
    INDEX 索引_类型 (类型),
    CONSTRAINT 外键_应急_化学品 FOREIGN KEY (化学品编号) REFERENCES 化学品(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='应急卡片表';

-- ============================================================================
-- 5. D层：MSDS数据（16部分）
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 5.1 MSDS文档头表
-- ----------------------------------------------------------------------------
CREATE TABLE MSDS文档 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'MSDS文档ID',
    化学品编号 BIGINT NOT NULL UNIQUE COMMENT '化学品ID（一对一）',
    编制单位 VARCHAR(256) COMMENT '提供者/编制单位',
    联系方式 JSON COMMENT '提供者联系方式（JSON格式）',
    编制人 VARCHAR(256) COMMENT '编制人',
    编制日期 DATE COMMENT '编制日期',
    编制依据 VARCHAR(256) COMMENT '编制依据标准，如：GB/T 17519、GB/T 16483',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX 索引_化学品 (化学品编号),
    CONSTRAINT 外键_MSDS_化学品 FOREIGN KEY (化学品编号) REFERENCES 化学品(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='MSDS文档头表';

-- ----------------------------------------------------------------------------
-- 5.2 MSDS章节表（16部分）
-- ----------------------------------------------------------------------------
CREATE TABLE MSDS章节 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'MSDS章节ID',
    文档编号 BIGINT NOT NULL COMMENT 'MSDS文档ID',
    章节序号 TINYINT NOT NULL COMMENT '章节号，1-16',
    章节标题 VARCHAR(256) NOT NULL COMMENT '章节标题，如：急救措施',
    内容 LONGTEXT COMMENT '章节原文（HTML/Markdown/纯文本）',
    结构化数据 JSON COMMENT '结构化内容（JSON格式）',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY 唯一键_文档章节 (文档编号, 章节序号),
    INDEX 索引_章节序号 (章节序号),
    FULLTEXT INDEX 全文索引_内容 (章节标题, 内容),
    CONSTRAINT 外键_章节_文档 FOREIGN KEY (文档编号) REFERENCES MSDS文档(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='MSDS章节表（16部分）';

-- ----------------------------------------------------------------------------
-- 5.3 MSDS理化特性表
-- ----------------------------------------------------------------------------
CREATE TABLE MSDS理化特性 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '理化特性ID',
    文档编号 BIGINT NOT NULL COMMENT 'MSDS文档ID',
    外观 VARCHAR(256) COMMENT '外观',
    pH值 VARCHAR(64) COMMENT 'pH值',
    熔点 VARCHAR(64) COMMENT '熔点',
    沸点 VARCHAR(64) COMMENT '沸点/初沸点',
    闪点 VARCHAR(64) COMMENT '闪点',
    易燃性 VARCHAR(64) COMMENT '易燃性',
    爆炸极限 VARCHAR(64) COMMENT '爆炸极限',
    蒸气压 VARCHAR(64) COMMENT '蒸气压',
    相对密度 VARCHAR(64) COMMENT '相对密度',
    溶解性 VARCHAR(128) COMMENT '溶解性',
    自燃温度 VARCHAR(64) COMMENT '自燃温度',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX 索引_文档 (文档编号),
    CONSTRAINT 外键_理化_文档 FOREIGN KEY (文档编号) REFERENCES MSDS文档(编号) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='MSDS理化特性表';

-- ============================================================================
-- 6. E层：自然语言检索增强
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 6.1 自然语言分面表
-- ----------------------------------------------------------------------------
CREATE TABLE 自然语言分面 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '分面ID',
    分面键 ENUM('管理要求','使用要求','识别许可','应急措施') NOT NULL COMMENT '分面键',
    显示名称 VARCHAR(128) NOT NULL COMMENT '展示名称',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY 唯一键_分面 (分面键)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='自然语言分面表';

-- ----------------------------------------------------------------------------
-- 6.2 自然语言模板表
-- ----------------------------------------------------------------------------
CREATE TABLE 自然语言模板 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '模板ID',
    分面键 ENUM('管理要求','使用要求','识别许可','应急措施') NOT NULL COMMENT '分面键',
    模板文本 VARCHAR(512) NOT NULL COMMENT '模板文本',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX 索引_分面 (分面键)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='自然语言模板表';

-- ============================================================================
-- 7. 初始化基础数据
-- ============================================================================

-- 初始化自然语言分面数据
INSERT INTO 自然语言分面 (分面键, 显示名称) VALUES
    ('管理要求', '管理要求'),
    ('使用要求', '使用要求'),
    ('识别许可', '识别与许可'),
    ('应急措施', '应急措施');

-- 初始化自然语言模板数据
INSERT INTO 自然语言模板 (分面键, 模板文本) VALUES
    ('管理要求', '<NAME> 管理要求 法律 法规 条款'),
    ('使用要求', '<NAME> 使用 操作规程 防护 PPE'),
    ('识别许可', '<NAME> 识别 运输 许可 UN编号'),
    ('应急措施', '<NAME> 应急 急救 消防 泄漏');

-- ============================================================================
-- 8. 完成提示
-- ============================================================================

SELECT '数据库初始化完成！' AS 消息,
       '已创建18张数据表' AS 详情,
       'utf8mb4字符集，UTC时区' AS 配置,
       '包含A-E层完整结构' AS 结构,
       '所有表名和列名均为中文' AS 特点;

-- 查看所有表
SHOW TABLES;

