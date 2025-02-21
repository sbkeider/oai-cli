### oai-cli

A straight forward command line interface for the OpenAI API.

#### Installation

Make sure you set your OpenAI API key in your environment variables:

```bash
export OPENAI_API_KEY=<your_openai_api_key>
```
or, add it to your `.zshrc` or `.bashrc` file:

```bash
echo "export OPENAI_API_KEY=<your_openai_api_key>" >> ~/.zshrc
```

In your virtual environment, install the package:

```bash
pip install -e .
```

#### Set Conversation

```bash
oai-set-chat ca_gold_rush
```

#### Set Model

```bash
oai-set-model o1-mini
```

#### Usage

```bash
oai "list five little known facts about the California gold rush. Be concise but cite your sources."
```

#### Clear Memory / Conversation History (Current Conversation)

```bash
oai-clear
```

#### See Current Conversation File

```bash
oai-which
```

#### See Conversation Chat History

```bash
oai-history
```


#### Clear All Conversations

```bash
oai-clear-all
```

#### Copy Last Assistant Response to Clipboard

```bash
oai-cl
```

#### Add file context

```bash
oai-add <file_path>
```

#### Remove file context

```bash
oai-rm <file_path>
```

#### Clear All File Context

```bash
oai-clear-context
```





