from setuptools import setup

setup(
    name="oai-cli",
    version="0.1",
    py_modules=["oai"],
    install_requires=[
        "openai",
        "rich",
        "tiktoken",
        "pyperclip",
    ],
    entry_points={
        "console_scripts": [
            "oai = oai:main",
            "oai-clear = oai:clear_conversation",
            "oai-set-model = oai:set_model",
            "oai-set-chat = oai:set_conversation",
            "oai-history = oai:print_conversation_history",
            "oai-c = oai:copy_block_to_clipboard",
            "oai-add = oai:add_context",
            "oai-rm = oai:rm_context",
            "oai-clear-context = oai:clear_context",
            "oai-cl = oai:copy_last_response",
            "oai-clear-all = oai:clear_all_chats",
            "oai-which = oai:which_chat",
        ],
    },
)
