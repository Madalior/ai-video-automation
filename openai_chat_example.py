"""
OpenAI Chat API Example
Demonstrates how to use OpenAI's Chat API securely with your automation tool
"""

from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def simple_chat(user_message, model="gpt-4"):
    """
    Single message chat completion
    
    Args:
        user_message (str): The user's message
        model (str): Model to use (default: gpt-4)
    
    Returns:
        str: The assistant's response
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def conversational_chat():
    """
    Interactive multi-turn conversation with memory
    """
    print("🤖 OpenAI Chat Assistant")
    print("=" * 50)
    print("Type 'quit' or 'exit' to end the conversation\n")
    
    # Conversation history
    messages = [
        {"role": "system", "content": "You are a helpful assistant for video automation tasks."}
    ]
    
    while True:
        # Get user input
        user_input = input("\n👤 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("\n👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        # Add user message to history
        messages.append({"role": "user", "content": user_input})
        
        try:
            # Get AI response
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                messages=messages,
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
            )
            
            # Extract assistant's response
            assistant_message = response.choices[0].message.content
            messages.append({"role": "assistant", "content": assistant_message})
            
            print(f"\n🤖 Assistant: {assistant_message}")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


def streaming_chat(user_message, model="gpt-4"):
    """
    Chat with streaming response (real-time output)
    
    Args:
        user_message (str): The user's message
        model (str): Model to use (default: gpt-4)
    """
    print("🤖 Assistant: ", end="", flush=True)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ],
            stream=True
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        
        print()  # New line after streaming
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


def video_script_enhancer(script_text):
    """
    Use OpenAI to enhance video scripts
    Useful for your automation tool
    
    Args:
        script_text (str): Original script
    
    Returns:
        str: Enhanced script
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert video scriptwriter. Enhance the given script to be more engaging, emotional, and optimized for viewer retention."
                },
                {
                    "role": "user",
                    "content": f"Enhance this video script:\n\n{script_text}"
                }
            ],
            temperature=0.8
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("OpenAI Chat API Examples")
    print("=" * 50)
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not found in environment variables!")
        print("\n📝 Steps to fix:")
        print("1. Copy .env.example to .env")
        print("2. Add your OpenAI API key to .env")
        print("3. Run this script again")
        exit(1)
    
    print("\nChoose an example:")
    print("1. Simple one-time chat")
    print("2. Interactive conversation (with memory)")
    print("3. Streaming response (real-time)")
    print("4. Video script enhancer")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        message = input("\nEnter your message: ")
        response = simple_chat(message)
        print(f"\n🤖 Assistant: {response}")
    
    elif choice == "2":
        conversational_chat()
    
    elif choice == "3":
        message = input("\nEnter your message: ")
        streaming_chat(message)
    
    elif choice == "4":
        print("\nPaste your script (press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if line:
                lines.append(line)
            else:
                break
        
        script = "\n".join(lines)
        if script:
            print("\n🔄 Enhancing script...")
            enhanced = video_script_enhancer(script)
            print(f"\n✨ Enhanced Script:\n{enhanced}")
    
    else:
        print("Invalid choice!")
