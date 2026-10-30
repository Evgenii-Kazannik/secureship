# Platforms and tools

## The shape this program runs

| Piece           | This program                                                      |
|-----------------|-------------------------------------------------------------------|
| Chat model      | One of the two runtimes below                                     |
| Embeddings      | A model from the same runtime, stored next to the document chunks |
| Tools           | Python functions that the code runs when the model asks           |
| Build assistant | Claude Code                                                       |
| Source control  | Git                                                               |

## Runtime A: Ollama

Open models served locally. Recommended chat model `qwen3:8b`, or `llama3.2:3b` on an 8 GB machine,
with weaker tool calls. Embeddings from a local model such as `nomic-embed-text`. Free, private, and it works offline. 
Slower on a small machine. From a Docker container it is reached at `http://host.docker.internal:11434`.

## Runtime B: EPAM DIAL

A hosted gateway to several models. Requires a key, the EPAM VPN, and staying within a specified USD allowance.

The API reference is the [DIAL Core API](https://dialx.ai/dial_api) (latest release). These are the operations:

| What                       | Operation                                                     | Reference                                                                                            |
|----------------------------|---------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| Send the key               | `Api-Key` header                                              | [Authorization](https://dialx.ai/dial_api#section/Authorization)                                     |
| Chat, including tool calls | `POST /openai/deployments/{deployment_name}/chat/completions` | [`sendChatCompletionRequest`](https://dialx.ai/dial_api#tag/LLM/operation/sendChatCompletionRequest) |
| Embeddings                 | `POST /openai/deployments/{deployment_name}/embeddings`       | [`createEmbedding`](https://dialx.ai/dial_api#tag/LLM/operation/createEmbedding)                     |
| Which deployments exist    | `GET /openai/deployments`                                     | [`getDeployments`](https://dialx.ai/dial_api#tag/Deployment-listing/operation/getDeployments)        |

`api-version` is a required query parameter on the deployment routes.
The reference example is `2023-12-01-preview`. The vector is `data[].embedding`, 
and its length is the dimension of the vector column. The server URL in the published spec is a placeholder. 
The host to call is `https://ai-proxy.lab.epam.com`, on the VPN. The [setup guide](../../setup.md) shows how to test it.

## What I run

- Primary runtime: **Runtime A — Ollama**
- Chat deployment or model: `qwen3:8b`
- Embedding deployment or model, and dimension: `nomic-embed-text`, 768 dimensions
- Why: local, free, and works offline — no cost risk

## Where else this shape is hosted

The same shape, a chat model, an embedding model, and the code holding the tools and the gate, 
can run on other platforms. This program does not use them. The table is for comparison.

| Platform         | What would stand in for the pieces above                                                                                              |
|------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| Azure AI Foundry | A Foundry model deployment for chat and embeddings, a project for tools and evaluation, the service still enforcing the shipment gate |
| AWS              | Bedrock, or an equivalent managed model API, for chat and embeddings, with the service owning the tools and the gate                  |
| Google Cloud AI  | Vertex AI model endpoints for chat and embeddings, with the service owning the tools and the gate                                     |

Moving the model to another host does not move the gate. The shipment lookup still reads the customer from the session, never from the model.

## Editors and assistants

| Tool           | Role in this program                         |
|----------------|----------------------------------------------|
| Claude Code    | Required build assistant                     |
| Git            | Required                                     |
| Cursor         | A named alternative editor. Not required.    |
| VS Code        | A named alternative editor. Not required.    |
| GitHub Copilot | A named alternative assistant. Not required. |

Use Claude Code for the build even if another assistant is installed.
The review rule is the same for any of them: read the diff before you keep it.