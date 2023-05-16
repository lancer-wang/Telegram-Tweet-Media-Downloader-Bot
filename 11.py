def test(outs,chat):
    for out in outs:
        nums +=1
        if out == "":
            continue
        res.append(out)
        if nums >=5:
            sendMultipleFiles(res,chat['id'])
            # self.sender.sendMultipleFiles(res,self.chat['id'],chat_id2=self.conf.cChatid)
            res = []
            nums = 0
            sendSilentMessage(f"-----------------------", chat['id'])
    if res !=[]:
        sendMultipleFiles(res,chat['id'])