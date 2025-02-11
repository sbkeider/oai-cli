from setuptools import setup

setup(
    name="oai-cli",
    version="0.1",
    py_modules=["oai"],
    install_requires=[
        "openai",
        "rich",
        "tiktoken",
    ],
    entry_points={
        "console_scripts": [
            "oai = oai:main",
            "oai-clear = oai:clear_conversation",
            "oai-set-model = oai:set_model",
            "oai-set-chat = oai:set_conversation",
        ],
    },
)
