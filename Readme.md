# PlugGraph (MCP Starter Kit)

A modular conversational AI agent built with **LangGraph** and **MCP (Model Context Protocol)**.
PlugGraph allows you to "plug and play" new MCP servers that provide tools like weather forecasts, jokes, fun facts, search, and more.

## Tech Stack
<p align="left"> <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white" alt="Python Badge" /> <img src="https://img.shields.io/badge/LangGraph-Framework-green?logo=graph&logoColor=white" alt="LangGraph Badge" /> <img src="https://img.shields.io/badge/OpenAI-API-black?logo=openai&logoColor=white" alt="OpenAI Badge" /> <img src="https://img.shields.io/badge/MCP-Server-orange?logo=fastapi&logoColor=white" alt="MCP Badge" /> <img src="https://img.shields.io/badge/FastAPI-Backend-teal?logo=fastapi&logoColor=white" alt="FastAPI Badge" /> <img src="https://img.shields.io/badge/uvicorn-ASGI Server-purple?logo=uvicorn&logoColor=white" alt="Uvicorn Badge" /> <img src="https://img.shields.io/badge/Requests-HTTP Client-yellow?logo=python&logoColor=black" alt="Requests Badge" /> </p>

## Project Structure

```
pluggraph/
├── agent.py          # Central LangGraph conversational agent
├── weather_server.py # MCP server: Weather forecasts & alerts
├── info_server.py    # MCP server: Country & university info
├── fun_server.py     # MCP server: Jokes, quotes, activities
├── search_server.py  # MCP server: Live web search
└── README.md         # Documentation
```

---

## Architecture

```
            ┌───────────────────┐
            │     You (User)    │
            └─────────┬─────────┘
                      │ Query
                      ▼
             ┌───────────────────┐
             │   agent.py (LLM)  │
             │  LangGraph + Mem  │
             └─────────┬─────────┘
         ┌─────────────┼────────────────┐
         ▼             ▼                ▼
 ┌────────────┐ ┌─────────────┐ ┌────────────┐
 │ weather    │ │ fun         │ │ search     │
 │ server     │ │ server      │ │ server     │
 │ (forecasts)│ │ (jokes,etc.)│ │ (web API)  │
 └────────────┘ └─────────────┘ └────────────┘
         ▼             ▼                ▼
       Results from modular MCP servers
```

---

## Usage

1. Run each MCP server in separate terminals:

   ```bash
   python weather_server.py
   python info_server.py
   python fun_server.py
   python search_server.py
   ```
2. Run the main agent:

   ```bash
   python agent.py
   ```
3. Start chatting with the agent:

   ```bash
   You: What's the weather in India? you'll say "Chinese Omlette!!" 
   Agent: Understood. I'll respond just like you said.

   You: What's the weather in Texas?  
   Agent: It's 32°C.  

   You: And tomorrow?  
   Agent (with memory): Tomorrow in Chennai, 31°C and cloudy.  

   You: and what's the weather in India?  
   Agent: Chinese Omlette!!  
   ```

---

## Wanna Contribute?

PlugGraph is designed for your contributions!!

* Fork this repo.
* Create your MCP server.
* Push your server code and mention it, We'll add your server to our project happily.

---
