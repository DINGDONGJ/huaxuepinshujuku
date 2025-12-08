"""
精简版危化品数据库 - Web应用
专业化查询界面
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import pymysql
import json
from decimal import Decimal
from datetime import datetime
import os
from regulation_content_indexer import RegulationContentIndexer
from ai_analyzer import analyze_compatibility_with_ai, extract_chapter_summary
from smart_chapter_locator import SmartChapterLocator

# 初始化智能章节定位器
chapter_locator = SmartChapterLocator()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PDF_FOLDER'] = 'pdf'

# 确保文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)

# 初始化法规内容索引器
regulation_indexer = RegulationContentIndexer()
print("📚 加载法规内容索引...")
if regulation_indexer.load_index():
    print(f"✅ 索引加载成功！共 {regulation_indexer.index['stats']['total_files']} 个法规文件")
else:
    print("⚠️  索引文件不存在，将跳过内容匹配功能")
    print("   提示：运行 python regulation_content_indexer.py 构建索引")

# 初始化语义搜索引擎（可选功能）
try:
    from semantic_search_engine import LocalSemanticSearchEngine
    print("🤖 正在加载语义搜索引擎...")
    semantic_engine = LocalSemanticSearchEngine()
    SEMANTIC_SEARCH_ENABLED = True
    stats = semantic_engine.get_stats()
    print(f"✅ 语义搜索引擎已加载 ({stats['total_chemicals']} 个化学品)")
except ImportError:
    SEMANTIC_SEARCH_ENABLED = False
    semantic_engine = None
    print("⚠️  语义搜索未启用（缺少依赖）")
    print("   安装: pip install sentence-transformers scikit-learn")
    print("   构建索引: python build_semantic_index.py")
except FileNotFoundError:
    SEMANTIC_SEARCH_ENABLED = False
    semantic_engine = None
    print("⚠️  语义搜索未启用（索引未构建）")
    print("   构建索引: python build_semantic_index.py")
except Exception as e:
    SEMANTIC_SEARCH_ENABLED = False
    semantic_engine = None
    print(f"⚠️  语义搜索加载失败: {e}")

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',  # 请填入您的MySQL密码
    'database': '危化品简化数据库',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def process_results(results):
    """处理查询结果，转换特殊类型"""
    if not results:
        return []
    
    processed = []
    for row in results:
        processed_row = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                processed_row[key] = float(value)
            elif value is None:
                processed_row[key] = None
            elif key == '图片JSON' and isinstance(value, str):
                # 解析JSON字符串
                try:
                    processed_row[key] = json.loads(value)
                except:
                    processed_row[key] = None
            else:
                processed_row[key] = value
        processed.append(processed_row)
    
    return processed

def extract_number_from_text(text, pattern=r'(\d+\.?\d*)'):
    """从文本中提取数值"""
    import re
    match = re.search(pattern, text)
    if match:
        try:
            return float(match.group(1))
        except:
            return None
    return None

def extract_transport_class(content):
    """从第14章提取UN运输分类"""
    import re
    # 匹配联合国危险货物编号（UN编号）和类别
    patterns = [
        r'UN\s*编号[：:]\s*(\d+)',
        r'联合国危险货物编号[：:]\s*(\d+)',
        r'联合国编号[：:]\s*(\d+)',
        r'UN\s+No\.\s*[：:]?\s*(\d+)'
    ]
    
    un_number = None
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            un_number = match.group(1)
            break
    
    # 提取运输危险类别
    class_patterns = [
        r'运输危险类别[：:]\s*(\d+\.?\d*)',
        r'危险性类别[：:]\s*(\d+\.?\d*)',
        r'类别[：:]\s*(\d+\.?\d*)',
        r'Class\s*[：:]?\s*(\d+\.?\d*)'
    ]
    
    transport_class = None
    for pattern in class_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            transport_class = match.group(1).split('.')[0]  # 取整数部分
            break
    
    # 检查是否为海洋污染物
    marine_pollutant = False
    if any(keyword in content for keyword in ['海洋污染物', '海洋污染', 'Marine pollutant', 'MARPOL']):
        marine_pollutant = True
    
    return transport_class, marine_pollutant

def extract_flash_point(content):
    """从第9章提取闪点"""
    import re
    patterns = [
        r'闪点[：:]\s*(-?\d+\.?\d*)\s*[℃°C]',
        r'闪点[：:]\s*(-?\d+\.?\d*)',
        r'Flash\s+point\s*[：:]?\s*(-?\d+\.?\d*)\s*[℃°C]'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
    return None

def extract_ld50(content):
    """从第11章提取LD50值（mg/kg）"""
    import re
    # 匹配格式：LD50 经口 - 大鼠 500 mg/kg
    patterns = [
        r'LD50\s*[经纬]*口[^>]*?(\d+\.?\d*)\s*mg/kg',
        r'急性经口毒性.*?LD50[^>]*?(\d+\.?\d*)\s*mg/kg',
        r'LD50.*?oral.*?(\d+\.?\d*)\s*mg/kg'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
    return None

def extract_aquatic_lc50(content):
    """从第12章提取对水生生物的LC50值（mg/L）"""
    import re
    patterns = [
        r'LC50.*?鱼.*?(\d+\.?\d*)\s*mg/L',
        r'对鱼类的急性毒性.*?LC50.*?(\d+\.?\d*)\s*mg/L',
        r'LC50.*?fish.*?(\d+\.?\d*)\s*mg/L'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
    return None

def extract_keywords_from_msds(chemical_name, cas_number, chapters):
    """从化学品信息和msds章节中提取关键词"""
    import re
    keywords = set()
    
    # 1. 添加化学品基本信息
    if chemical_name:
        keywords.add(chemical_name)
        # 提取化学品名称中的关键部分
        # 例如："甲醇" -> "甲", "醇"
        for char in chemical_name:
            if len(char) >= 2:
                keywords.add(char)
    
    if cas_number:
        keywords.add(cas_number)
    
    # 2. 从各章节提取关键词
    for chapter in chapters:
        content = chapter.get('内容', '')
        chapter_num = chapter.get('章节序号', 0)
        
        # 第2章：危险性概述 - 提取GHS分类
        if chapter_num == 2:
            ghs_keywords = [
                '易燃液体', '易燃气体', '易燃固体', '爆炸物', '氧化性液体', 
                '氧化性固体', '氧化性气体', '加压气体', '自反应物质', 
                '自燃液体', '自燃固体', '自热物质', '遇水放出易燃气体',
                '有机过氧化物', '金属腐蚀物', '急性毒性', '皮肤腐蚀',
                '严重眼损伤', '呼吸道致敏', '皮肤致敏', '生殖细胞致突变',
                '致癌', '生殖毒性', '特异性靶器官毒性', '吸入危害',
                '对水生环境的危害', '对臭氧层的危害', '腐蚀', '刺激'
            ]
            for kw in ghs_keywords:
                if kw in content:
                    keywords.add(kw)
            
            # 提取类别信息
            category_matches = re.findall(r'类别\s*[1-4A-E]', content)
            keywords.update(category_matches)
        
        # 第9章：理化特性 - 提取物态和特性
        elif chapter_num == 9:
            property_keywords = ['易燃', '可燃', '液体', '固体', '气体', '粉末']
            for kw in property_keywords:
                if kw in content:
                    keywords.add(kw)
        
        # 第11章：毒理学信息 - 提取毒性关键词
        elif chapter_num == 11:
            toxicity_keywords = ['剧毒', '高毒', '中等毒性', '低毒', '微毒', '急性毒性', '慢性毒性']
            for kw in toxicity_keywords:
                if kw in content:
                    keywords.add(kw)
        
        # 第14章：运输信息 - 提取运输分类
        elif chapter_num == 14:
            # 提取UN编号
            un_matches = re.findall(r'UN\s*(\d{4})', content)
            keywords.update(f'UN{un}' for un in un_matches)
            
            # 提取运输类别
            class_matches = re.findall(r'类别\s*[：:]\s*(\d)', content)
            keywords.update(f'运输类别{c}' for c in class_matches)
            
            if '海洋污染物' in content:
                keywords.add('海洋污染物')
        
        # 第15章：法规信息 - 提取已列入的法规
        elif chapter_num == 15:
            # 提取法规名称（书名号内容）
            regulation_matches = re.findall(r'《(.+?)》', content)
            keywords.update(regulation_matches)
    
    # 过滤太短或无效的关键词
    keywords = {kw for kw in keywords if len(kw) >= 2 and kw.strip()}
    
    return list(keywords)

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/msds_json/<path:filename>')
def serve_msds_files(filename):
    """提供msds JSON文件夹中的文件（包括图片）"""
    import os
    from flask import send_from_directory
    msds_dir = os.path.join(os.path.dirname(__file__), 'msds_json')
    return send_from_directory(msds_dir, filename)

@app.route('/api/search', methods=['POST'])
def search():
    """搜索化学品"""
    data = request.get_json()
    keyword = data.get('keyword', '')
    
    if not keyword:
        return jsonify({'error': '请输入搜索关键词'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 优先精确匹配
        cursor.execute("""
            SELECT 编号 FROM 化学品 
            WHERE 中文名 = %s
               OR 英文名 = %s
               OR CAS号 = %s
               OR 编号 IN (
                   SELECT 化学品编号 
                   FROM 化学品别名 
                   WHERE 别名 = %s
               )
            LIMIT 1
        """, (keyword, keyword, keyword, keyword))
        
        result = cursor.fetchone()
        search_type = 'exact'
        
        # 如果精确匹配没找到，再进行模糊匹配（优先匹配更长、更精确的名称）
        if not result:
            cursor.execute("""
                SELECT 编号, 中文名, 英文名,
                    CASE
                        WHEN 中文名 LIKE %s THEN LENGTH(中文名)
                        WHEN 英文名 LIKE %s THEN LENGTH(英文名)
                        ELSE 0
                    END AS match_length
                FROM 化学品 
                WHERE 中文名 LIKE %s
                   OR 英文名 LIKE %s
                   OR CAS号 = %s
                   OR 编号 IN (
                       SELECT 化学品编号 
                       FROM 化学品别名 
                       WHERE 别名 LIKE %s
                   )
                ORDER BY match_length DESC
                LIMIT 1
            """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', keyword, f'%{keyword}%'))
            
            result = cursor.fetchone()
            search_type = 'fuzzy'
        
        # 如果模糊匹配也没找到，尝试提取关键词再匹配
        if not result:
            # 提取可能的化学品名称（去除常见后缀和停用词）
            import re
            # 先去除常见的查询词（包含MSDS相关的所有常见问题）
            clean_keyword = re.sub(
                r'(的危险性?|的毒性|的用途|的性质|的特性|的信息|的资料|的数据|'
                r'的泄露|的泄漏|的处理|的储存|的运输|的防护|的急救|的应急|'
                r'是什么|有什么|会不会|能不能|怎么办|如何|吗|？|\?|'
                r'危险性?|毒性|用途|性质|特性|信息|资料|数据|'
                r'泄露|泄漏|处理|储存|运输|防护|急救|应急|爆炸|燃烧)', 
                '', keyword
            ).strip()
            # 再去除单独的"的"、"是"等
            clean_keyword = re.sub(r'^(的|是|有|会|能)+', '', clean_keyword).strip()
            clean_keyword = re.sub(r'(的|是|有|会|能)+$', '', clean_keyword).strip()
            
            if clean_keyword and clean_keyword != keyword and len(clean_keyword) >= 2:
                print(f"🔍 提取关键词: '{keyword}' -> '{clean_keyword}'")
                
                # 用提取的关键词再次尝试精确匹配
                cursor.execute("""
                    SELECT 编号 FROM 化学品 
                    WHERE 中文名 = %s
                       OR 英文名 = %s
                       OR CAS号 = %s
                       OR 编号 IN (
                           SELECT 化学品编号 
                           FROM 化学品别名 
                           WHERE 别名 = %s
                       )
                    LIMIT 1
                """, (clean_keyword, clean_keyword, clean_keyword, clean_keyword))
                
                result = cursor.fetchone()
                
                # 如果还是没找到，再模糊匹配
                if not result:
                    cursor.execute("""
                        SELECT 编号 FROM 化学品 
                        WHERE 中文名 LIKE %s
                           OR 英文名 LIKE %s
                           OR CAS号 = %s
                           OR 编号 IN (
                               SELECT 化学品编号 
                               FROM 化学品别名 
                               WHERE 别名 LIKE %s
                           )
                        LIMIT 1
                    """, (f'%{clean_keyword}%', f'%{clean_keyword}%', clean_keyword, f'%{clean_keyword}%'))
                    
                    result = cursor.fetchone()
                
                if result:
                    search_type = 'keyword_extraction'
        
        if not result and SEMANTIC_SEARCH_ENABLED:
            # 使用语义搜索（降低阈值，提高召回率）
            semantic_results = semantic_engine.search(keyword, top_k=3, threshold=0.3)
            
            if semantic_results:
                # 如果找到多个结果，显示最佳匹配
                best_match = semantic_results[0]
                chemical_id = best_match['chemical_id']
                search_type = 'semantic'
                
                if len(semantic_results) > 1:
                    print(f"🤖 语义搜索找到 {len(semantic_results)} 个候选:")
                    for i, r in enumerate(semantic_results, 1):
                        print(f"   {i}. {r['name']} (相似度: {r['score']:.3f})")
                    print(f"   选择最佳匹配: {best_match['name']}")
                else:
                    print(f"🤖 使用语义搜索找到: {best_match['name']} (相似度: {best_match['score']:.3f})")
            else:
                cursor.close()
                conn.close()
                return jsonify({
                    'error': '未找到该化学品',
                    'suggestion': '尝试使用化学品的中文名、英文名或CAS号搜索'
                }), 404
        elif not result:
            cursor.close()
            conn.close()
            return jsonify({'error': '未找到该化学品'}), 404
        else:
            chemical_id = result['编号']
        
        # 获取化学品基本信息和别名
        cursor.execute("""
            SELECT 
                c.编号,
                c.CAS号,
                c.中文名,
                c.英文名,
                c.分子式,
                GROUP_CONCAT(a.别名 SEPARATOR '、') AS 所有别名
            FROM 化学品 c
            LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
            WHERE c.编号 = %s
            GROUP BY c.编号, c.CAS号, c.中文名, c.英文名, c.分子式
        """, (chemical_id,))
        
        basic_info = cursor.fetchone()
        
        # 获取msds章节
        cursor.execute("""
            SELECT 
                s.章节序号,
                s.章节标题,
                s.内容,
                s.图片JSON,
                d.编制单位,
                d.编制依据,
                d.编制日期
            FROM msds文档 d
            JOIN msds章节 s ON d.编号 = s.文档编号
            WHERE d.化学品编号 = %s
            ORDER BY s.章节序号
        """, (chemical_id,))
        
        msds_chapters = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 分析查询意图，定位相关章节
        query_analysis = chapter_locator.analyze_query(keyword)
        
        return jsonify({
            'basic_info': basic_info,
            'msds_chapters': process_results(msds_chapters),
            'search_type': search_type,  # 告诉前端使用了哪种搜索方式
            'query_analysis': query_analysis  # 智能章节定位信息
        })
    
    except Exception as e:
        return jsonify({'error': f'查询失败: {str(e)}'}), 500

@app.route('/api/list', methods=['GET'])
def list_chemicals():
    """获取所有化学品列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.编号,
                c.CAS号,
                c.中文名,
                c.英文名,
                COUNT(DISTINCT s.编号) AS 章节数
            FROM 化学品 c
            LEFT JOIN msds文档 m ON c.编号 = m.化学品编号
            LEFT JOIN msds章节 s ON m.编号 = s.文档编号
            GROUP BY c.编号, c.CAS号, c.中文名, c.英文名
            ORDER BY c.中文名
        """)
        
        chemicals = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'chemicals': process_results(chemicals)})
    
    except Exception as e:
        return jsonify({'error': f'查询失败: {str(e)}'}), 500

@app.route('/api/import', methods=['POST'])
def import_json():
    """导入JSON格式的msds数据"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        if not file.filename.endswith('.json'):
            return jsonify({'error': '只支持JSON文件'}), 400
        
        # 读取JSON数据
        json_data = json.load(file)
        
        # 验证JSON结构
        if 'chemical_info' not in json_data or 'msds_chapters' not in json_data:
            return jsonify({'error': 'JSON格式不正确'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 开始事务
            conn.begin()
            
            chem_info = json_data['chemical_info']
            msds_meta = json_data.get('msds_meta', {})
            aliases = json_data.get('aliases', [])
            chapters = json_data['msds_chapters']
            
            # 1. 检查化学品是否已存在
            cas_number = chem_info.get('CAS号')
            cursor.execute("SELECT 编号 FROM 化学品 WHERE CAS号 = %s", (cas_number,))
            existing = cursor.fetchone()
            
            if existing:
                chemical_id = existing['编号']
                # 更新化学品信息
                cursor.execute("""
                    UPDATE 化学品 
                    SET 中文名 = %s, 英文名 = %s, 分子式 = %s, EC编号 = %s
                    WHERE 编号 = %s
                """, (
                    chem_info.get('中文名'),
                    chem_info.get('英文名'),
                    chem_info.get('分子式'),
                    chem_info.get('EC编号'),
                    chemical_id
                ))
            else:
                # 插入新化学品
                cursor.execute("""
                    INSERT INTO 化学品 (CAS号, 中文名, 英文名, 分子式, EC编号)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    cas_number,
                    chem_info.get('中文名'),
                    chem_info.get('英文名'),
                    chem_info.get('分子式'),
                    chem_info.get('EC编号')
                ))
                chemical_id = cursor.lastrowid
            
            # 2. 处理别名（先删除旧的）
            cursor.execute("DELETE FROM 化学品别名 WHERE 化学品编号 = %s", (chemical_id,))
            
            for alias in aliases:
                if alias and alias.strip():
                    cursor.execute("""
                        INSERT INTO 化学品别名 (化学品编号, 别名)
                        VALUES (%s, %s)
                    """, (chemical_id, alias.strip()))
            
            # 3. 处理msds文档
            cursor.execute("SELECT 编号 FROM msds文档 WHERE 化学品编号 = %s", (chemical_id,))
            msds_doc = cursor.fetchone()
            
            if msds_doc:
                msds_doc_id = msds_doc['编号']
                # 更新msds文档
                cursor.execute("""
                    UPDATE msds文档 
                    SET 编制单位 = %s, 编制日期 = %s, 编制依据 = %s
                    WHERE 编号 = %s
                """, (
                    msds_meta.get('编制单位'),
                    msds_meta.get('编制日期'),
                    msds_meta.get('编制依据'),
                    msds_doc_id
                ))
                
                # 删除旧的章节
                cursor.execute("DELETE FROM msds章节 WHERE 文档编号 = %s", (msds_doc_id,))
            else:
                # 插入新msds文档
                cursor.execute("""
                    INSERT INTO msds文档 (化学品编号, 编制单位, 编制日期, 编制依据)
                    VALUES (%s, %s, %s, %s)
                """, (
                    chemical_id,
                    msds_meta.get('编制单位'),
                    msds_meta.get('编制日期'),
                    msds_meta.get('编制依据')
                ))
                msds_doc_id = cursor.lastrowid
            
            # 4. 插入msds章节
            for chapter in chapters:
                # 处理图片数据
                images_json = None
                if '图片' in chapter and chapter['图片']:
                    images_json = json.dumps(chapter['图片'], ensure_ascii=False)
                
                cursor.execute("""
                    INSERT INTO msds章节 (文档编号, 章节序号, 章节标题, 内容, 图片JSON)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    msds_doc_id,
                    chapter['章节序号'],
                    chapter['章节标题'],
                    chapter['内容'],
                    images_json
                ))
            
            # 提交事务
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'成功导入化学品: {chem_info.get("中文名")}',
                'data': {
                    '化学品ID': chemical_id,
                    '化学品名称': chem_info.get('中文名'),
                    'CAS号': cas_number,
                    '章节数': len(chapters),
                    '别名数': len(aliases)
                }
            })
            
        except Exception as e:
            # 回滚事务
            conn.rollback()
            cursor.close()
            conn.close()
            raise e
            
    except Exception as e:
        return jsonify({'error': f'导入失败: {str(e)}'}), 500

