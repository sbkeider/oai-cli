#!/usr/bin/env python3
import os
import sys
import argparse
import openai
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel

# Create a global Console instance.
console = Console()

def main():
    # Use the API key from the environment.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("Error: The OPENAI_API_KEY environment variable is not set.", style="bold red")
        sys.exit(1)
    openai.api_key = api_key
    model = "o1-preview"
    # Parse command-line arguments; allow multi-word prompts.
    parser = argparse.ArgumentParser(
        description="Query OpenAI API with streaming markdown responses."
    )
    parser.add_argument("prompt", nargs="+", help="The prompt to send to the model")
    args = parser.parse_args()
    prompt_text = " ".join(args.prompt)

    try:
        # Create a streaming chat completion.
        response = openai.chat.completions.create(
            model="o1-preview",  # Change this to your desired model name.
            messages=[{"role": "user", "content": prompt_text}],
            stream=True
        )

        console.print("\n")
        console.print(f'[{model}] Prompt:', style="bold green", markup=False)
        console.print(">> ", prompt_text)
        console.print("\n")

        # Accumulate the text as it streams in.
        accumulated_text = ""
        # Use Live to update a single markdown block in the terminal.
        with Live(Markdown(accumulated_text, code_theme="github-dark"), console=console, refresh_per_second=6) as live:
            for chunk in response:
                # Directly access the content of the streamed chunk.
                try:
                    message = chunk.choices[0].delta.content
                except Exception:
                    message = ""
                if message:
                    accumulated_text += message
                    # Update the live display with the new markdown content.
                    panel = Panel(Markdown(accumulated_text, code_theme="github-dark"), title="oai response", padding=(2, 4), border_style="green")
                    live.update(panel)
    except Exception as e:
        panel = Panel(f"Error during API request: {e}", title="oai error", padding=(2, 4), border_style="red")
        console.print(panel)
        sys.exit(1)

if __name__ == "__main__":
    main()
