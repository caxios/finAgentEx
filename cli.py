from main import agent
from langchain.messages import HumanMessage
import uuid

def main():
    print("Welcome to the Stock Analysis CLI!")
    print("Type 'quit' or 'exit' to stop.")
    
    # Create a unique thread ID for this session
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        user_input = input("\nEnter a ticker or question: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("Goodbye!")
            break
            
        if not user_input:
            continue
            
        try:
            # Stream the response
            print("\nAgent: ", end="", flush=True)
            for chunk in agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
                stream_mode="values"
            ):
                # The stream mode "values" returns the full state at each step.
                # We want to print the last message content if it's from the AI.
                pass
            
            # Since stream_mode="values" yields the full state, getting the final response 
            # might be cleaner by just invoking or inspecting the last message after the stream loop.
            # However, to stream token by token visually, "messages" stream mode is often better,
            # but usually requires a different handling than just printing "values".
            
            # Let's try invoke first for simplicity in the CLI to ensure we get a clean result,
            # OR better, use the stream properly for a chat-like experience.
            # Reworking loop for stream_mode='messages' to be closer to main.py implementation.
            
            pass 
        except Exception as e:
            print(f"Error: {e}")

# Redefining to be cleaner and actually work
import asyncio

async def run_chat():
    print("Welcome to the Stock Analysis CLI!") 
    print("Type 'quit' or 'exit' to stop.")
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["quit", "exit"]:
            break
        
        print("Agent: ", end="", flush=True)
        try:
            # Using simple stream to debug
            for output in agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
            ):
                # output contains the state update from the last node
                for key, value in output.items():
                    print(f"\n[{key}]: {value}")
            print() # Newline at end
        except Exception as e:
            print(f"\nError encountered: {e}")

if __name__ == "__main__":
    asyncio.run(run_chat())
