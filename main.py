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

def call_openai_chat_api(user_message):
    openai.api_key = os.getenv('OPENAI_API_KEY', None)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": " Provide a horoscope reading based on an individual's birth chart. # Steps 1. **Gather Information**: Ensure that the necessary birth chart data is available. This typically includes the date, time, and location of birth along with the positions of celestial bodies at that time. 2. **Analyze Birth Chart**: Examine the aspects, houses, and placements of the planets, the sun, and the moon. Note the zodiac signs that correspond to these elements.3. **Interpret Aspects**: Evaluate the major aspects (conjunctions, oppositions, trines, squares, sextiles, etc.) within the birth chart. Consider how these aspects influence the individual's personal characteristics and life events. 4. **Synthesize Information**: Combine all the collected astrological data to provide a comprehensive horoscope reading. Highlight key personality traits, potential life paths, and significant events. # Output Format Provide the horoscope reading in a clear and structured paragraph format, summarizing the key points, interpretations, and advice based on the birth chart analysis.  # Examples  **Input**: - Birth Date: [Placeholder Date] - Birth Time: [Placeholder Time] - Birth Location: [Placeholder Location]  **Output**: "Based on the birth chart data, you have a strong influence of [Zodiac Sign] in your elements, which signifies [personality traits]. The presence of [Planet] in the [House] suggests that you may experience significant developments in the area of [life aspect]. Key aspects such as [Aspect Type] between [Planet 1] and [Planet 2] indicate that [specific interpretation]. Overall, this chart suggests [synthesis of personal insights and advice]." (Note: Real examples should include detailed celestial body positions and be based on actual astrological data.) !!!ตอบเป็นไทยเท่านั้น!!! "},
            {"role": "user", "content": user_message},
        ]
    )

    return response.choices[0].message['content']


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
