# agent.py
# ---------------------------
# Purpose:
#   - Create a LangGraph ReAct agent using OpenAI (ChatOpenAI).
#   - Connect multiple MCP servers (weather, fun, info, search) via stdio.
#   - Provide an interactive chat loop with memory retained across turns.
#   - Demonstrate tool use: weather forecast/alerts, quotes, jokes, activities, universities, country info, images, live web search.
# ---------------------------

import os  # for reading environment variables like OPENAI_API_KEY
import asyncio  # for running async event loop
from dotenv import load_dotenv  # to load .env file for API keys
from langchain_openai import ChatOpenAI  # OpenAI chat model wrapper for LangChain
from langchain_core.messages import HumanMessage  # structured message type for inputs
from langchain_mcp_adapters.client import MultiServerMCPClient  # MCP multi-server client
from langgraph.prebuilt import create_react_agent  # prebuilt ReAct agent for LangGraph
from langgraph.checkpoint.memory import MemorySaver  # simple in-memory checkpointer for persistence

# Load environment variables from .env so OPENAI_API_KEY is available
load_dotenv()

# Read the OpenAI API key from env; fail fast if not set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # get API key string
if not OPENAI_API_KEY:  # check if missing
    raise ValueError("Set OPENAI_API_KEY in .env")  # tell developer how to fix

# Instantiate the LLM; gpt-4o is strong and multimodal-aware, good for tool orchestration
llm = ChatOpenAI(model="gpt-4o")  # create the chat model instance

# Define a single thread_id to keep conversation memory across turns during this run
THREAD_ID = "demo-thread-001"  # any stable string works as a memory key

async def run_chat_loop(agent, client):
    """
    Purpose:
      - Provide an interactive CLI loop where the user can type messages.
      - Maintain memory (via LangGraph checkpointer) across turns.
      - Forward each user message to the agent; print the agent's final reply.
    """
    print("Type 'exit' to quit.")
    # Infinite loop until user types 'exit'
    while True:
        # Read a line of input from the terminal
        user_input = input("\nYou: ").strip()  # strip whitespace to simplify checks
        # If the user wants to exit, break the loop
        if user_input.lower() in {"exit", "quit"}:  # allow multiple exit keywords
            break  # leave the loop gracefully
        # Build the message list for the agent; using HumanMessage for clarity
        messages = [HumanMessage(content=user_input)]  # wrap input as a HumanMessage
        # Send the message to the agent using ainvoke (async invoke)
        # Provide configurable 'config' with a thread_id so memory is consistent
        resp = await agent.ainvoke({"messages": messages}, config={"configurable": {"thread_id": THREAD_ID}})
        # Extract the final LLM message content from LangGraph's response
        final = resp["messages"][-1].content  # get the last message content
        # Print the agent's response to console for the user to read
        print(f"\nAgent:\n{final}")  # render the output

async def main():
    """
    Purpose:
      - Start multiple MCP servers (weather, fun, info, search) via stdio.
      - Discover their tools via MCP protocol.
      - Build a LangGraph ReAct agent with those tools and a memory checkpointer.
      - Start an interactive chat loop.
    """
    # Initialize MCP client with multiple servers; each will be launched as a subprocess
    client = MultiServerMCPClient({
        "weather": {  # logical server name for weather tools
            "command": "python",  # run via Python interpreter
            "args": ["weather_server.py"],  # script that hosts the MCP server
            "transport": "stdio"  # communicate via stdin/stdout (recommended)
        },
        "fun": {  # logical server for quotes/jokes/activities
            "command": "python",
            "args": ["fun_server.py"],
            "transport": "stdio"
        },
        "info": {  # logical server for universities/country info/images
            "command": "python",
            "args": ["info_server.py"],
            "transport": "stdio"
        },
        "search": {  # logical server for live web search
            "command": "python",
            "args": ["search_server.py"],
            "transport": "stdio"
        }
    })

    # Ask the MCP client to introspect all connected servers and return their tool schemas
    tools = await client.get_tools()  # returns a list of ToolSpecifications for LangChain

    # Create a simple in-memory checkpointer so the agent retains conversation state across turns
    checkpointer = MemorySaver()  # ephemeral memory (per process) suitable for demos

    # Build a ReAct agent that can call any of the MCP tools as function calls
    agent = create_react_agent(
        llm,  # the OpenAI chat model
        tools,  # the MCP tools discovered above
        checkpointer=checkpointer  # memory handler for stateful conversations
    )

    # (Optional) Warm-up test: show it can call at least one tool (commented for clean demo)
    # test = await agent.ainvoke({"messages": [HumanMessage(content="Say hi without tools.")]},
    #                            config={"configurable": {"thread_id": THREAD_ID}})
    # print(test["messages"][-1].content)

    # Start the interactive chat loop so you can demo multi-tool conversations
    await run_chat_loop(agent, client)  # run the REPL

# Standard async entrypoint guard
if __name__ == "__main__":  # ensure this block runs only when script executed directly
    asyncio.run(main())  # start the asyncio event loop and run main()
