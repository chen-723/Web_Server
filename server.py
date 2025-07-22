from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)

# ② 配置数据库连接（改成你自己的）
def get_conn():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        db='vue_login_demo',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# --------------- 登录接口（保持原样） ---------------
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'code': 1, 'message': '用户名或密码不能为空'}), 401

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE username = %s AND password = %s",
                (username, password)
            )
            user = cur.fetchone()
            if user:
                return jsonify({
                    'code': 0,
                    'token': 'fake-jwt-token',
                    'user': {'username': user['username']}
                }), 200
            else:
                return jsonify({'code': 1, 'message': '用户名或密码错误'}), 401
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500
    finally:
        conn.close()

# --------------- 新增注册接口 ---------------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'code': 3, 'message': '用户名或密码不能为空'}), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return jsonify({'code': 2, 'message': '用户名已存在'}), 400

            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            return jsonify({'code': 0, 'message': '注册成功'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'code': 4, 'message': str(e)}), 500
    finally:
        conn.close()

# --------------- 启动 ---------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)