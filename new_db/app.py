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

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PDF_FOLDER'] = 'pdf'

# 确保文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)

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

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/msds_json/<path:filename>')
def serve_msds_files(filename):
    """提供MSDS JSON文件夹中的文件（包括图片）"""
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
        
        # 查找化学品
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
        """, (f'%{keyword}%', f'%{keyword}%', keyword, f'%{keyword}%'))
        
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            return jsonify({'error': '未找到该化学品'}), 404
        
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
        
        # 获取MSDS章节
        cursor.execute("""
            SELECT 
                s.章节序号,
                s.章节标题,
                s.内容,
                s.图片JSON,
                d.编制单位,
                d.编制依据,
                d.编制日期
            FROM MSDS文档 d
            JOIN MSDS章节 s ON d.编号 = s.文档编号
            WHERE d.化学品编号 = %s
            ORDER BY s.章节序号
        """, (chemical_id,))
        
        msds_chapters = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'basic_info': basic_info,
            'msds_chapters': process_results(msds_chapters)
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
            LEFT JOIN MSDS文档 m ON c.编号 = m.化学品编号
            LEFT JOIN MSDS章节 s ON m.编号 = s.文档编号
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
    """导入JSON格式的MSDS数据"""
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
            
            # 3. 处理MSDS文档
            cursor.execute("SELECT 编号 FROM MSDS文档 WHERE 化学品编号 = %s", (chemical_id,))
            msds_doc = cursor.fetchone()
            
            if msds_doc:
                msds_doc_id = msds_doc['编号']
                # 更新MSDS文档
                cursor.execute("""
                    UPDATE MSDS文档 
                    SET 编制单位 = %s, 编制日期 = %s, 编制依据 = %s
                    WHERE 编号 = %s
                """, (
                    msds_meta.get('编制单位'),
                    msds_meta.get('编制日期'),
                    msds_meta.get('编制依据'),
                    msds_doc_id
                ))
                
                # 删除旧的章节
                cursor.execute("DELETE FROM MSDS章节 WHERE 文档编号 = %s", (msds_doc_id,))
            else:
                # 插入新MSDS文档
                cursor.execute("""
                    INSERT INTO MSDS文档 (化学品编号, 编制单位, 编制日期, 编制依据)
                    VALUES (%s, %s, %s, %s)
                """, (
                    chemical_id,
                    msds_meta.get('编制单位'),
                    msds_meta.get('编制日期'),
                    msds_meta.get('编制依据')
                ))
                msds_doc_id = cursor.lastrowid
            
            # 4. 插入MSDS章节
            for chapter in chapters:
                # 处理图片数据
                images_json = None
                if '图片' in chapter and chapter['图片']:
                    images_json = json.dumps(chapter['图片'], ensure_ascii=False)
                
                cursor.execute("""
                    INSERT INTO MSDS章节 (文档编号, 章节序号, 章节标题, 内容, 图片JSON)
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
            
            # 删除化学品（外键级联会自动删除别名、MSDS文档和章节）
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

@app.route('/pdf/<path:filename>')
def serve_pdf(filename):
    """提供PDF文件访问"""
    try:
        return send_from_directory(app.config['PDF_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({'error': 'PDF文件未找到'}), 404

if __name__ == '__main__':
    print("=" * 60)
    print("🔬 精简版危化品数据库 Web应用")
    print("=" * 60)
    print("📍 访问地址: http://localhost:5001")
    print("💡 数据库: 危化品简化数据库")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=True)

