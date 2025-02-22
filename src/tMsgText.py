from tMsgSender import tMsgSender
from config import Config
import os, re, logging,subprocess,asyncio
from func_timeout import func_set_timeout
class tMsgText:
    def __init__(self, message: dict, sender: tMsgSender, conf: Config):
        self.message: dict = message
        self.getInfo()
        self.sender: tMsgSender = sender
        self.conf: Config = conf
        self.urlRegex: str = r'http[s]?://(?:[a-zA-Z]|[0-9]|[^?\s])+'


    def getInfo(self):
        # extract always included message data
        self.message_id = self.message['message_id']
        self.date = self.message['date']
        self.chat = self.message['chat']
        self.isfrom = self.message['from']


    def checkCanReply(self, id) -> bool:
        logging.debug(f"Checking if allowed to reply to userID: {id}")
        match id in self.conf.allowedIds:
            case True: 
                logging.info(f"Allowed to reply to userID: {id}")
                return True
            case _:
                logging.info(f"Not allowed to process things from userID: {id}")
                return False


    def process(self):
        # Check for userID who sent the msg. Only do stuff if they're allowed to send stuff
        if self.checkCanReply(self.isfrom['id']) == False:
            logging.info(f"Sending not on allow list message for userID: {self.isfrom['id']}")
            self.sender.sendSilentMessage("Sorry, you're not on my allow list! Zzzz...", self.chat['id'])
            return
        
        match self.message:
            case _ if 'text' in self.message and self.message['text'] == "/start":
                # what to say when a new person talks to the bot
                logging.info(f"Received /start message from userID {self.isfrom['id']}, replying with info text")
                self.sender.sendSilentMessage("Hi! Please send a URL to get started!", self.chat['id'])
            case msg if 'text' in self.message and self.message['text'] != "/start":
                logging.info(f"Received text message from userID {self.isfrom['id']}")
                self.downloadAndRespond(msg['text'])
            case msg if 'caption' in self.message:
                logging.info(f"Received media message with caption text from userID {self.isfrom['id']}")
                self.downloadAndRespond(msg['caption'])
            case _:
                logging.warning(f"Received incompatible message from userID {self.isfrom['id']}")
                self.sender.sendSilentMessage("Incompatible message!", self.chat['id'])
        

    def downloadAndRespond(self, text):
        urls: list[str] = self.parseRegex(text)
        if len(urls) > 0:
            logging.debug(f"Mapping URLs to download and respond to")
            # Map() returns an iterator, and won't process any elements until told to.
            # Use the list() to force all elements to be processed
            for url in urls:
                asyncio.run(self.downloadUrl(url))
            # list(map(lambda x: self.handleDownloadOutcome(self.downloadUrl(x)), urls))
        else:
            logging.info(f"Replying couldn't find URL to userID {self.isfrom['id']}")
            self.reply([False, "Couldn't find a valid URL to use"])


    def parseRegex(self, toParse: str) -> list[str]:
        logging.debug(f"Parsing text against regex")
        urls: list[str] = re.findall(self.urlRegex, toParse)
        logging.debug(f"Found {len(urls)} matches")
        return urls
    

    async def downloadUrl(self, url: str) -> tuple[str, int]:
        logging.info(f"Attempting to gallery-dl download content from: {url}")
        try:
            output = subprocess.run(f"gallery-dl \"{url}\"",shell=True, capture_output=True,text=True,timeout=3600)
        except subprocess.TimeoutExpired:
            output.terminate()
            logging.info("超时了")
            return
        recode = output.returncode
        nums = 0
        res = []
        # tg 有速率限制，似乎是一分钟20个
        # sem = asyncio.Semaphore(2)
        # tasks = []
        logging.info("returncode")
        # if output.returncode == 1:
        #     logging.info(output.stdout)
        logging.info(output.returncode)
        if (output.returncode == 0 or output.returncode == 4 or output.returncode == 1) and self.conf.sendTg == "2" and self.conf.cChatid !="":
            try:
                outs = output.stdout.replace("#","").replace(" ","").split("\n")
                logging.info(outs)
                res = []
                nums = 0
                outs.reverse()
                for out in outs:
                    nums +=1
                    if out == "":
                        continue
                    res.append(out)
                    if nums >=5:
                        # task = asyncio.create_task(self.sender.sendMultipleFiles(res, self.chat['id'],sem))
                        # tasks.append(task)

                        self.sender.sendMultipleFiles(res,self.chat['id'],chat_id2=self.conf.cChatid)
                        res = []
                        nums = 0
                        # self.sender.sendSilentMessage(f"-----------------------", self.chat['id'])
                if res !=[]:
                    # task = asyncio.create_task(self.sender.sendMultipleFiles(res, self.chat['id'],sem))
                    # tasks.append(task)

                    self.sender.sendMultipleFiles(res,self.chat['id'],chat_id2=self.conf.cChatid)
                # await asyncio.gather(*tasks)
            except Exception as e:
                logging.warn(e)
            # release all permits
        # return (url, recode)
        match recode:
            case 0: 
                logging.info(f"Replying success for {url} to userID {self.isfrom['id']}")
                self.reply([True, url])
            case 4: 
                logging.info(f"Replying success for {url} to userID {self.isfrom['id']}")
                self.reply([True, url])
            case _: 
                logging.info(f"Replying failed download for {url} to userID {self.isfrom['id']}")
                self.reply([False, f"Encountered an error whilst downloading content for {url}"])

    def handleDownloadOutcome(self, downloadResult: tuple[str, int]) -> None:
        match downloadResult[1]:
            case 0: 
                logging.info(f"Replying success for {downloadResult[0]} to userID {self.isfrom['id']}")
                self.reply([True, downloadResult[0]])
            case _: 
                logging.info(f"Replying failed download for {downloadResult[0]} to userID {self.isfrom['id']}")
                self.reply([False, f"Encountered an error whilst downloading content for {downloadResult[0]}"])


    def reply(self, data):
        if data[0] == True:
            logging.debug(f"Sending sendMessage request to chat_id {self.chat['id']} with text 'Done for URL {data[1]}'")
            self.sender.sendSilentMessage(f"Done for URL {data[1]}", self.chat['id'])
        else:
            logging.debug(f"Sending sendMessage request to chat_id {self.chat['id']} with text 'Failed! {data[1]}'")
            self.sender.sendSilentMessage(f"Failed! {data[1]}", self.chat['id'])
