# -*- coding: utf-8 -*-

from sre_parse import State
import aiohttp
from aiohttp import web
import json
import datetime,os

def get_date():
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    return current_date

def get_accounts():
    accounts = []
    with open("/mnt/c/Users/path/to/your/bean/file/1.bean",'r',encoding='utf-8') as f:
        lines = f.readlines()
    for i in lines:
        if 'open' in i:
            accounts.append(i[16:-1])
    with open("/mnt/c/Users/path/to/your/bean/file/accounts.bean",'r',encoding='utf-8') as f:
        lines = f.readlines()
    for i in lines:
        if 'open' in i:
            accounts.append(i[16:-1])
    return accounts

async def reply(ws,msg):
    body = {
        "action": "send_private_msg",
            "params": {
                "user_id": your_qq_id,
                "message": msg
            },
    }
    await ws.send_json(body)


async def websocket_handler(request):
    global session,buf,temp_buf
    # ws对象
    ws = web.WebSocketResponse()
    # 等待用户连接
    await ws.prepare(request)

    async for message in ws:
        if message.type == aiohttp.WSMsgType.TEXT:
            if message.data == 'close':
                await ws.close()
            else:
                if 'post_type' in  message.data:
                    msg=json.loads(message.data)
                    if msg['post_type'] == 'message':
                        temp_msg = msg['message'].split(' ')
                        order = temp_msg[0]
                        if order == 'add':
                            if len(temp_msg) > 1:
                                bill = '"'+temp_msg[1]+'"'
                            else:
                                bill = '""'
                            buf = buf + get_date() + " * " + bill
                            await reply(ws,buf)
                            session['state'] = '候选条目'
                        elif order == 'sav':
                            session = {"state":"","acc":"","num":0,'chooser':[]}
                            with open("/mnt/c/Users/path/to/your/bean/file/1.bean",'a',encoding='utf-8') as f:
                                f.write(buf)
                                f.write('\n')
                            await reply(ws,'退出本次记账，新增条目：\n'+buf)
                            buf = ''
                            acc = ['9328','微信','支付宝']
                            result = '账户余额：'
                            for i in acc:
                                ret = os.popen('bean-report /mnt/c/Users/path/to/your/bean/file/1.bean bal -e '+ i)
                                result = result +'\n'+ ret.read().strip()
                            await reply(ws,result)
                        elif order == 'del':
                            session['state'] = '编辑'
                            temp_buf = buf.split('\n')
                            bill = ''
                            for i in range(len(temp_buf)):
                                if i > 0 :
                                    bill = bill + '\n'
                                bill  = bill + str(i) +' → ' + temp_buf[i]
                            await reply(ws,'请选择要删除的条目，a为退出：\n'+bill)
                        elif order == 'exit':
                            await reply(ws,'已放弃本次记账')
                            session = {"state":"","acc":"","num":0,'chooser':[]}
                            buf = ''
                            temp_buf = ''
                        else:
                            if (session['state']):
                                match session['state']:
                                    case '编辑':
                                        if order == 'a':
                                            session['state'] = '候选条目'
                                            await reply(ws,'已退出编辑，请继续输入条目')
                                        else:
                                            del(temp_buf[int(order)])
                                            bill = ''
                                            for i in temp_buf:
                                                bill = bill + i + '\n'
                                            buf = bill
                                            temp_buf = []
                                            session['state'] = '候选条目'
                                            await reply(ws,'已删除第'+order+'项，目前如下：\n'+buf)
                                    case '候选条目':
                                        accounts = get_accounts()
                                        order = msg['message']
                                        session['acc'] = order.split(' ')[0]
                                        try:
                                            session['num'] = order.split(' ')[1]
                                        except:
                                            session['num'] = ''
                                        for i in accounts:
                                            if session['acc'] in i.lower():
                                                session['chooser'].append(i)
                                        if session['chooser']:
                                            bill = ''
                                            for i in range(len(session['chooser'])):
                                                if i > 0 :
                                                    bill = bill + '\n'
                                                bill = bill + str(i) +' → ' + session['chooser'][i]
                                            session['state'] = '选择条目'
                                        else:
                                            bill = '未找到候选词，请重新输入'
                                        await reply(ws,bill)
                                    case '选择条目':
                                        bill = '  ' + session['chooser'][int(order)] + ' ' +session['num']
                                        if session['num']:
                                            bill = bill + ' CN'
                                        buf = buf + '\n' + bill
                                        session = {"state":"候选条目","acc":"","num":0,'chooser':[]}
                                        await reply(ws,bill)
                                    case _:
                                        await reply(ws,"error")


        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())

    # 断开连接了
    print('websocket connection closed')
    return ws

if __name__ == '__main__':
    global session,buf,temp_buf
    session = {"state":"","acc":"","num":0,'chooser':[]}
    buf = ''
    temp_buf = []
    app = web.Application()
    app.add_routes([web.get('/', websocket_handler)])
    web.run_app(app,host='127.0.0.1',port=1314)
