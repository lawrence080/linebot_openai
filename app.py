from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
import json
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

flag = False


def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0, max_tokens=500)
    print(response)
    # 重組回應
    answer = response['choices'][0]['text'].replace('。','')
    return answer


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    d = json.loads(body)
    user_id=d["events"][0]["source"]["userId"]

    rich_menu_id = setUpInterface()
    with open("richmenu.png",'rb') as f:
        line_bot_api.set_rich_menu_image(rich_menu_id, "image/png", f)

    line_bot_api.link_rich_menu_to_user(user_id,rich_menu_id)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


#處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event, rep):
    if flag == True:
        msg = event.message.text
        GPT_answer = GPT_response(msg)
        print(GPT_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
        button_template_message = TemplateSendMessage(
        alt_text = "invisiable",
        template = ButtonsTemplate(
            thumbnail_imgae_url = "",
            title = "any more question?",
            text = "yes or no",
            actions = [
                    PostbackAction(
                        label = "yes",
                        display_text = "what's your question",
                        data = "yes"
                    ),
                    PostbackAction(
                        label = "no",
                        display_text = "ok thank you ",
                        data = "no"
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token,button_template_message )
        return
    else :
        message  = "please chose one of following before we can help you"
        line_bot_api.reply_message(event.reply_token,TextSendMessage(message) )
    
        
    



@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)


    

def setUpInterface():
    rich_menu_to_create = RichMenu(
        size=RichMenuSize(width=1200, height=405),
        selected=True,
        name="first richMenu",  # display name
        chat_bar_text="測試使用",
        areas=[RichMenuArea(  # 這邊是陣列的格式，可以動態設定自己要的區域想要有什麼功能
            bounds=RichMenuBounds(x=0, y=0, width=400, height=405),
            action= URIAction(label='link test', uri='https://line.me')),
            RichMenuArea(bounds=RichMenuBounds(x=400, y=0, width=400, height=405),
            action= {
                "type":"postback",
                "label":'postback',
                "display_text":'has question to AI',
                "data":'action=buy&itemid=2'
            }),
            RichMenuArea(bounds=RichMenuBounds(x=800, y=0, width=400, height=405),
            action= 
            {
                "type":"postback",
                "label":'postback',
                "display_text":'postback text',
                "data":'action=buy&itemid=1'
            }
                
            )]
    )
    rich_menu_id = line_bot_api.create_rich_menu(rich_menu=rich_menu_to_create)
    return rich_menu_id
    print(rich_menu_id)


@handler.add(PostbackEvent)
def buttontemplate(self,event):
    if event.postback.data == 'action=buy&itemid=1':
        button_template_message = TemplateSendMessage(
        alt_text = "invisiable",
        template = ButtonsTemplate(
            thumbnail_imgae_url = "",
            title = "button testing ",
            text = "text....",
            actions = [
                    URIAction(
                        label = "line",
                        uri = "https://line.me"
                    ),
                    MessageAction(
                        label = "button testing",
                        text = "testing "
                    ),
                    PostbackAction(
                        label = "postback testing",
                        display_text = "test postback plz",
                        data = "testing"
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token,button_template_message )
        return
    elif event.postback.data == 'action=buy&itemid=2' or 'yes':
        self.flag = True
    elif event.postback.data == 'no':
        self.flag = False
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)