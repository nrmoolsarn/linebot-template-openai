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

import openai
import os

# Initialize OpenAI API using the correct method
openai.api_key = os.getenv('OPENAI_API_KEY')

# Correct implementation for the Assistant API
def call_openai_chat_api(user_message):
    # Create the Assistant (replace this with the appropriate API call if needed)
    assistant = openai.Assistant.create(
        name="Astrology Assistant",
        instructions="คุณเป็นหมอดูดวงจากวันเกิด ก่อนคิดและตอบ เท่านั้น !!!ตอบเป็นไทยเท่านั้น!!!",
        model="gpt-4o-mini"
    )

    # Create a thread
    thread = openai.Thread.create()

    # Add user message to the thread
    message = openai.Message.create(
        thread_id=thread.id,
        role="user",
        content=user_message
    )

    # Run the Assistant
    response = openai.Run.create(thread_id=thread.id, assistant_id=assistant.id)

    # Return assistant response
    return response['choices'][0]['message']['content']



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
