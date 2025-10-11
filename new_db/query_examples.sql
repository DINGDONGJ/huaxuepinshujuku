-- ============================================================================
-- 精简版危化品数据库 - 查询示例
-- ============================================================================
-- 说明：本文件包含常用查询示例
-- ============================================================================

USE 危化品简化数据库;

-- ============================================================================
-- 1. 基础查询
-- ============================================================================

-- 查询所有化学品
SELECT * FROM 化学品;

-- 查询所有别名
SELECT 
    c.中文名,
    c.CAS号,
    GROUP_CONCAT(a.别名 SEPARATOR '、') AS 所有别名
FROM 化学品 c
LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
GROUP BY c.编号, c.中文名, c.CAS号;

-- 查询所有MSDS文档
SELECT 
    c.中文名,
    c.CAS号,
    m.编制单位,
    m.编制依据,
    COUNT(s.编号) AS 章节数
FROM 化学品 c
JOIN MSDS文档 m ON c.编号 = m.化学品编号
LEFT JOIN MSDS章节 s ON m.编号 = s.文档编号
GROUP BY c.编号, c.中文名, c.CAS号, m.编号, m.编制单位, m.编制依据;

-- ============================================================================
-- 2. 使用存储过程查询
-- ============================================================================

-- 通过中文名查询
CALL 查询化学品('甲醛');

-- 通过英文名查询
CALL 查询化学品('formaldehyde');

-- 通过CAS号查询
CALL 查询化学品('50-00-0');

-- 通过别名查询
CALL 查询化学品('福尔马林');

-- ============================================================================
-- 3. MSDS章节查询
-- ============================================================================

-- 查询某化学品的所有MSDS章节标题
SELECT 
    c.中文名,
    s.章节序号,
    s.章节标题
FROM 化学品 c
JOIN MSDS文档 m ON c.编号 = m.化学品编号
JOIN MSDS章节 s ON m.编号 = s.文档编号
WHERE c.CAS号 = '50-00-0'
ORDER BY s.章节序号;

-- 查询某化学品的特定章节内容
SELECT 
    c.中文名,
    s.章节标题,
    s.内容
FROM 化学品 c
JOIN MSDS文档 m ON c.编号 = m.化学品编号
JOIN MSDS章节 s ON m.编号 = s.文档编号
WHERE c.CAS号 = '50-00-0'
  AND s.章节序号 = 4  -- 第4部分：急救措施
ORDER BY s.章节序号;

-- 查询多个章节
SELECT 
    c.中文名,
    s.章节序号,
    s.章节标题,
    s.内容
FROM 化学品 c
JOIN MSDS文档 m ON c.编号 = m.化学品编号
JOIN MSDS章节 s ON m.编号 = s.文档编号
WHERE c.CAS号 = '50-00-0'
  AND s.章节序号 IN (4, 5, 6)  -- 急救措施、消防措施、泄漏应急处理
ORDER BY s.章节序号;

-- ============================================================================
-- 4. 全文搜索
-- ============================================================================

-- 在化学品名称中搜索
SELECT * FROM 化学品
WHERE MATCH(中文名, 英文名) AGAINST('甲醛' IN NATURAL LANGUAGE MODE);

-- 在别名中搜索
SELECT 
    c.中文名,
    c.CAS号,
    a.别名
FROM 化学品 c
JOIN 化学品别名 a ON c.编号 = a.化学品编号
WHERE MATCH(a.别名) AGAINST('福尔马林' IN NATURAL LANGUAGE MODE);

-- 在MSDS章节内容中搜索
SELECT 
    c.中文名,
    c.CAS号,
    s.章节序号,
    s.章节标题,
    SUBSTRING(s.内容, 1, 200) AS 内容摘要
FROM 化学品 c
JOIN MSDS文档 m ON c.编号 = m.化学品编号
JOIN MSDS章节 s ON m.编号 = s.文档编号
WHERE MATCH(s.章节标题, s.内容) AGAINST('急救' IN NATURAL LANGUAGE MODE)
ORDER BY c.中文名, s.章节序号;

-- ============================================================================
-- 5. 统计查询
-- ============================================================================

-- 统计化学品数量
SELECT 
    COUNT(*) AS 化学品总数
FROM 化学品;

-- 统计别名数量
SELECT 
    COUNT(*) AS 别名总数
FROM 化学品别名;

-- 统计MSDS文档数量
SELECT 
    COUNT(*) AS MSDS文档数
FROM MSDS文档;

-- 统计MSDS章节数量
SELECT 
    COUNT(*) AS MSDS章节总数,
    COUNT(*) / 16 AS 完整MSDS数量
FROM MSDS章节;

-- 查看每个化学品的章节完整性
SELECT 
    c.中文名,
    c.CAS号,
    COUNT(s.编号) AS 已有章节数,
    CASE 
        WHEN COUNT(s.编号) = 16 THEN '完整'
        WHEN COUNT(s.编号) > 0 THEN '不完整'
        ELSE '无MSDS'
    END AS 状态
FROM 化学品 c
LEFT JOIN MSDS文档 m ON c.编号 = m.化学品编号
LEFT JOIN MSDS章节 s ON m.编号 = s.文档编号
GROUP BY c.编号, c.中文名, c.CAS号
ORDER BY c.中文名;

-- ============================================================================
-- 6. 批量操作示例
-- ============================================================================

-- 查询缺失的MSDS章节
SELECT 
    c.中文名,
    c.CAS号,
    missing.章节序号 AS 缺失章节
FROM 化学品 c
JOIN MSDS文档 m ON c.编号 = m.化学品编号
CROSS JOIN (
    SELECT 1 AS 章节序号 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
    UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8
    UNION SELECT 9 UNION SELECT 10 UNION SELECT 11 UNION SELECT 12
    UNION SELECT 13 UNION SELECT 14 UNION SELECT 15 UNION SELECT 16
) missing
LEFT JOIN MSDS章节 s ON m.编号 = s.文档编号 AND missing.章节序号 = s.章节序号
WHERE s.编号 IS NULL
ORDER BY c.中文名, missing.章节序号;

-- ============================================================================
-- 完成
-- ============================================================================

SELECT '查询示例执行完成！' AS 状态;

