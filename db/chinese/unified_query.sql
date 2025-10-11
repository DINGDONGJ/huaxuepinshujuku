-- ================================================================
-- 危化品数据库 - 统一查询功能（中文版）
-- 实现：输入化学品名称，一次性返回四大类信息
-- 版本：2.0 - 修正为完全匹配中文数据库表名和列名
-- ================================================================

USE 危化品数据库;

-- ================================================================
-- 存储过程1：获取化学品的四类卡片信息
-- ================================================================

DROP PROCEDURE IF EXISTS 获取化学品完整信息;

DELIMITER $$

CREATE PROCEDURE 获取化学品完整信息(
    IN p_化学品名称 VARCHAR(256)
)
BEGIN
    DECLARE v_化学品ID BIGINT;
    
    -- 获取化学品ID（支持中文名、英文名、CAS号、别名）
    SELECT 编号 INTO v_化学品ID 
    FROM 化学品 
    WHERE 中文名 LIKE CONCAT('%', p_化学品名称, '%')
       OR 英文名 LIKE CONCAT('%', p_化学品名称, '%')
       OR CAS号 = p_化学品名称
       OR 编号 IN (
           SELECT 化学品编号 
           FROM 化学品别名 
           WHERE 名称 LIKE CONCAT('%', p_化学品名称, '%')
       )
    LIMIT 1;
    
    IF v_化学品ID IS NULL THEN
        SELECT '未找到该化学品' AS 错误信息;
    ELSE
        -- ============ 结果集1：基本信息 ============
        SELECT 
            '基本信息' AS 信息类别,
            CAS号,
            中文名,
            英文名,
            分子式,
            EC编号
        FROM 化学品
        WHERE 编号 = v_化学品ID;
        
        -- ============ 结果集2：管理要求（法律法规条款） ============
        SELECT 
            '管理要求' AS 信息类别,
            d.文档类型,
            d.标题 AS 法规名称,
            cl.条款编号,
            cl.标题 AS 条款标题,
            cl.内容 AS 条款内容,
            cl.链接 AS 条款链接,
            dv.文件地址 AS 文档文件,
            m.相关度评分,
            d.生效日期,
            d.状态
        FROM 化学品条款映射 m
        JOIN 法规条款 cl ON m.条款编号 = cl.编号
        JOIN 文档版本 dv ON cl.版本编号 = dv.编号
        JOIN 法规文档 d ON dv.文档编号 = d.编号
        WHERE m.化学品编号 = v_化学品ID
          AND cl.分类 = '管理要求'
        ORDER BY m.相关度评分 DESC, d.文档类型, d.生效日期 DESC;
        
        -- ============ 结果集3：使用要求（安全操作规程） ============
        SELECT 
            '使用要求' AS 信息类别,
            s.标题 AS 规程名称,
            s.适用范围,
            s.版本标签,
            s.正文 AS 规程内容,
            st.步骤序号,
            st.步骤内容
        FROM 操作规程库 s
        LEFT JOIN 操作规程步骤 st ON s.编号 = st.规程编号
        WHERE s.化学品编号 = v_化学品ID
        ORDER BY s.标题, st.步骤序号;
        
        -- ============ 结果集4：识别与许可 - GHS分类 ============
        SELECT 
            '识别与许可-GHS分类' AS 信息类别,
            g.危害类别,
            g.类别编号,
            g.信号词,
            g.象形图,
            g.H代码,
            g.P代码,
            g.数据来源
        FROM GHS分类 g
        WHERE g.化学品编号 = v_化学品ID;
        
        -- ============ 结果集5：识别与许可 - 运输分类 ============
        SELECT 
            '识别与许可-运输分类' AS 信息类别,
            t.UN编号,
            t.UN运输名称 AS UN正式名称,
            t.主要危险类别 AS 危险类别,
            t.次要危险类别,
            t.包装类别,
            CASE WHEN t.是否海洋污染物 = 1 THEN '是' ELSE '否' END AS 是否海洋污染物,
            t.运输注意事项
        FROM 运输分类 t
        WHERE t.化学品编号 = v_化学品ID;
        
        -- ============ 结果集6：识别与许可 - 目录标识 ============
        SELECT 
            '识别与许可-目录标识' AS 信息类别,
            hf.目录名称,
            CASE WHEN hf.是否列入 = 1 THEN '已列入' ELSE '未列入' END AS 列入状态,
            hf.参考文号
        FROM 危险品目录标识 hf
        WHERE hf.化学品编号 = v_化学品ID;
        
        -- ============ 结果集7：应急措施 ============
        SELECT 
            '应急措施' AS 信息类别,
            ec.类型 AS 应急类型,
            ec.内容 AS 应急措施内容,
            ec.版本标签
        FROM 应急卡片 ec
        WHERE ec.化学品编号 = v_化学品ID
        ORDER BY ec.类型;
        
        -- ============ 结果集8：别名列表 ============
        SELECT 
            '别名信息' AS 信息类别,
            GROUP_CONCAT(名称 SEPARATOR '、') AS 所有别名
        FROM 化学品别名
        WHERE 化学品编号 = v_化学品ID;
        
        -- ============ 结果集9：MSDS章节（16个部分） ============
        SELECT 
            'MSDS章节' AS 信息类别,
            c.章节序号,
            c.章节标题,
            c.内容,
            c.结构化数据,
            m.编制单位,
            m.编制人,
            m.编制日期,
            m.编制依据
        FROM MSDS文档 m
        JOIN MSDS章节 c ON m.编号 = c.文档编号
        WHERE m.化学品编号 = v_化学品ID
        ORDER BY c.章节序号;
        
    END IF;