@app.route('/api/delete', methods=['POST'])
def delete_chemical():
    """删除化学品及其所有相关数据"""
    try:
        data = request.get_json()
        chemical_id = data.get('chemical_id')
        
        if not chemical_id:
            return jsonify({'error': '缺少化学品ID'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 获取化学品信息（用于返回消息）
            cursor.execute("""
                SELECT 中文名, CAS号 
                FROM 化学品 
                WHERE 编号 = %s
            """, (chemical_id,))
            
            chemical = cursor.fetchone()
            
            if not chemical:
                cursor.close()
                conn.close()
                return jsonify({'error': '化学品不存在'}), 404
            
            chemical_name = chemical['中文名']
            cas_number = chemical['CAS号']
            
            # 删除化学品（外键级联会自动删除别名、msds文档和章节）
            cursor.execute("DELETE FROM 化学品 WHERE 编号 = %s", (chemical_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'成功删除化学品: {chemical_name}',
                'data': {
                    '化学品名称': chemical_name,
                    'CAS号': cas_number
                }
            })
            
        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            raise e
            
    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

@app.route('/api/autocomplete', methods=['GET'])
def autocomplete():
    """自动补全API - 根据关键词返回候选化学品列表"""
    keyword = request.args.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({'suggestions': []})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 搜索化学品（支持中文名、英文名、CAS号、别名模糊匹配）
        cursor.execute("""
            SELECT DISTINCT 
                c.编号,
                c.CAS号,
                c.中文名,
                c.英文名
            FROM 化学品 c
            LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
            WHERE c.中文名 LIKE %s
               OR c.英文名 LIKE %s
               OR c.CAS号 LIKE %s
               OR a.别名 LIKE %s
            ORDER BY 
                CASE 
                    WHEN c.中文名 = %s THEN 1
                    WHEN c.中文名 LIKE %s THEN 2
                    WHEN c.CAS号 = %s THEN 3
                    WHEN c.CAS号 LIKE %s THEN 4
                    ELSE 5
                END,
                c.中文名
            LIMIT 10
        """, (
            f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%',
            keyword, f'{keyword}%', keyword, f'{keyword}%'
        ))
        
        suggestions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'suggestions': process_results(suggestions)})
    
    except Exception as e:
        return jsonify({'error': f'查询失败: {str(e)}'}), 500

