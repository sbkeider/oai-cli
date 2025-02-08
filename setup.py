from setuptools import setup

setup(
    name="oai-cli",
    version="0.1",
    py_modules=["oai"],
    install_requires=[
        "openai",
    ],
    entry_points={
        "console_scripts": [
            "oai = oai:main",
            "oai-clear = oai:clear_conversation",
        ],
    },
)
