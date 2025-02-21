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
import re
import pyperclip  # Cross-platform clipboard library


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
        # if /conversations/ doesn't exist, create it
        if not os.path.exists("./conversations"):
            os.makedirs("./conversations")
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

def extract_code_blocks(message):
    # find all code blocks in the message
    code_block_pattern = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
    code_blocks = code_block_pattern.findall(message)

    numbered_blocks = []
    for idx, (lang, code) in enumerate(code_blocks, start=1):
        numbered_blocks.append({
            'language': lang if lang else 'plaintext',
            'code': code.strip(),
            'number': idx,
        })
    return numbered_blocks

def copy_block_to_clipboard():
    parser = argparse.ArgumentParser(description="Set the number of the block to copy to clipboard.")
    parser.add_argument("block_number", help="Set the block number to copy to clipboard.")
    args = parser.parse_args()
    block_number = int(args.block_number)
    config = load_config()
    conversation = config["conversation"]
    with open(conversation, "r") as f:
        conversation_history = json.load(f)
    entry = conversation_history[-1]
    message = entry["content"]
    blocks = extract_code_blocks(message)
    if block_number > len(blocks):
        console.print(f"Block number {block_number} is out of range.", style="bold red")
        return
    block = blocks[block_number - 1]
    pyperclip.copy(block["code"])
    console.print(f"Copied {block['language']} block {block['number']} to clipboard.", style="bold green")
    # print the block in a panel
    panel = Panel(block["code"], title=fr'\[{block["language"]}] block copied', padding=(2, 4), border_style="green")
    console.print(panel)

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
    # if conversation doesn't exist, create it
    if not os.path.exists(conversation):
        with open(conversation, "w") as f:
            json.dump([], f)
            
    conversation_name = conversation.split("/")[-1].split(".")[0]
    # Parse command-line arguments; allow multi-word prompts.
    parser = argparse.ArgumentParser(
        description="Query OpenAI API with streaming markdown responses."
    )
    parser.add_argument("prompt", nargs="+", help="The prompt to send to the model")
    args = parser.parse_args()
    prompt_text = " ".join(args.prompt)

    # -- NEW CODE TO INCLUDE FILE CONTEXT --
    context_files = config.get("context", [])
    context_text = ""
    prompt_display_context = []
    for file_path in context_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    file_content = f.read()
                    context_text += f"\n\n[Context from {file_path}]\n{file_content}"
                    prompt_display_context.append(fr"\[including context from {file_path}]")
            except Exception as e:
                console.print(f"Failed to read context file {file_path}: {e}", style="bold red")
        else:
            console.print(f"Context file {file_path} does not exist. Skipping...", style="bold yellow")
    if context_text:
        display_text = prompt_text + "\n\n" + "\n".join(prompt_display_context)
        prompt_text = context_text + "\n\n" + prompt_text
    else:
        display_text = prompt_text
        
    # -- END NEW CODE --

    if os.path.exists(conversation):
        with open(conversation, "r") as f:
            conversation_history = json.load(f)
    else:
        conversation_history = []
        # create file if it doesn't exist
        with open(conversation, "w") as f:
            json.dump([], f)

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
        panel = Panel(f'>> {display_text} \n\n[bold]Token count:[/bold] {prompt_token_count} \n[bold]Total tokens in memory:[/bold] {token_count}', 
                      title=fr'\[{model}] \[{conversation_name}] prompt', padding=(1, 2), border_style="yellow")
        console.print(panel)

        # Accumulate the text as it streams in.
        accumulated_text = ""
        with Live(Markdown(accumulated_text, code_theme="github-dark", inline_code_theme="github-dark"), console=console, refresh_per_second=10) as live:
            for chunk in response:
                try:
                    message = chunk.choices[0].delta.content
                except Exception:
                    message = ""
                if message:
                    accumulated_text += message
                    tokens_so_far = count_tokens(accumulated_text, model)
                    response_token_count = f"\n**Response token count:** {tokens_so_far} \n"
                    total_tokens = f"\n**Total tokens in memory:** {tokens_so_far + token_count}"
                    display_text = accumulated_text + f"\n\n---" + response_token_count + total_tokens
                    panel = Panel(Markdown(display_text, code_theme="github-dark", inline_code_theme="github-dark"),
                                  title=fr'\[{model}] \[{conversation_name}] response',
                                  padding=(2, 4), border_style="green")
                    live.update(panel)
        conversation_history.append({"role": "assistant", "content": accumulated_text})
    except Exception as e:
        panel = Panel(f"Error during API request: {e}", title="oai error", padding=(2, 4), border_style="red")
        console.print(panel)
        sys.exit(1)

    with open(conversation, "w") as f:
        json.dump(conversation_history, f)

