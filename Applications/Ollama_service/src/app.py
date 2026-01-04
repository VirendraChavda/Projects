import streamlit as st
import subprocess
import requests
import json
import time

# Model categories and options
categories = {
    "Reasoning models": ["deepseek-r1:8b", "deepseek-r1:7b", "deepseek-r1:1.5b", "phi4-mini:3.8b"],
    "Chat models": ["llama3.1:8b", "llama3.2:3b", "llama3.2:1b", "mistral:7b", "qwen3:4b", "qwen3:1.7b", "qwen3:0.6b", "smollm2:1.7b"],
    "Big embedding model": ["bge-m3"],
    "Small embedding model": ["nomic-embed-text", "all-minilm", "snowflake-arctic-embed:22m"]
}

def check_model_available(model_name):
    """Check if the model is available locally."""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        return model_name in result.stdout
    except subprocess.CalledProcessError:
        st.error("Failed to check model list. Ensure Ollama is installed and running.")
        return False

def pull_model(model_name):
    """Pull the model using Ollama."""
    try:
        subprocess.run(["ollama", "pull", model_name], check=True)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Failed to pull model {model_name}: {e}")
        return False

def stop_model(model_name):
    """Stop the model to free VRAM."""
    try:
        subprocess.run(["ollama", "stop", model_name], check=True)
    except subprocess.CalledProcessError:
        pass  # Model might not be running or already stopped

def test_chat_model(model_name, prompt):
    """Test a chat/reasoning model."""
    url = "http://localhost:11434/api/generate"
    data = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    start_time = time.time()
    try:
        response = requests.post(url, json=data, timeout=200)
        response.raise_for_status()
        result = response.json()
        end_time = time.time()
        response_text = result.get("response", "No response")
        return response_text, end_time - start_time
    except requests.RequestException as e:
        end_time = time.time()
        return f"Error: {e}", end_time - start_time

def test_embedding_model(model_name, text):
    """Test an embedding model."""
    url = "http://localhost:11434/api/embeddings"
    data = {
        "model": model_name,
        "prompt": text
    }
    start_time = time.time()
    try:
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        end_time = time.time()
        embedding = result.get("embedding", [])
        if embedding:
            response_text = f"Embedding generated (length: {len(embedding)}). First 10 values: {embedding[:10]}"
        else:
            response_text = "No embedding generated"
        return response_text, end_time - start_time
    except requests.RequestException as e:
        end_time = time.time()
        return f"Error: {e}", end_time - start_time

# Streamlit app
st.title("Ollama Model Tester")

st.write("Select a model category and then a specific model to test. Ensure Ollama is running (`ollama serve`).")

# Category selection
category = st.selectbox("Select Model Category", list(categories.keys()))

if category:
    # Model selection
    model = st.selectbox("Select Model", categories[category])

    if model:
        # Check availability
        available = check_model_available(model)

        if not available:
            st.warning(f"Model '{model}' is not available locally.")
            if st.button("Download Model"):
                with st.spinner("Downloading model... This may take a while."):
                    success = pull_model(model)
                if success:
                    st.success("Model downloaded successfully!")
                    st.rerun()  # Force rerun to update availability check
                else:
                    st.error("Download failed.")

        if available:
            st.success(f"Model '{model}' is ready for testing.")

            # Text input
            text_input = st.text_area("Enter text to test the model", height=100)

            # Test button
            if st.button("Test Model"):
                if not text_input.strip():
                    st.error("Please enter some text to test.")
                else:
                    with st.spinner("Model running..."):
                        if category in ["Reasoning models", "Chat models"]:
                            result, elapsed_time = test_chat_model(model, text_input)
                        else:
                            result, elapsed_time = test_embedding_model(model, text_input)
                    st.write("**Result:**")
                    st.write(result)
                    st.write(f"**Time taken:** {elapsed_time:.2f} seconds")
                    # Unload the model to free VRAM
                    stop_model(model)
                    st.info("Model unloaded to free VRAM.")