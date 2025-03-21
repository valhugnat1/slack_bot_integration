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

    print (body['event']['channel'], body['event']['ts'])

    # Add thinking reaction
    app.client.reactions_add(
        channel=body['event']['channel'],
        timestamp=body['event']['ts'],
        name="thought_balloon"
    )

    message_text = extract_message_text(body)
    
    # Check if the message is in a thread
    if 'thread_ts' in body['event']:
        # Get previous messages from thread
        thread_messages = get_thread_messages(body['event']['channel'], body['event']['thread_ts'])
        message_text = f"Previous messages: \n{thread_messages}\nUser message: {message_text}"

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
    res_clean = "".join(res_clean_list)

    # Remove thinking reaction
    app.client.reactions_remove(
        channel=body['event']['channel'],
        timestamp=body['event']['ts'],
        name="thought_balloon"
    )

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

def get_thread_messages(channel_id, thread_ts):
    """
    Retrieve all messages from a thread except the last one (which is the mention)
    """
    try:
        result = app.client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )
        
        # Get all messages except the last one (which contains the mention)
        messages = result["messages"][:-1]
        
        # Format messages
        formatted_messages = []
        for msg in messages:
            user_info = app.client.users_info(user=msg.get("user", "unknown"))
            username = user_info["user"]["real_name"] if "user" in user_info else "Unknown User"
            formatted_messages.append(f"{username}: {msg.get('text', '')}")
            
        return "\n".join(formatted_messages)
    except Exception as e:
        print(f"Error fetching thread messages: {e}")
        return ""

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()