# Add files to the context array.
def add_context():
    parser = argparse.ArgumentParser(description="Add one or more files to the context array.")
    parser.add_argument("files", nargs="+", help="File paths to add to context.")
    args = parser.parse_args()

    config = load_config()
    context_files = config.get("context", [])
    for file_path in args.files:
        if file_path in context_files:
            console.print(f"File {file_path} is already in context.", style="bold yellow")
        else:
            context_files.append(file_path)
            console.print(f"Added {file_path} to context.", style="bold green")
    config["context"] = context_files
    save_config(config)

# Remove a file from the context array.
def rm_context():
    parser = argparse.ArgumentParser(description="Remove a file from the context array.")
    parser.add_argument("file", help="File path to remove from context.")
    args = parser.parse_args()

    config = load_config()
    context_files = config.get("context", [])
    if args.file not in context_files:
        console.print(f"File {args.file} is not in context.", style="bold yellow")
    else:
        context_files.remove(args.file)
        config["context"] = context_files
        save_config(config)
        console.print(f"Removed {args.file} from context.", style="bold green")

# Clear the entire context array.
def clear_context():
    config = load_config()
    config["context"] = []
    save_config(config)
    console.print("Cleared context. Context array reset.", style="bold green")
    
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

# print conversation history in panels like main function
def print_conversation_history():
    config = load_config()
    conversation = config["conversation"]
    if os.path.exists(conversation):
        with open(conversation, "r") as f:
            conversation_history = json.load(f)
    else:
        conversation_history = []
    for message in conversation_history:
        if message["role"] == "user":
            panel = Panel(f'>> {message["content"]}', title=fr'\[{message["role"]}]', padding=(1, 2), border_style="yellow")
        else:
            panel = Panel(Markdown(message["content"], code_theme="github-dark", inline_code_theme="github-dark"), 
                         title=fr'\[{message["role"]}]', padding=(2, 4), border_style="green")
        console.print(panel)

def copy_last_response():
    config = load_config()
    conversation = config["conversation"]
    if os.path.exists(conversation):
        with open(conversation, "r") as f:
            conversation_history = json.load(f)
        # Iterate from the end to find the last assistant message
        for message in reversed(conversation_history):
            if message["role"] == "assistant":
                pyperclip.copy(message["content"])
                console.print("Last assistant response copied to clipboard.", style="bold green")
                return
        console.print("No assistant response found in the conversation.", style="bold yellow")
    else:
        console.print("Conversation file does not exist.", style="bold red")

def clear_all_chats():
    config = load_config()
    config["conversation"] = "./conversations/default.json"
    save_config(config)
    # remove all files in ./conversations/
    for file in os.listdir("./conversations/"):
        os.remove(os.path.join("./conversations/", file))
    console.print("All chats cleared.", style="bold green")

def which_chat():
    config = load_config()
    conversation = config["conversation"]
    if os.path.exists(conversation):
        console.print(f"Currently using chat: {conversation}", style="bold green")
    else:
        console.print("No chat selected.", style="bold yellow")