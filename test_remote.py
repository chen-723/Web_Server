import pymysql
conn = pymysql.connect(
    host='111dc5664cn09.vicp.fun',
    port=15894,
    user='remote',
    password='123456',
    db='vue_login_demo',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
with conn.cursor() as cur:
    cur.execute("SELECT 1")
    print(cur.fetchone())
conn.close()