END$$

DELIMITER ;

-- ================================================================
-- 存储过程2：获取引导词（四大类别）
-- ================================================================

DROP PROCEDURE IF EXISTS 获取引导词;

DELIMITER $$

CREATE PROCEDURE 获取引导词(
    IN p_化学品名称 VARCHAR(256)
)
BEGIN
    DECLARE v_化学品ID BIGINT;
    
    -- 获取化学品ID（支持中文名、英文名、CAS号、别名）
    SELECT 编号 INTO v_化学品ID 
    FROM 化学品 
    WHERE 中文名 LIKE CONCAT('%', p_化学品名称, '%')
       OR 英文名 LIKE CONCAT('%', p_化学品名称, '%')
       OR CAS号 = p_化学品名称
       OR 编号 IN (
           SELECT 化学品编号 
           FROM 化学品别名 
           WHERE 名称 LIKE CONCAT('%', p_化学品名称, '%')
       )
    LIMIT 1;
    
    IF v_化学品ID IS NULL THEN
        SELECT '未找到该化学品' AS 错误信息;
    ELSE
        -- 返回四大类别及每类的数据条数
        SELECT 
            '管理要求' AS 类别,
            '查看法律法规要求' AS 描述,
            COUNT(DISTINCT m.编号) AS 数据条数,
            'MANAGEMENT' AS 类别键
        FROM 化学品条款映射 m
        JOIN 法规条款 cl ON m.条款编号 = cl.编号
        WHERE m.化学品编号 = v_化学品ID AND cl.分类 = '管理要求'
        
        UNION ALL
        
        SELECT 
            '使用要求' AS 类别,
            '查看安全操作规程' AS 描述,
            COUNT(*) AS 数据条数,
            'USE_SOP' AS 类别键
        FROM 操作规程库
        WHERE 化学品编号 = v_化学品ID
        
        UNION ALL
        
        SELECT 
            '识别与许可' AS 类别,
            '查看GHS分类、运输许可' AS 描述,
            (SELECT COUNT(*) FROM GHS分类 WHERE 化学品编号 = v_化学品ID) +
            (SELECT COUNT(*) FROM 运输分类 WHERE 化学品编号 = v_化学品ID) +
            (SELECT COUNT(*) FROM 危险品目录标识 WHERE 化学品编号 = v_化学品ID) AS 数据条数,
            'IDENTIFICATION_PERMIT' AS 类别键
        
        UNION ALL
        
        SELECT 
            '应急措施' AS 类别,
            '查看应急预案和处置措施' AS 描述,
            COUNT(*) AS 数据条数,
            'EMERGENCY' AS 类别键
        FROM 应急卡片
        WHERE 化学品编号 = v_化学品ID;
    END IF;
END$$

DELIMITER ;

-- ================================================================
-- 存储过程3：按类别查询（单独获取某一类信息）
-- ================================================================

DROP PROCEDURE IF EXISTS 按类别查询;

DELIMITER $$

