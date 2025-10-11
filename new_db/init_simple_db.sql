-- ============================================================================
-- 精简版危化品数据库 - 只保留化学品和MSDS信息
-- ============================================================================
-- 版本: 1.0 (精简版)
-- 创建时间: 2025-10-10
-- 数据库: MySQL 8.0+
-- 字符集: utf8mb4_0900_ai_ci
-- ============================================================================

-- ============================================================================
-- 1. 数据库创建与配置
-- ============================================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS 危化品简化数据库
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

-- 使用数据库
USE 危化品简化数据库;

-- 设置时区为UTC
SET time_zone = '+00:00';

-- ============================================================================
-- 2. 化学品主表
-- ============================================================================
CREATE TABLE 化学品 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '化学品ID',
    CAS号 VARCHAR(32) UNIQUE COMMENT 'CAS号，如 50-00-0',
    中文名 VARCHAR(256) NOT NULL COMMENT '中文名称',
    英文名 VARCHAR(256) COMMENT '英文名称',
    分子式 VARCHAR(64) COMMENT '分子式',
    EC编号 VARCHAR(64) COMMENT 'EC编号',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX 索引_CAS号 (CAS号),
    INDEX 索引_中文名 (中文名(191)),
    INDEX 索引_英文名 (英文名(191)),
    FULLTEXT INDEX 全文索引_名称 (中文名, 英文名) COMMENT '名称全文索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='化学品主表';

-- ============================================================================
-- 3. 化学品别名表
-- ============================================================================
CREATE TABLE 化学品别名 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '别名ID',
    化学品编号 BIGINT NOT NULL COMMENT '化学品ID',
    别名 VARCHAR(256) NOT NULL COMMENT '别名/同义词',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX 索引_化学品 (化学品编号),
    FULLTEXT INDEX 全文索引_别名 (别名) COMMENT '别名全文索引',
    CONSTRAINT 外键_别名_化学品 FOREIGN KEY (化学品编号) 
        REFERENCES 化学品(编号) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='化学品别名表';

-- ============================================================================
-- 4. MSDS文档表
-- ============================================================================
CREATE TABLE MSDS文档 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'MSDS文档ID',
    化学品编号 BIGINT NOT NULL UNIQUE COMMENT '化学品ID（一对一关系）',
    编制单位 VARCHAR(256) COMMENT '编制单位',
    编制依据 VARCHAR(256) COMMENT '编制依据标准',
    编制日期 DATE COMMENT '编制日期',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX 索引_化学品 (化学品编号),
    CONSTRAINT 外键_MSDS_化学品 FOREIGN KEY (化学品编号) 
        REFERENCES 化学品(编号) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='MSDS文档表';

-- ============================================================================
-- 5. MSDS章节表（16个部分）
-- ============================================================================
CREATE TABLE MSDS章节 (
    编号 BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'MSDS章节ID',
    文档编号 BIGINT NOT NULL COMMENT 'MSDS文档ID',
    章节序号 TINYINT NOT NULL COMMENT '章节号（1-16）',
    章节标题 VARCHAR(256) NOT NULL COMMENT '章节标题',
    内容 LONGTEXT COMMENT '章节内容（纯文本）',
    图片JSON JSON COMMENT '章节图片列表，格式：[{"url": "images/xxx.png", "alt": "GHS象形图", "type": "ghs"}]',
    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    更新时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY 唯一键_文档章节 (文档编号, 章节序号),
    INDEX 索引_章节序号 (章节序号),
    FULLTEXT INDEX 全文索引_内容 (章节标题, 内容) COMMENT '内容全文索引',
    CONSTRAINT 外键_章节_文档 FOREIGN KEY (文档编号) 
        REFERENCES MSDS文档(编号) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
COMMENT='MSDS章节表（16个部分）';

-- ============================================================================
-- 6. 查询存储过程
-- ============================================================================

-- 删除已存在的存储过程
DROP PROCEDURE IF EXISTS 查询化学品;

DELIMITER $$

-- 创建查询存储过程
CREATE PROCEDURE 查询化学品(
    IN p_关键词 VARCHAR(256)
)
BEGIN
    DECLARE v_化学品ID BIGINT;
    
    -- 查找化学品ID（支持中文名、英文名、CAS号、别名）
    SELECT 编号 INTO v_化学品ID 
    FROM 化学品 
    WHERE 中文名 LIKE CONCAT('%', p_关键词, '%')
       OR 英文名 LIKE CONCAT('%', p_关键词, '%')
       OR CAS号 = p_关键词
       OR 编号 IN (
           SELECT 化学品编号 
           FROM 化学品别名 
           WHERE 别名 LIKE CONCAT('%', p_关键词, '%')
       )
    LIMIT 1;
    
    IF v_化学品ID IS NULL THEN
        SELECT '未找到该化学品' AS 错误信息;
    ELSE
        -- 返回化学品基本信息
        SELECT 
            c.编号,
            c.CAS号,
            c.中文名,
            c.英文名,
            c.分子式,
            GROUP_CONCAT(a.别名 SEPARATOR '、') AS 所有别名
        FROM 化学品 c
        LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
        WHERE c.编号 = v_化学品ID
        GROUP BY c.编号, c.CAS号, c.中文名, c.英文名, c.分子式;
        
        -- 返回MSDS章节
        SELECT 
            m.章节序号,
            m.章节标题,
            m.内容,
            m.图片JSON,
            d.编制单位,
            d.编制依据,
            d.编制日期
        FROM MSDS文档 d
        JOIN MSDS章节 m ON d.编号 = m.文档编号
        WHERE d.化学品编号 = v_化学品ID
        ORDER BY m.章节序号;
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- 完成
-- ============================================================================

SELECT '精简版数据库创建完成！' AS 状态,
       '包含4个表：化学品、化学品别名、MSDS文档、MSDS章节' AS 说明,
       '使用方法：CALL 查询化学品("甲醛");' AS 查询示例;

