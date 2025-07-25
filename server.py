from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql

from flask_socketio import SocketIO, emit

app = Flask(__name__)
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*")

# ② 配置数据库连接（这里用的远程数据库，因为我的数据库已经暴露出去了）
def get_conn():
    return pymysql.connect(
        host='111dc5664cn09.vicp.fun',
        port=15894,
        user='remote',
        password='123456',
        db='vue_login_demo',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# --------------- 登录接口（保持原样） ---------------
# 替换 /api/login 的返回体
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, email, avatar_url, created_at FROM users WHERE username=%s AND password=%s",
                (username, password)
            )
            user = cur.fetchone()
            if user:
                return jsonify({
                    'code': 0,
                    'token': 'fake-jwt-token',
                    'user': {
                        'username': user['username'],
                        'email': user['email'],
                        'avatar_url': user['avatar_url'],
                        'created_at': user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    }
                }), 200
            else:
                return jsonify({'code': 1, 'message': '用户名或密码错误'}), 401
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500
    finally:
        conn.close()

# --------------- 新增注册接口 ---------------
# 替换 /api/register 的插入语句
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username  = data.get('username', '').strip()
    password  = data.get('password', '').strip()
    email     = data.get('email', '').strip()         # 新增
    avatar_url= data.get('avatar_url', '')            # 新增

    if not username or not password:
        return jsonify({'code': 3, 'message': '用户名或密码不能为空'}), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username=%s", (username,))
            if cur.fetchone():
                return jsonify({'code': 2, 'message': '用户名已存在'}), 400
            cur.execute(
                "INSERT INTO users(username, password, email, avatar_url) VALUES(%s,%s,%s,%s)",
                (username, password, email, avatar_url)
            )
            conn.commit()
            return jsonify({'code': 0, 'message': '注册成功'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'code': 4, 'message': str(e)}), 500
    finally:
        conn.close()

# ---------------- 步骤 1：查历史消息 ----------------
@app.route('/api/chat/messages', methods=['GET'])
def get_messages():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, user_id, username, content, created_at
                FROM messages
                ORDER BY id ASC
                LIMIT 100
            """)
            rows = cur.fetchall()
            # 把 datetime 转字符串
            for r in rows:
                r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            return jsonify({'code': 0, 'data': rows}), 200
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500
    finally:
        conn.close()

# ---------------- 步骤 2：发送消息 ----------------
@app.route('/api/chat/messages', methods=['POST'])
def post_message():
    data = request.get_json()
    user_id  = data.get('user_id')
    username = data.get('username', '').strip()
    content  = data.get('content', '').strip()

    if not user_id or not username or not content:
        return jsonify({'code': 1, 'message': '字段缺失'}), 400

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages(user_id, username, content) VALUES (%s,%s,%s)",
                (user_id, username, content)
            )
            conn.commit()
        return jsonify({'code': 0, 'message': '发送成功'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'code': 2, 'message': str(e)}), 500
    finally:
        conn.close()    

# ---------- 步骤 6-1：WebSocket 事件 ----------
@socketio.on('send')            # 前端发 send 事件
def handle_send(data):
    """
    data = {user_id:int, username:str, content:str}
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages(user_id, username, content) VALUES(%s,%s,%s)",
                (data['user_id'], data['username'], data['content'])
            )
            conn.commit()
            msg_id = cur.lastrowid
            # 把刚插入的行取出来，广播
            cur.execute(
                "SELECT id,username,content,created_at FROM messages WHERE id=%s",
                (msg_id,)
            )
            row = cur.fetchone()
            row['created_at'] = row['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            emit('new_message', row, broadcast=True)   # 所有人收到
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()            

# --------------- 启动 ---------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)