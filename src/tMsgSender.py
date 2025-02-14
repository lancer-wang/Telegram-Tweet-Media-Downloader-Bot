import requests
import asyncio
import logging,sqlite3,os
import telegram,time
from telegram import InputMediaPhoto, InputMediaVideo, InputMediaDocument

def get_db3():
    if not os.path.exists("/etc/twmedia.db"):
        con = sqlite3.connect("/etc/twmedia.db")
        cur = con.cursor()
        sql = """CREATE TABLE IF NOT EXISTS `twmedia_new`  (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `file_id` varchar(255)  NULL DEFAULT NULL,
  `file_path` varchar(255)  NULL DEFAULT NULL
)"""
        cur.execute(sql)
        cur.close()
        con.close()
    con2 = sqlite3.connect("/etc/twmedia.db")
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
    
    # logging.info("数据添加成功")
class recievedData:
    def __init__(self, isOk: bool, isErr: bool = False, statusCode: int = -1, content: bytes = bytearray(0), errDetails: str = ""):
        self.ok: bool = isOk
        self.isErr: bool = isErr
        self.statusCode: int = statusCode
        self.content: bytes = content
        self.errDetails: str = errDetails


class tMsgSender:
    def __init__(self, token: str):
        self.token = token
        self.tAPIUrl: str = f"https://api.telegram.org/bot{self.token}"

    def generateRequest(self, msgParams: list) -> str:
        logging.debug("Generating request string")

        match msgParams:
            # if there's multiple parameters, have to append them correctly
            case p if len(msgParams) > 3:
                requestString = f"{self.tAPIUrl}/{str(p[0])}?"
                # skip the 0th item, already appended it to the requestString
                for i in range(1, len(p)-3, 2):
                    requestString = f"{requestString}{str(p[i])}={str(p[i+1])}&"
                requestString = f"{requestString}{str(p[-2])}={str(p[-1])}"
            case p if len(msgParams) > 1:
                requestString = f"{self.tAPIUrl}/{str(p[0])}?{str(p[1])}={str(p[2])}"
            case p:
                requestString = f"{self.tAPIUrl}/{str(p[0])}"
        logging.debug(f"Generated request string: {requestString}")
        return requestString

    def sendGetMe(self) -> recievedData:
        return self.sendRequest(["getMe"])

    def sendGetUpdates(self, msgOffset: int, pollTimeout: int, updatesToFetch: str) -> recievedData:
        return self.sendRequest(["getUpdates", "offset", msgOffset, "timeout", pollTimeout, "allowed_updates", updatesToFetch])

    def sendMessage(self, text: str, chat_id: str) -> recievedData:
        return self.sendRequest(["sendMessage", "chat_id", chat_id, "text", text, "disable_web_page_preview", True])

    def sendSilentMessage(self, text: str, chat_id: str) -> recievedData:
        return self.sendRequest(["sendMessage", "chat_id", chat_id, "text", text, "disable_web_page_preview", True, "disable_notification", True])

    def sendMultipleFiles(self, file_paths, chat_id: str, chat_id2: str) -> recievedData:
        upload_url_photo = self.tAPIUrl + "/sendPhoto"
        upload_url_video = self.tAPIUrl + "/sendVideo"
        upload_url_document = self.tAPIUrl + "/sendDocument"
        upload_params = {
            "chat_id": chat_id2
        }
        media_group = []

        # 遍历本地媒体列表，根据文件类型上传文件，并获取file_id
        for media in file_paths:
            file_id = select_db2(media)
            if file_id == "nares":
                # 判断文件类型，如果是图片，使用sendPhoto方法和photo参数
                if media.endswith((".png", ".jpg", ".jpeg")):
                    upload_files = {
                        "photo": open(media, "rb")
                    }
                    response = requests.post(
                        upload_url_photo, data=upload_params, files=upload_files)
                    file_id = response.json()["result"]["photo"][-1]["file_id"]
                    media_type = "photo"
                # 判断文件类型，如果是视频，使用sendVideo方法和video参数
                elif media.endswith((".mp4", ".avi", ".mov")):
                    upload_files = {
                        "video": open(media, "rb")
                    }
                    response = requests.post(
                        upload_url_video, data=upload_params, files=upload_files)
                    file_id = response.json()["result"]["video"]["file_id"]
                    media_type = "video"
                # 如果文件类型不是图片或视频，跳过该文件，并打印提示信息
                else:
                    upload_files = {
                        "document": open(media, "rb")
                    }
                    response = requests.post(
                        upload_url_document, data=upload_params, files=upload_files)
                    file_id = response.json()["result"]["document"]["file_id"]
                    media_type = "document"
                insert_db2(file_id,media)
            else:
                if media.endswith(".jpg"):
                    media_type = "photo"
                elif media.endswith(".mp4"):
                    media_type = "video"
                else:
                    media_type = "document"
            # 将上传后的媒体信息添加到媒体组中，最多10个
            if len(media_group) < 10:
                if len(media_group) == 0:
                    media_group.append({
                        "type": media_type,
                        "media": file_id,
                        "caption":"#########################"
                    })
                else:
                    media_group.append({
                        "type": media_type,
                        "media": file_id
                    })
            else:
                print("Media group is full. Cannot add more.")
                break

        # 定义要发送的请求的URL，使用sendMediaGroup方法
        request_url = self.tAPIUrl + "/sendMediaGroup"

        # 定义要发送的请求的参数，使用json格式
        request_params = {
            "chat_id": chat_id,
            "media": media_group
        }

        # 发送请求，并获取响应
        response = requests.post(request_url, json=request_params)
        time.sleep(10)
        logging.info(response)

    async def sendMultipleFiles2(self, file_paths, chat_id: str, sem):
        async with sem:
            # Create an updater object with your bot token
            # updater = Updater(token=self.tAPIUrl)
            bot = telegram.Bot(token=self.token)
            # Get the bot instance from the updater
            # bot = updater.bot
            # Create an empty list to store the media group
            media_group = []

            # Loop through the local media list, upload the files according to their type, and get the file_id
            for _, file_path in enumerate(file_paths):
                try:
                    # Check the file type, if it is an image, use send_photo method and photo parameter
                    # 判断文件类型，如果是图片，就创建一个InputMediaPhoto对象
                    if file_path.endswith((".png", ".jpg", ".jpeg")):
                        media = InputMediaPhoto(open(file_path, "rb"))
                    # 如果是视频，就创建一个InputMediaVideo对象
                    elif file_path.endswith((".mp4", ".avi", ".mov")):
                        media = InputMediaVideo(open(file_path, "rb"))
                    # 如果是其他类型，就文件
                    else:
                        media = InputMediaDocument(open(file_path, "rb"))
                except Exception as e:
                    logging.warn(file_path)
                    logging.warn(e)
                    continue
                # 把媒体对象添加到媒体组列表中
                media_group.append(media)
                # Add the uploaded media information to the media group, up to 10
            try:
                await bot.send_media_group(chat_id=chat_id, media=media_group)
                # self.sendSilentMessage(f"-----------------------",chat_id=chat_id)
                # await bot.send_message(chat_id=chat_id, text="-----------------------")
            except Exception as e:
                logging.warn(e)
                # for _, file_path2 in enumerate(file_paths):
                #     try:
                #         # Check the file type, if it is an image, use send_photo method and photo parameter
                #         # 判断文件类型，如果是图片，就创建一个InputMediaPhoto对象
                #         if file_path2.endswith((".png", ".jpg", ".jpeg")):
                #             await bot.send_photo(chat_id=chat_id, photo=(open(file_path2, "rb")))
                #         # 如果是视频，就创建一个InputMediaVideo对象
                #         elif file_path2.endswith((".mp4", ".avi", ".mov")):
                #             await bot.send_video(chat_id, video=(open(file_path2, "rb")))
                #         # 如果是其他类型，就文件
                #         else:
                #             await bot.send_document(chat_id, document=open(file_path2, "rb"))
                #     except Exception as e:
                #         logging.warn(file_path2)
                #         logging.warn(e)
                #         continue
            await asyncio.sleep(60)
        # try:
        #     await bot.send_media_group(chat_id=chat_id, media=media_group)
        # except Exception as e:
        #     logging.warn(e)
        #     logging.warn(media_group)
        # Use send_media_group method to send the media group to the chat id
        # await bot.send_media_group(chat_id=chat_id, media=media_group)

    def sendRequest(self, msgParams: list) -> recievedData:
        requestString = self.generateRequest(msgParams)

        try:
            request: requests.Response = requests.get(requestString)
            # return True/False for a status code of 2XX, the status code itself and the response content
            return recievedData(request.ok, statusCode=request.status_code, content=request.content)
        except Exception as e:
            return recievedData(isOk=False, isErr=True, errDetails=f"Error making request {requestString}, {str(e)}")
