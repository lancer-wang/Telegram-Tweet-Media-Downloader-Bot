import os,sqlite3,pymysql
def get_db3():
    if not os.path.exists("/cobudy/Telegram-Tweet-Media-Downloader-Bot/etc/twmedia.db"):
        con = sqlite3.connect("/cobudy/Telegram-Tweet-Media-Downloader-Bot/etc/twmedia.db")
        cur = con.cursor()
        sql = """CREATE TABLE IF NOT EXISTS `twmedia_new`  (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `file_id` varchar(255)  NULL DEFAULT NULL,
  `file_path` varchar(255)  NULL DEFAULT NULL
)"""
        cur.execute(sql)
        cur.close()
        con.close()
    con2 = sqlite3.connect("/cobudy/Telegram-Tweet-Media-Downloader-Bot/etc/twmedia.db")
    return con2

def get_db():
    host = "103.150.8.222"
    user = "my_db"
    dbname = "my_db"
    password = "XD4tRWY3t3ZccwZs"

    # user = "adm"
    # dbname = "test"
    # password = "123456"

    port = 3306
    charset = 'utf8mb4'
    # 去重
    db2 = pymysql.Connect(host=host, port=port, user=user, passwd=password, db=dbname, charset=charset)
    return db2
def select_db2(ids):
    db = get_db3()
    cursor = db.cursor()
    insert_sql = """select * From twmedia_new where  id > {0} """.format(ids)

    cursor.execute(insert_sql)
    res = cursor.fetchall()
    cursor.close()
    db.close()
    if res:
        return res
    else:
        return "nares"
def insert_db(file_id, file_path):
    db = get_db()
    cursor = db.cursor()
    insert_sql = """insert into twmedia_new(file_id, file_path) VALUES ("{0}","{1}")""".format(file_id, file_path)
    cursor.execute(insert_sql)
    db.commit()
    cursor.close()
    db.close()
    print("数据添加成功")
# print(select_db2("./gallery-dl/twitter/laowangshitu/1665815416650735617_1_laowangshitu.mp4"))
db = get_db()
cursor = db.cursor()
last_sql = "SELECT count(id) as num FROM twmedia_new"
cursor.execute(last_sql)
last_res = cursor.fetchall()
datas = select_db2(last_res[0][0])
if datas != "nares":
    for i in datas:
        insert_db(i[1],i[2])
