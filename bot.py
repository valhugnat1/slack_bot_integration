import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()  # Charge les variables d'environnement depuis un fichier .env


SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")


client = OpenAI(base_url="http://localhost:8081", api_key="fake")
app = App(token=SLACK_BOT_TOKEN)


# Listen for app_mention events
@app.event("app_mention")
def handle_app_mention_events(body, say, logger):
    """
    Event handler for when the bot is mentioned in a channel
    Responds with "Hello world" to any mention
    """
    logger.info(body)

    message_text = extract_message_text(body)

    print (message_text)


    completion = client.chat.completions.create(
        model="Jean-Cloud",
        messages=[
            {
                "role": "user",
                "content": message_text
            }
        ]
    )

    res_clean_list = completion.choices[0].message.content.split("\n\n **Model:**")[:-1]

    print (res_clean_list)
    res_clean = "".join(res_clean_list)
    print (res_clean)

    say(text=res_clean, thread_ts=body['event']['ts'])

def extract_message_text(slack_payload):
    # Access the text content from the event
    full_text = slack_payload['event']['text']
    
    # Replace any user mention patterns like <@USER_ID> with empty string
    import re
    clean_text = re.sub(r'<@[A-Z0-9]+>', '', full_text)
    
    # Remove any extra whitespace that might have been created
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    return clean_text.strip()


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()