CREATE PROCEDURE 按类别查询(
    IN p_化学品名称 VARCHAR(256),
    IN p_类别键 VARCHAR(50)  -- MANAGEMENT, USE_SOP, IDENTIFICATION_PERMIT, EMERGENCY
)
BEGIN
    DECLARE v_化学品ID BIGINT;
    
    -- 获取化学品ID（支持中文名、英文名、CAS号、别名）
    SELECT 编号 INTO v_化学品ID 
    FROM 化学品 
    WHERE 中文名 LIKE CONCAT('%', p_化学品名称, '%')
       OR 英文名 LIKE CONCAT('%', p_化学品名称, '%')
       OR CAS号 = p_化学品名称
       OR 编号 IN (
           SELECT 化学品编号 
           FROM 化学品别名 
           WHERE 名称 LIKE CONCAT('%', p_化学品名称, '%')
       )
    LIMIT 1;
    
    IF v_化学品ID IS NULL THEN
        SELECT '未找到该化学品' AS 错误信息;
    ELSE
        -- 根据类别返回对应信息
        CASE p_类别键
            WHEN 'MANAGEMENT' THEN
                -- 管理要求
                SELECT 
                    d.文档类型,
                    d.标题 AS 法规名称,
                    cl.条款编号,
                    cl.标题 AS 条款标题,
                    cl.内容 AS 条款内容,
                    cl.链接 AS 条款链接,
                    dv.文件地址 AS 文档文件,
                    m.相关度评分
                FROM 化学品条款映射 m
                JOIN 法规条款 cl ON m.条款编号 = cl.编号
                JOIN 文档版本 dv ON cl.版本编号 = dv.编号
                JOIN 法规文档 d ON dv.文档编号 = d.编号
                WHERE m.化学品编号 = v_化学品ID
                  AND cl.分类 = '管理要求'
                ORDER BY m.相关度评分 DESC;
                
            WHEN 'USE_SOP' THEN
                -- 使用要求
                SELECT 
                    s.标题 AS 规程名称,
                    s.适用范围,
                    s.正文 AS 规程内容,
                    st.步骤序号,
                    st.步骤内容
                FROM 操作规程库 s
                LEFT JOIN 操作规程步骤 st ON s.编号 = st.规程编号
                WHERE s.化学品编号 = v_化学品ID
                ORDER BY s.标题, st.步骤序号;
                
            WHEN 'IDENTIFICATION_PERMIT' THEN
                -- 识别与许可（合并显示GHS、运输、目录）
                SELECT 
                    '运输分类' AS 类型,
                    CONCAT('UN', UN编号, ' - ', UN运输名称) AS 信息,
                    CONCAT('危险类别: ', 主要危险类别, ', 包装类别: ', 包装类别) AS 详情
                FROM 运输分类
                WHERE 化学品编号 = v_化学品ID
                
                UNION ALL
                
                SELECT 
                    'GHS分类' AS 类型,
                    危害类别 AS 信息,
                    CONCAT('信号词: ', 信号词, ', 类别: ', 类别编号) AS 详情
                FROM GHS分类
                WHERE 化学品编号 = v_化学品ID
                
                UNION ALL
                
                SELECT 
                    '目录标识' AS 类型,
                    目录名称 AS 信息,
                    CASE WHEN 是否列入 = 1 THEN '已列入' ELSE '未列入' END AS 详情
                FROM 危险品目录标识
                WHERE 化学品编号 = v_化学品ID;
                
            WHEN 'EMERGENCY' THEN
                -- 应急措施
                SELECT 
                    类型 AS 应急类型,
                    内容 AS 应急措施内容,
                    版本标签
                FROM 应急卡片
                WHERE 化学品编号 = v_化学品ID
                ORDER BY 类型;
                
            ELSE
                SELECT '无效的类别键，请使用：MANAGEMENT, USE_SOP, IDENTIFICATION_PERMIT, EMERGENCY' AS 错误信息;
        END CASE;
    END IF;
END$$

DELIMITER ;

-- ================================================================
-- 使用示例
-- ================================================================

-- 示例1：获取甲醛的完整信息（8个结果集）
-- CALL 获取化学品完整信息('甲醛');

-- 示例2：获取甲醛的引导词（显示四个类别按钮）
-- CALL 获取引导词('甲醛');

-- 示例3：只查询管理要求
-- CALL 按类别查询('甲醛', 'MANAGEMENT');

-- 示例4：只查询应急措施
-- CALL 按类别查询('甲醛', 'EMERGENCY');

-- 示例5：通过CAS号查询
-- CALL 获取化学品完整信息('50-00-0');

-- 示例6：查询使用要求
-- CALL 按类别查询('乙醇', 'USE_SOP');

-- 示例7：查询识别与许可
-- CALL 按类别查询('甲醛', 'IDENTIFICATION_PERMIT');

-- ================================================================
-- 验证安装
-- ================================================================

-- 查看已创建的存储过程
-- SHOW PROCEDURE STATUS WHERE Db = '危化品数据库';

-- 查看存储过程详情
-- SHOW CREATE PROCEDURE 获取化学品完整信息;
-- SHOW CREATE PROCEDURE 获取引导词;
-- SHOW CREATE PROCEDURE 按类别查询;
