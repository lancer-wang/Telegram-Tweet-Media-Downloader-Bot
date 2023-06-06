import os,sqlite3
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
def insert_db2(file_id, file_path):
    db = get_db3()
    cursor = db.cursor()
    insert_sql = """insert into twmedia_new(file_id, file_path) VALUES ("{0}","{1}")""".format(file_id, file_path)
    cursor.execute(insert_sql)
    db.commit()
    cursor.close()
    db.close()
def select_db2(file_path):
    db = get_db3()
    cursor = db.cursor()
    insert_sql = """select file_id From twmedia_new where file_path = "{0}" limit 1 """.format(file_path)
    cursor.execute(insert_sql)
    res = cursor.fetchall()
    cursor.close()
    db.close()
    if res:
        return res[0][0]
    else:
        return "nares"
print(select_db2("./gallery-dl/twitter/laowangshitu/1665815416650735617_1_laowangshitu.mp4"))