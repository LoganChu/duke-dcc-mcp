import gradio as gr
import requests
from openai import OpenAI
from dotenv import load_dotenv
import os;

load_dotenv()  

# Example function to call your MCP server
def query_mcp(user_message):
    # Replace with your MCP server endpoint & payload format
    url = "http://localhost:8000/chat"
    payload = {"message": user_message}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json().get("reply", "⚠️ No reply field found")
    else:
        return f"⚠️ Error {response.status_code}: {response.text}"

# Chat handler for Gradio
def chat_fn(message, history):
    token = os.getenv("LITELLM_KEY")
    client = OpenAI(
        api_key=token,
        base_url="https://litellm.oit.duke.edu/v1",
    )

    response = client.responses.create(
        model="GPT 4.1",
        instructions="You are a helpful assistent here to demo the power of AI",
        input=message,
    )

    return response.output[0].content[0].text

# Build the Gradio Chat UI
demo = gr.ChatInterface(
    fn=chat_fn,
    title="My MCP Chat",
    description="Chat with my custom LLM through MCP server",
    theme="soft",  # you can try "default" or "glass" too
    type = 'messages'
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
