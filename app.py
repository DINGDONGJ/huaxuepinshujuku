"""
危化品数据库 - Web应用后端
使用Flask框架 + MySQL数据库
"""

from flask import Flask, render_template, request, jsonify
import pymysql
import json
from decimal import Decimal

app = Flask(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',  # 请填入您的MySQL密码
    'database': '危化品数据库',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def convert_to_json_serializable(obj):
    """转换对象为JSON可序列化格式"""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8')
    return obj

def process_results(results):
    """处理查询结果，转换为JSON可序列化格式"""
    processed = []
    for row in results:
        processed_row = {}
        for key, value in row.items():
            processed_row[key] = convert_to_json_serializable(value)
        processed.append(processed_row)
    return processed

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    """搜索化学品完整信息"""
    data = request.get_json()
    chemical_name = data.get('name', '')
    
    if not chemical_name:
        return jsonify({'error': '请输入化学品名称'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 调用存储过程
        cursor.callproc('获取化学品完整信息', [chemical_name])
        
        # 获取所有结果集
        results = []
        
        # 方法1：使用 nextset() 遍历所有结果集
        while True:
            result_set = cursor.fetchall()
            if result_set:
                results.append(process_results(result_set))
            if not cursor.nextset():
                break
        
        cursor.close()
        conn.close()
        
        if not results or not results[0]:
            return jsonify({'error': '未找到该化学品'}), 404
        
        # 构造返回数据
        response = {
            'basic_info': results[0][0] if len(results) > 0 else None,
            'management': results[1] if len(results) > 1 else [],
            'sop': results[2] if len(results) > 2 else [],
            'ghs': results[3] if len(results) > 3 else [],
            'transport': results[4] if len(results) > 4 else [],
            'catalog': results[5] if len(results) > 5 else [],
            'emergency': results[6] if len(results) > 6 else [],
            'aliases': results[7][0] if len(results) > 7 and results[7] else None,
            'msds': results[8] if len(results) > 8 else []  # MSDS章节（16个部分）
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': f'查询失败: {str(e)}'}), 500

@app.route('/api/guide', methods=['POST'])
def get_guide():
    """获取引导词"""
    data = request.get_json()
    chemical_name = data.get('name', '')
    
    if not chemical_name:
        return jsonify({'error': '请输入化学品名称'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 调用存储过程
        cursor.callproc('获取引导词', [chemical_name])
        
        # 获取结果
        guides = process_results(cursor.fetchall())
        
        cursor.close()
        conn.close()
        
        return jsonify({'guides': guides})
    
    except Exception as e:
        return jsonify({'error': f'查询失败: {str(e)}'}), 500

@app.route('/api/category', methods=['POST'])
def search_by_category():
    """按类别查询"""
    data = request.get_json()
    chemical_name = data.get('name', '')
    category = data.get('category', '')
    
    if not chemical_name or not category:
        return jsonify({'error': '参数不完整'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 调用存储过程
        cursor.callproc('按类别查询', [chemical_name, category])
        
        # 获取结果
        data_list = process_results(cursor.fetchall())
        
        cursor.close()
        conn.close()
        
        return jsonify({'data': data_list})
    
    except Exception as e:
        return jsonify({'error': f'查询失败: {str(e)}'}), 500

@app.route('/api/chemicals', methods=['GET'])
def get_chemicals():
    """获取所有化学品列表（用于自动补全）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT CAS号, 中文名, 英文名 
            FROM 化学品 
            WHERE 是否有效 = 1
            ORDER BY 中文名
        """)
        
        chemicals = process_results(cursor.fetchall())
        
        cursor.close()
        conn.close()
        
        return jsonify({'chemicals': chemicals})
    
    except Exception as e:
        return jsonify({'error': f'查询失败: {str(e)}'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 危化品数据库 Web应用启动中...")
    print("=" * 60)
    print("📍 访问地址: http://localhost:5000")
    print("💡 提示: 请确保已在 app.py 中配置正确的数据库密码")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)

