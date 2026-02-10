import streamlit as st
 
st.set_page_config(page_title="Chatbot UI", page_icon="🤖", layout="centered")
 
st.title("💬 Streamlit Chatbot")
 
# Store chat messages in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
 
# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
 
# Chat input box (always at bottom)
if prompt := st.chat_input("Type your message here..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
 
    # Bot reply
    reply = f"🤖 You said: {prompt}"
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)