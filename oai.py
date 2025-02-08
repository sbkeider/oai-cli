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

# Create a global Console instance.
console = Console()

def main():
    # Use the API key from the environment.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("Error: The OPENAI_API_KEY environment variable is not set.", style="bold red")
        sys.exit(1)
    openai.api_key = api_key

    model = "o1-mini"
    
    # Parse command-line arguments; allow multi-word prompts.
    parser = argparse.ArgumentParser(
        description="Query OpenAI API with streaming markdown responses."
    )
    parser.add_argument("prompt", nargs="+", help="The prompt to send to the model")
    args = parser.parse_args()
    prompt_text = " ".join(args.prompt)
    if os.path.exists("conversation_history.json"):
        with open("conversation_history.json", "r") as f:
            conversation_history = json.load(f)
    else:
        conversation_history = []

    conversation_history.append({"role": "user", "content": prompt_text})

    try:
        # Create a streaming chat completion.
        response = openai.chat.completions.create(
            model=model,  # Change this to your desired model name.
            messages=conversation_history,
            stream=True
        )

        # fr'[bold]\[{model}] Prompt:[/bold]' + 
        panel = Panel(f'>> {prompt_text}', title=fr'\[{model}] prompt', padding=(1, 2), border_style="yellow")
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
                    # Update the live display with the new markdown content.
                    panel = Panel(Markdown(accumulated_text, code_theme="github-dark", inline_code_theme="github-dark"), title=fr'\[{model}] response', padding=(2, 4), border_style="green")
                    live.update(panel)
        conversation_history.append({"role": "assistant", "content": accumulated_text})
    except Exception as e:
        panel = Panel(f"Error during API request: {e}", title="oai error", padding=(2, 4), border_style="red")
        console.print(panel)
        sys.exit(1)

    # Save the conversation history to a JSON file.
    with open("conversation_history.json", "w") as f:
        json.dump(conversation_history, f)

if __name__ == "__main__":
    main()

def clear_conversation():
    if os.path.exists("conversation_history.json"):
        os.remove("conversation_history.json")
        console.print("Conversation history cleared.", style="bold green")
    else:
        console.print("No conversation history to clear.", style="bold yellow")
