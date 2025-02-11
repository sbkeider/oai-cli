#!/usr/bin/env python3
import os
import sys
import argparse
import openai
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
import json
import tiktoken

CONFIG_FILE = "config.json"

# Create a global Console instance.
console = Console()

def load_config():
    if not os.path.exists(CONFIG_FILE):
        console.print(f"Error: The config file {CONFIG_FILE} does not exist.", style="bold red")
        sys.exit(1)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)
    
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def change_model(model):
    config = load_config()
    config["model"] = model
    save_config(config)
    console.print(f"Model changed to {model}.", style="bold green")

def change_conversation(conversation):
    config = load_config()
    # add /conversations/ to the conversation if it's not already there
    if not conversation.startswith("./conversations/"):
        conversation = "./conversations/" + conversation
    # append .json to the conversation if it's not already there
    if not conversation.endswith(".json"):
        conversation += ".json"
    # if the conversation doesn't exist, create it
    if not os.path.exists(conversation):
        with open(conversation, "w") as f:
            json.dump([], f)
    config["conversation"] = conversation
    save_config(config)
    console.print(f"Conversation changed to {conversation}.", style="bold green")

def count_tokens(prompt, model):
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(prompt)
    return len(tokens)

def count_cumulative_tokens(conversation, model):
    encoding = tiktoken.encoding_for_model(model)
    with open(conversation, "r") as f:
        conversation_history = json.load(f)
    cumulative_tokens = 0
    for message in conversation_history:
        cumulative_tokens += count_tokens(message["content"], model)
    return cumulative_tokens

def main():
    # Use the API key from the environment.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("Error: The OPENAI_API_KEY environment variable is not set.", style="bold red")
        sys.exit(1)
    openai.api_key = api_key

    config = load_config()
    model = config["model"]
    encoding = tiktoken.encoding_for_model(model)
    conversation = config["conversation"]
    conversation_name = conversation.split("/")[-1].split(".")[0]
    # Parse command-line arguments; allow multi-word prompts.
    parser = argparse.ArgumentParser(
        description="Query OpenAI API with streaming markdown responses."
    )
    parser.add_argument("prompt", nargs="+", help="The prompt to send to the model")
    args = parser.parse_args()
    prompt_text = " ".join(args.prompt)
    if os.path.exists(conversation):
        with open(conversation, "r") as f:
            conversation_history = json.load(f)
    else:
        conversation_history = []

    conversation_history.append({"role": "user", "content": prompt_text})
    prompt_token_count = count_tokens(prompt_text, model)
    cumulative_tokens = count_cumulative_tokens(conversation, model)
    token_count = prompt_token_count + cumulative_tokens
    try:
        # Create a streaming chat completion.
        response = openai.chat.completions.create(
            model=model,  # Change this to your desired model name.
            messages=conversation_history,
            stream=True
        )

        # fr'[bold]\[{model}] Prompt:[/bold]' + 
        panel = Panel(f'>> {prompt_text} \n\n[bold]Token count:[/bold] {prompt_token_count} \n[bold]Total tokens in memory:[/bold] {token_count}', title=fr'\[{model}] \[{conversation_name}] prompt', padding=(1, 2), border_style="yellow")
        console.print(panel)

        # Accumulate the text as it streams in.
        accumulated_text = ""
        # Use Live to update a single markdown block in the terminal.
        with Live(Markdown(accumulated_text, code_theme="github-dark", inline_code_theme="github-dark"), console=console, refresh_per_second=10) as live:
            for chunk in response:
                # Directly access the content of the streamed chunk.
                try:
                    message = chunk.choices[0].delta.content
                except Exception:
                    message = ""
                if message:
                    accumulated_text += message
                    # Compute live token count for the accumulated response.
                    tokens_so_far = count_tokens(accumulated_text, model)
                    # Create a display text that includes the live token counter at the bottom.
                    response_token_count = f"\n**Response token count:** {tokens_so_far}"
                    total_tokens = f"\n\n**Total tokens in memory:** {tokens_so_far + token_count}"
                    display_text = accumulated_text + f"\n\n---" + response_token_count + total_tokens
                    # Update the live display with the new markdown content and token counter.
                    panel = Panel(Markdown(display_text, code_theme="github-dark", inline_code_theme="github-dark"),
                                  title=fr'\[{model}] \[{conversation_name}] response',
                                  padding=(2, 4), border_style="green")
                    live.update(panel)
        conversation_history.append({"role": "assistant", "content": accumulated_text})
    except Exception as e:
        panel = Panel(f"Error during API request: {e}", title="oai error", padding=(2, 4), border_style="red")
        console.print(panel)
        sys.exit(1)

    # Save the conversation history to a JSON file.
    with open(conversation, "w") as f:
        json.dump(conversation_history, f)

if __name__ == "__main__":
    main()

def clear_conversation():
    config = load_config()
    conversation = config["conversation"]
    if os.path.exists(conversation):
        os.remove(conversation)
        console.print("Conversation history cleared.", style="bold green")
    else:
        console.print("No conversation history to clear.", style="bold yellow")

def set_model():
    parser = argparse.ArgumentParser(description="Set the model to use.")
    parser.add_argument("model", help="The model to use.")
    args = parser.parse_args()
    change_model(args.model)

def set_conversation():
    parser = argparse.ArgumentParser(description="Set the conversation to use.")
    parser.add_argument("conversation", help="The conversation to use.")
    args = parser.parse_args()
    change_conversation(args.conversation)