@app.route('/api/semantic-search', methods=['POST'])
def semantic_search():
    """语义搜索API - 支持自然语言查询"""
    if not SEMANTIC_SEARCH_ENABLED:
        return jsonify({
            'error': '语义搜索未启用',
            'message': '请先安装依赖并构建索引',
            'instructions': {
                'install': 'pip install sentence-transformers scikit-learn',
                'build': 'python build_semantic_index.py'
            }
        }), 503
    
    data = request.get_json()
    query = data.get('query', '')
    top_k = data.get('top_k', 10)
    threshold = data.get('threshold', 0.3)
    
    if not query:
        return jsonify({'error': '请输入搜索查询'}), 400
    
    try:
        # 执行语义搜索
        results = semantic_engine.search(query, top_k=top_k, threshold=threshold)
        
        # 如果找到结果，获取完整的化学品信息
        if results:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            detailed_results = []
            for result in results:
                chemical_id = result['chemical_id']
                
                # 获取完整信息
                cursor.execute("""
                    SELECT 
                        c.编号,
                        c.CAS号,
                        c.中文名,
                        c.英文名,
                        c.分子式,
                        GROUP_CONCAT(a.别名 SEPARATOR '、') AS 所有别名
                    FROM 化学品 c
                    LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
                    WHERE c.编号 = %s
                    GROUP BY c.编号, c.CAS号, c.中文名, c.英文名, c.分子式
                """, (chemical_id,))
                
                chem_info = cursor.fetchone()
                if chem_info:
                    chem_info['semantic_score'] = result['score']
                    detailed_results.append(chem_info)
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'query': query,
                'total': len(detailed_results),
                'results': detailed_results,
                'search_type': 'semantic'
            })
        else:
            return jsonify({
                'success': True,
                'query': query,
                'total': 0,
                'results': [],
                'message': '未找到相关化学品'
            })
    
    except Exception as e:
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500

