# PlugGraph (MCP Starter Kit)

A modular conversational AI agent built with **LangGraph** and **MCP (Model Context Protocol)**.
PlugGraph allows you to "plug and play" new MCP servers that provide tools like weather forecasts, jokes, fun facts, search, and more.

## Tech Stack

* **LangGraph** → agent orchestration and memory
* **OpenAI API** → natural language understanding and generation
* **MCP Servers** → modular tools exposing APIs as agents (weather, jokes, search, etc.)
* **Python** → core runtime

---

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

## Why PlugGraph?

PlugGraph is designed to give you a **MCP Starter Kit**:

* You can easily add new MCP servers (finance, news, custom APIs).
* The LangGraph agent automatically learns how to use them.
* Demonstrates **memory + tool-usage reasoning**.

---