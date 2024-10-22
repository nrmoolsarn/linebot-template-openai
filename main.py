# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import openai
import os
import sys
import json

import aiohttp

from fastapi import Request, FastAPI, HTTPException
from linebot import (
    AsyncLineBotApi, WebhookParser
)
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())  # read local .env file


# Initialize OpenAI API

def call_openai_chat_api(user_message, message_history=None):
    if message_history is None:
        message_history = []

    openai.api_key = os.getenv('OPENAI_API_KEY', None)

    # เพิ่มข้อความของผู้ใช้เข้าไปในประวัติการสนทนา
    message_history.append({"role": "user", "content": user_message})

    # กำหนดข้อความระบบ
    system_message = {"role": "system", "content": "คุณเป็นหมอดูดวงจากวันเกิด ก่อนคิดและตอบ เท่านั้น  !!!ตอบเป็นไทยเท่านั้น!!! "}
    messages = [system_message] + message_history

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages
    )

    # เพิ่มการตอบกลับของผู้ช่วยเข้าไปในประวัติการสนทนา
    assistant_message = {"role": "assistant", "content": response.choices[0].message['content']}
    message_history.append(assistant_message)

    return response.choices[0].message['content'], message_history



# Get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('ChannelSecret', None)
channel_access_token = os.getenv('ChannelAccessToken', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

# Initialize LINE Bot Messaigng API
app = FastAPI()
session = aiohttp.ClientSession()
async_http_client = AiohttpAsyncHttpClient(session)
line_bot_api = AsyncLineBotApi(channel_access_token, async_http_client)
parser = WebhookParser(channel_secret)


@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        result = call_openai_chat_api(event.message.text)

        await line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )

    return 'OK'