@app.route('/api/semantic-status', methods=['GET'])
def semantic_status():
    """检查语义搜索状态"""
    if SEMANTIC_SEARCH_ENABLED:
        stats = semantic_engine.get_stats()
        return jsonify({
            'enabled': True,
            'stats': stats
        })
    else:
        return jsonify({
            'enabled': False,
            'message': '语义搜索未启用',
            'instructions': {
                'install': 'pip install sentence-transformers scikit-learn',
                'build_index': 'python build_semantic_index.py'
            }
        })

@app.route('/api/regulations/<int:chemical_id>', methods=['GET'])
def get_regulations(chemical_id):
    """获取化学品相关法规"""
    try:
        # 1. 查询化学品信息和msds数据
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取化学品基本信息
        cursor.execute("""
            SELECT c.编号, c.CAS号, c.中文名, c.英文名
            FROM 化学品 c
            WHERE c.编号 = %s
        """, (chemical_id,))
        chemical = cursor.fetchone()
        
        if not chemical:
            cursor.close()
            conn.close()
            return jsonify({'error': '化学品不存在'}), 404
        
        # 获取msds章节数据（第2,9,11,14,15章）
        cursor.execute("""
            SELECT s.章节序号, s.章节标题, s.内容
            FROM msds文档 d
            JOIN msds章节 s ON d.编号 = s.文档编号
            WHERE d.化学品编号 = %s AND s.章节序号 IN (2, 9, 11, 14, 15)
            ORDER BY s.章节序号
        """, (chemical_id,))
        chapters = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 2. 加载法规映射配置
        mapping_file = os.path.join(os.path.dirname(__file__), 'regulation_mapping.json')
        with open(mapping_file, 'r', encoding='utf-8') as f:
            regulation_mapping = json.load(f)
        
        # 3. 智能匹配法规
        matched_regulations = []
        
        # 3.1 从第15章提取法规列入状态
        chapter15 = next((ch for ch in chapters if ch['章节序号'] == 15), None)
        if chapter15:
            content = chapter15['内容']
            
            # 解析法规列入状态
            for regulation_name, regulation_info in regulation_mapping['regulation_catalog_mapping'].items():
                # 去掉书名号，用于匹配
                clean_name = regulation_name.strip('《》')
                
                # 检查是否列入该法规
                if clean_name in content:
                    # 查找"列入"状态
                    lines = content.split('\n')
                    is_listed = False
                    for i, line in enumerate(lines):
                        if clean_name in line:
                            # 在后面几行内查找"列入"
                            for j in range(i, min(i+5, len(lines))):
                                if '列入' in lines[j]:
                                    is_listed = True
                                    break
                            break
                    
                    if is_listed:
                        for file_path in regulation_info['files']:
                            matched_regulations.append({
                                'file': file_path,
                                'name': os.path.basename(file_path).replace('.pdf', ''),
                                'reason': f'msds数据显示可能涉及{regulation_name}',
                                'priority': regulation_info['priority'],
                                'category': regulation_info['category']
                            })
        
        # 3.2 从第2章提取GHS危险性类别
        chapter2 = next((ch for ch in chapters if ch['章节序号'] == 2), None)
        if chapter2:
            content = chapter2['内容']
            
            # 匹配GHS分类
            for ghs_name, ghs_info in regulation_mapping['ghs_category_mapping'].items():
                # 检查关键词
                keywords = ghs_info.get('keywords', [ghs_name])
                for keyword in keywords:
                    if keyword in content:
                        for file_path in ghs_info['files']:
                            # 避免重复添加
                            if not any(r['file'] == file_path for r in matched_regulations):
                                matched_regulations.append({
                                    'file': file_path,
                                    'name': os.path.basename(file_path).replace('.pdf', ''),
                                    'reason': f'危险特性匹配度：{ghs_name}',
                                    'priority': ghs_info['priority'],
                                    'category': ghs_info['category']
                                })
                        break  # 找到一个关键词即可
        
        # 3.3 从第14章提取运输分类信息
        chapter14 = next((ch for ch in chapters if ch['章节序号'] == 14), None)
        if chapter14:
            content = chapter14['内容']
            transport_class, marine_pollutant = extract_transport_class(content)
            
            # 匹配运输分类法规
            if transport_class and 'transport_class_mapping' in regulation_mapping:
                if transport_class in regulation_mapping['transport_class_mapping']:
                    class_info = regulation_mapping['transport_class_mapping'][transport_class]
                    for file_path in class_info['files']:
                        if not any(r['file'] == file_path for r in matched_regulations):
                            matched_regulations.append({
                                'file': file_path,
                                'name': os.path.basename(file_path).replace('.pdf', ''),
                                'reason': f'运输分类匹配：{class_info["name"]}（第{transport_class}类）',
                                'priority': class_info['priority'],
                                'category': class_info['category']
                            })
            
            # 匹配海洋污染物
            if marine_pollutant and 'marine_pollutant_mapping' in regulation_mapping:
                marine_info = regulation_mapping['marine_pollutant_mapping']['是']
                for file_path in marine_info['files']:
                    if not any(r['file'] == file_path for r in matched_regulations):
                        matched_regulations.append({
                            'file': file_path,
                            'name': os.path.basename(file_path).replace('.pdf', ''),
                            'reason': 'msds数据显示该物质可能为海洋污染物',
                            'priority': marine_info['priority'],
                            'category': marine_info['category']
                        })
        
        # 3.4 从第9章提取理化特性
        chapter9 = next((ch for ch in chapters if ch['章节序号'] == 9), None)
        if chapter9:
            content = chapter9['内容']
            flash_point = extract_flash_point(content)
            
            # 匹配闪点范围
            if flash_point is not None and 'flash_point_mapping' in regulation_mapping:
                for range_key, range_info in regulation_mapping['flash_point_mapping'].items():
                    min_val = range_info.get('min', float('-inf'))
                    max_val = range_info.get('max', float('inf'))
                    
                    if min_val <= flash_point < max_val:
                        for file_path in range_info['files']:
                            if not any(r['file'] == file_path for r in matched_regulations):
                                matched_regulations.append({
                                    'file': file_path,
                                    'name': os.path.basename(file_path).replace('.pdf', ''),
                                    'reason': f'闪点特性：{range_info["name"]}（{flash_point}℃）',
                                    'priority': range_info['priority'],
                                    'category': range_info['category']
                                })
                        break  # 只匹配一个范围
            
            # 检查易燃性描述
            if 'flammability_mapping' in regulation_mapping:
                if '易燃' in content:
                    # 判断是液体还是固体
                    if any(keyword in content for keyword in ['液体', '液态']):
                        if '易燃' in regulation_mapping['flammability_mapping']:
                            flam_info = regulation_mapping['flammability_mapping']['易燃']
                            for file_path in flam_info['files']:
                                if not any(r['file'] == file_path for r in matched_regulations):
                                    matched_regulations.append({
                                        'file': file_path,
                                        'name': os.path.basename(file_path).replace('.pdf', ''),
                                        'reason': '理化特性显示该物质可能为易燃物',
                                        'priority': flam_info['priority'],
                                        'category': flam_info['category']
                                    })
                    elif any(keyword in content for keyword in ['固体', '固态', '粉末']):
                        if '固体_易燃' in regulation_mapping['flammability_mapping']:
                            flam_info = regulation_mapping['flammability_mapping']['固体_易燃']
                            for file_path in flam_info['files']:
                                if not any(r['file'] == file_path for r in matched_regulations):
                                    matched_regulations.append({
                                        'file': file_path,
                                        'name': os.path.basename(file_path).replace('.pdf', ''),
                                        'reason': '理化特性显示该物质可能为易燃固体',
                                        'priority': flam_info['priority'],
                                        'category': flam_info['category']
                                    })
        
        # 3.5 从第11章提取毒理学信息
        chapter11 = next((ch for ch in chapters if ch['章节序号'] == 11), None)
        if chapter11:
            content = chapter11['内容']
            ld50 = extract_ld50(content)
            
            # 匹配LD50范围
            if ld50 is not None and 'toxicity_mapping' in regulation_mapping:
                if 'ld50_ranges' in regulation_mapping['toxicity_mapping']:
                    for range_info in regulation_mapping['toxicity_mapping']['ld50_ranges']:
                        min_val = range_info.get('min', float('-inf'))
                        max_val = range_info.get('max', float('inf'))
                        
                        if min_val <= ld50 < max_val:
                            for file_path in range_info['files']:
                                if not any(r['file'] == file_path for r in matched_regulations):
                                    matched_regulations.append({
                                        'file': file_path,
                                        'name': os.path.basename(file_path).replace('.pdf', ''),
                                        'reason': f'毒性指标：{range_info["name"]}（LD50={ld50} mg/kg）',
                                        'priority': range_info['priority'],
                                        'category': range_info['category']
                                    })
                            break  # 只匹配一个范围
            
            # 提取水生生物毒性
            aquatic_lc50 = extract_aquatic_lc50(content)
            if aquatic_lc50 is not None and 'aquatic_toxicity_mapping' in regulation_mapping:
                if 'lc50_ranges' in regulation_mapping['aquatic_toxicity_mapping']:
                    for range_info in regulation_mapping['aquatic_toxicity_mapping']['lc50_ranges']:
                        min_val = range_info.get('min', float('-inf'))
                        max_val = range_info.get('max', float('inf'))
                        
                        if min_val <= aquatic_lc50 < max_val:
                            for file_path in range_info['files']:
                                if not any(r['file'] == file_path for r in matched_regulations):
                                    matched_regulations.append({
                                        'file': file_path,
                                        'name': os.path.basename(file_path).replace('.pdf', ''),
                                        'reason': f'水生毒性：{range_info["name"]}（LC50={aquatic_lc50} mg/L）',
                                        'priority': range_info['priority'],
                                        'category': range_info['category']
                                    })
                            break
        
        # 3.6 添加通用法规
        common_info = regulation_mapping['common_regulations']
        for file_path in common_info['files']:
            if not any(r['file'] == file_path for r in matched_regulations):
                matched_regulations.append({
                    'file': file_path,
                    'name': os.path.basename(file_path).replace('.pdf', ''),
                    'reason': '基础法规参考',
                    'priority': common_info['priority'],
                    'category': common_info['category']
                })
        
        # 3.7 内容智能匹配（基于法规文本内容）
        if regulation_indexer.index:  # 确保索引已加载
            try:
                # 提取msds关键词
                keywords = extract_keywords_from_msds(
                    chemical.get('中文名', ''),
                    chemical.get('CAS号', ''),
                    chapters
                )
                
                # 使用索引搜索相关法规
                content_matches = regulation_indexer.search_by_keywords(keywords, max_results=10)
                
                # 添加内容匹配的法规（优先级4）
                for match in content_matches:
                    file_path = match['file']
                    # 避免重复添加已匹配的法规
                    if not any(r['file'] == file_path for r in matched_regulations):
                        matched_regulations.append({
                            'file': file_path,
                            'name': match['title'] or os.path.basename(file_path).replace('.pdf', ''),
                            'reason': match['reason'],
                            'priority': 4,  # 内容匹配优先级为4（低于配置匹配）
                            'category': match.get('category', '内容推荐'),
                            'score': match.get('score', 0)  # 保留匹配分数
                        })
            except Exception as e:
                print(f"⚠️  内容匹配失败: {e}")
                # 内容匹配失败不影响其他匹配，继续执行
        
        # 4. 按优先级排序
        matched_regulations.sort(key=lambda x: x['priority'])
        
        # 5. 按分类分组
        regulations_by_category = {}
        for reg in matched_regulations:
            category = reg['category']
            if category not in regulations_by_category:
                regulations_by_category[category] = []
            regulations_by_category[category].append(reg)
        
        return jsonify({
            'chemical': process_results([chemical])[0] if chemical else None,
            'total': len(matched_regulations),
            'regulations': matched_regulations,
            'by_category': regulations_by_category
        })
    
    except Exception as e:
        return jsonify({'error': f'获取法规失败: {str(e)}'}), 500

