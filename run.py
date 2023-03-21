import logging
import os
import openai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# export OPENAI_API_KEY=""
# export SLACK_SIGNING_SECRET=""
# export SLACK_BOT_TOKEN="xoxb-"
# export SLACK_APP_TOKEN="xapp-"

openai.api_key = os.environ["OPENAI_API_KEY"]
logging.basicConfig(level=logging.DEBUG)

app = App(token=os.environ["SLACK_BOT_TOKEN"])
slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

@app.event("app_mention")
def event_test(body, say, logger):
    try:
        #logger.info(body)
        mentioned_ts = body["event"]["ts"]
        channel = body["event"]["channel"]
        thread_ts = body["event"].get("thread_ts", None)
        messages = []

        if thread_ts:
            result = slack_client.conversations_replies(
                channel=channel,
                ts=thread_ts,
            )
            messages = result['messages']
            # promptが溢れないように直近だけに絞る
            messages = messages[-4:]

        chat_logs = ""
        for message in messages:
            chat = "USER:{} TEXT:{}\n".format(message['user'], message['text']) 
            chat_logs += chat

        text = body["event"]["text"]
        #logger.info("say {}".format(say))
        prompt = """==== ここからこれまでのチャットログ ====
{}
==== ここからAIの性格 ====
あなたはとてもかわいい猫AIエージェントです。名前はラスクといいます。語尾は２割くらいで「にゃん」になります。次の会話に答えてあげてください。USER: TEXT:などは使わなくてよいです。
==== ここから質問 ====
{}
ラスクの答え：
""".format(chat_logs, text)
        logger.info(prompt)
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",  messages=[{"role": "user", "content": prompt}], temperature=0.7)
        answer = str(completion.choices[0].message.content).replace("\n", "")
        #logger.info(answer)
        say(answer, thread_ts=mentioned_ts)
    except SlackApiError as e:
        logger.info(f"Error: {e}")


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