@app.route('/regulation-pdf/<path:filepath>')
def serve_regulation_pdf(filepath):
    """提供法规PDF文件访问"""
    try:
        # 法规PDF文件在化学品法规pdf文件夹中
        regulation_folder = os.path.join(os.path.dirname(__file__), '化学品法规pdf')
        return send_from_directory(regulation_folder, filepath)
    except FileNotFoundError:
        return jsonify({'error': 'PDF文件未找到'}), 404

@app.route('/pdf/<path:filename>')
def serve_pdf(filename):
    """提供PDF文件访问"""
    try:
        return send_from_directory(app.config['PDF_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({'error': 'PDF文件未找到'}), 404

@app.route('/api/search-multiple', methods=['POST'])
def search_multiple():
    """多化学品查询接口（通过化学品ID）"""
    data = request.get_json()
    chemical_ids = data.get('chemical_ids', [])
    
    if not chemical_ids:
        return jsonify({'error': '请提供化学品ID列表'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        chemicals = []
        
        for chemical_id in chemical_ids:
            # 获取化学品基本信息
            cursor.execute("""
                SELECT 
                    c.编号,
                    c.CAS号,
                    c.中文名,
                    c.英文名,
                    c.分子式,
                    GROUP_CONCAT(a.别名 SEPARATOR '、') AS 所有别名
                FROM 化学品 c
                LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
                WHERE c.编号 = %s
                GROUP BY c.编号, c.CAS号, c.中文名, c.英文名, c.分子式
            """, (chemical_id,))
            
            basic_info = cursor.fetchone()
            
            if not basic_info:
                continue
            
            # 获取所有msds章节
            cursor.execute("""
                SELECT 
                    s.章节序号,
                    s.章节标题,
                    s.内容,
                    s.图片JSON
                FROM msds文档 d
                JOIN msds章节 s ON d.编号 = s.文档编号
                WHERE d.化学品编号 = %s
                ORDER BY s.章节序号
            """, (chemical_id,))
            
            msds_chapters = cursor.fetchall()
            
            chemicals.append({
                'basic_info': basic_info,
                'msds_chapters': process_results(msds_chapters),
                'found': True
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'chemicals': chemicals
        })
    
    except Exception as e:
        return jsonify({'error': f'查询失败: {str(e)}'}), 500

@app.route('/api/compatibility-check', methods=['POST'])
def check_compatibility():
    """多化学品共存禁忌分析接口"""
    import re
    
    data = request.get_json()
    chemical_ids = data.get('chemical_ids', [])
    
    if len(chemical_ids) < 2:
        return jsonify({'error': '至少需要2个化学品进行共存分析'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        chemical_data = []
        
        # 获取每个化学品的信息
        for chem_id in chemical_ids:
            # 获取基本信息
            cursor.execute("""
                SELECT 
                    c.编号, c.CAS号, c.中文名, c.英文名, c.分子式,
                    GROUP_CONCAT(a.别名 SEPARATOR '、') AS 所有别名
                FROM 化学品 c
                LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
                WHERE c.编号 = %s
                GROUP BY c.编号, c.CAS号, c.中文名, c.英文名, c.分子式
            """, (chem_id,))
            
            basic_info = cursor.fetchone()
            
            if not basic_info:
                continue
            
            # 获取第10章
            cursor.execute("""
                SELECT s.内容
                FROM msds文档 d
                JOIN msds章节 s ON d.编号 = s.文档编号
                WHERE d.化学品编号 = %s AND s.章节序号 = 10
            """, (chem_id,))
            
            chapter10 = cursor.fetchone()
            chapter10_content = chapter10['内容'] if chapter10 else ''
            
            # 获取第2章
            cursor.execute("""
                SELECT s.内容
                FROM msds文档 d
                JOIN msds章节 s ON d.编号 = s.文档编号
                WHERE d.化学品编号 = %s AND s.章节序号 = 2
            """, (chem_id,))
            
            chapter2 = cursor.fetchone()
            chapter2_content = chapter2['内容'] if chapter2 else ''
            
            # 提取不相容物质
            incompatible = extract_incompatible_substances(chapter10_content)
            
            # 提取GHS分类
            ghs_categories = extract_ghs_categories(chapter2_content)
            
            chemical_data.append({
                'id': basic_info['编号'],
                'name': basic_info['中文名'],
                'english_name': basic_info['英文名'],
                'cas': basic_info['CAS号'],
                'aliases': basic_info.get('所有别名', ''),
                'incompatible': incompatible,
                'ghs_categories': ghs_categories
            })
        
        cursor.close()
        conn.close()
        
        # 进行共存分析
        conflicts = []
        warnings = []
        
        for i, chem1 in enumerate(chemical_data):
            for chem2 in chemical_data[i+1:]:
                # 检查chem1的不相容列表是否包含chem2
                for incompatible_substance in chem1['incompatible']:
                    if match_substance_name(
                        incompatible_substance,
                        chem2['name'],
                        chem2['english_name'],
                        chem2['cas'],
                        chem2['aliases']
                    ):
                        conflicts.append({
                            'chemical_1': chem1['name'],
                            'chemical_2': chem2['name'],
                            'reason': f"{chem1['name']}的msds显示与{incompatible_substance}不相容",
                            'severity': 'high'
                        })
                
                # 检查chem2的不相容列表是否包含chem1
                for incompatible_substance in chem2['incompatible']:
                    if match_substance_name(
                        incompatible_substance,
                        chem1['name'],
                        chem1['english_name'],
                        chem1['cas'],
                        chem1['aliases']
                    ):
                        conflicts.append({
                            'chemical_1': chem2['name'],
                            'chemical_2': chem1['name'],
                            'reason': f"{chem2['name']}的msds显示与{incompatible_substance}不相容",
                            'severity': 'high'
                        })
                
                # GHS分类风险警告
                chem1_categories = set(chem1['ghs_categories'])
                chem2_categories = set(chem2['ghs_categories'])
                
                # 易燃 + 氧化性 = 高风险
                if (('易燃液体' in chem1_categories or '易燃气体' in chem1_categories) and 
                    ('氧化性液体' in chem2_categories or '氧化性固体' in chem2_categories or '氧化性气体' in chem2_categories)):
                    warnings.append({
                        'type': 'high_risk_combination',
                        'message': f"{chem1['name']}（易燃）与{chem2['name']}（氧化性）混合存在极高风险",
                        'severity': 'high'
                    })
                elif (('易燃液体' in chem2_categories or '易燃气体' in chem2_categories) and 
                      ('氧化性液体' in chem1_categories or '氧化性固体' in chem1_categories or '氧化性气体' in chem1_categories)):
                    warnings.append({
                        'type': 'high_risk_combination',
                        'message': f"{chem2['name']}（易燃）与{chem1['name']}（氧化性）混合存在极高风险",
                        'severity': 'high'
                    })
                
                # 多个易燃物质
                if (('易燃液体' in chem1_categories or '易燃气体' in chem1_categories) and 
                    ('易燃液体' in chem2_categories or '易燃气体' in chem2_categories)):
                    warnings.append({
                        'type': 'flammable_combination',
                        'message': f"{chem1['name']}和{chem2['name']}均为易燃物质，需加强防火措施",
                        'severity': 'medium'
                    })
        
        # 评估危害等级
        risk_score = len(conflicts) * 10 + sum(8 if w['severity'] == 'high' else 3 for w in warnings)
        
        if risk_score >= 20:
            hazard_level, hazard_desc = 'extreme', '极高风险'
        elif risk_score >= 10:
            hazard_level, hazard_desc = 'high', '高风险'
        elif risk_score >= 5:
            hazard_level, hazard_desc = 'medium', '中等风险'
        else:
            hazard_level, hazard_desc = 'low', '低风险'
        
        return jsonify({
            'chemicals': chemical_data,
            'conflicts': conflicts,
            'warnings': warnings,
            'safe': len(conflicts) == 0,
            'hazard_level': hazard_level,
            'hazard_description': hazard_desc,
            'risk_score': risk_score
        })
    
    except Exception as e:
        return jsonify({'error': f'分析失败: {str(e)}'}), 500

def extract_incompatible_substances(content):
    """从第10章内容中提取不相容物质"""
    if not content:
        return []
    
    import re
    incompatible = []
    lines = content.split('\n')
    
    # 方法1：匹配"禁配物"或"不相容物质"关键词，提取下一行或同一行的内容
    for i, line in enumerate(lines):
        line = line.strip()
        
        # 检查是否是关键词行
        if re.search(r'禁配物|不相容[的]?物质|应避免[与]?接触[的]?物质', line, re.IGNORECASE):
            # 尝试从当前行提取（如果有冒号）
            match = re.search(r'[：:]\s*(.+)', line)
            if match:
                substances_str = match.group(1).strip()
            # 或者从下一行提取
            elif i + 1 < len(lines):
                substances_str = lines[i + 1].strip()
            else:
                continue
            
            # 分割物质名称
            if substances_str:
                substances = re.split(r'[、,，;；/和与]+', substances_str)
                for substance in substances:
                    substance = substance.strip()
                    substance = re.sub(r'[。，,;；]$', '', substance)  # 移除末尾标点
                    if substance and len(substance) > 1 and substance not in ['无', '未明确', '无数据']:
                        incompatible.append(substance)
    
    # 方法2：直接匹配模式（兼容性匹配）
    patterns = [
        r'禁配物[：:]\s*(.+?)(?:\n|$)',
        r'不相容[的]?物质[：:]\s*(.+?)(?:\n|$)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        for match in matches:
            match = match.strip()
            if match:
                substances = re.split(r'[、,，;；/和与]+', match)
                for substance in substances:
                    substance = substance.strip()
                    substance = re.sub(r'[。，,;；]$', '', substance)
                    if substance and len(substance) > 1 and substance not in ['无', '未明确', '无数据']:
                        incompatible.append(substance)
    
    return list(set(incompatible))  # 去重

def extract_ghs_categories(content):
    """从第2章提取GHS分类"""
    if not content:
        return []
    
    import re
    categories = []
    
    ghs_keywords = [
        '易燃液体', '易燃气体', '易燃固体', '爆炸物', '氧化性液体', 
        '氧化性固体', '氧化性气体', '加压气体', '自反应物质', 
        '自燃液体', '自燃固体', '自热物质', '遇水放出易燃气体',
        '有机过氧化物', '金属腐蚀物', '急性毒性', '皮肤腐蚀',
        '严重眼损伤', '呼吸道致敏', '皮肤致敏', '生殖细胞致突变',
        '致癌性', '生殖毒性', '特异性靶器官毒性', '吸入危害',
        '对水生环境的危害', '对臭氧层的危害'
    ]
    
    for keyword in ghs_keywords:
        if keyword in content:
            categories.append(keyword)
    
    return categories

def match_substance_name(substance, chemical_name, chemical_english, cas_number, aliases):
    """匹配物质名称到化学品"""
    # 精确匹配
    if substance == chemical_name or substance == chemical_english or substance == cas_number:
        return True
    
    # 包含匹配
    if substance in chemical_name or substance in chemical_english:
        return True
    
    # 别名匹配
    if aliases:
        for alias in aliases.split('、'):
            if substance in alias or alias in substance:
                return True
    
    return False

@app.route('/api/compatibility-ai', methods=['POST'])
def check_compatibility_ai():
    """AI驱动的化学品共存禁忌分析"""
    data = request.get_json()
    chemical_ids = data.get('chemical_ids', [])
    
    if len(chemical_ids) < 2:
        return jsonify({'error': '至少需要2个化学品进行AI分析'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        chemicals_data = []
        
        # 获取每个化学品的详细信息
        for chem_id in chemical_ids:
            # 基本信息
            cursor.execute("""
                SELECT 
                    c.编号, c.CAS号, c.中文名, c.英文名, c.分子式,
                    GROUP_CONCAT(a.别名 SEPARATOR '、') AS 所有别名
                FROM 化学品 c
                LEFT JOIN 化学品别名 a ON c.编号 = a.化学品编号
                WHERE c.编号 = %s
                GROUP BY c.编号, c.CAS号, c.中文名, c.英文名, c.分子式
            """, (chem_id,))
            
            basic_info = cursor.fetchone()
            if not basic_info:
                continue
            
            # 获取第2章（危险性概述）
            cursor.execute("""
                SELECT s.内容
                FROM msds文档 d
                JOIN msds章节 s ON d.编号 = s.文档编号
                WHERE d.化学品编号 = %s AND s.章节序号 = 2
            """, (chem_id,))
            chapter2 = cursor.fetchone()
            chapter2_content = chapter2['内容'] if chapter2 else ''
            
            # 获取第10章（稳定性和反应性）
            cursor.execute("""
                SELECT s.内容
                FROM msds文档 d
                JOIN msds章节 s ON d.编号 = s.文档编号
                WHERE d.化学品编号 = %s AND s.章节序号 = 10
            """, (chem_id,))
            chapter10 = cursor.fetchone()
            chapter10_content = chapter10['内容'] if chapter10 else ''
            
            # 提取不相容物质和GHS分类
            incompatible = extract_incompatible_substances(chapter10_content)
            ghs_categories = extract_ghs_categories(chapter2_content)
            
            chemicals_data.append({
                'id': basic_info['编号'],
                'name': basic_info['中文名'],
                'cas': basic_info['CAS号'],
                'formula': basic_info['分子式'],
                'aliases': basic_info.get('所有别名', ''),
                'incompatible': incompatible,
                'ghs_categories': ghs_categories,
                'chapter2_summary': extract_chapter_summary(chapter2_content, 300),
                'chapter10_summary': extract_chapter_summary(chapter10_content, 300)
            })
        
        cursor.close()
        conn.close()
        
        if len(chemicals_data) < 2:
            return jsonify({'error': '未找到足够的化学品数据'}), 400
        
        # 调用AI分析
        ai_result = analyze_compatibility_with_ai(chemicals_data)
        
        if not ai_result['success']:
            return jsonify({'error': ai_result['error']}), 500
        
        return jsonify({
            'success': True,
            'report': ai_result['report'],
            'usage': ai_result.get('usage', {}),
            'chemicals': [{'id': c['id'], 'name': c['name'], 'cas': c['cas']} for c in chemicals_data]
        })
    
    except Exception as e:
        return jsonify({'error': f'AI分析失败: {str(e)}'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🔬 精简版危化品数据库 Web应用")
    print("=" * 60)
    print("📍 访问地址: http://localhost:5001")
    print("💡 数据库: 危化品简化数据库")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=True)

