import streamlit as st
import requests
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"


def get_token():
    if "token" not in st.session_state:
        st.session_state.token = None
    return st.session_state.token


def set_token(token):
    st.session_state.token = token


def headers():
    token = get_token()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def login(email: str, password: str):
    resp = requests.post(f"{API_BASE}/auth/login", data={"username": email, "password": password})
    if resp.status_code == 200:
        data = resp.json()
        set_token(data["access_token"])
        return True
    return False


def logout():
    set_token(None)


def api_get(path):
    resp = requests.get(f"{API_BASE}{path}", headers=headers())
    return resp


def api_post(path, data=None):
    resp = requests.post(f"{API_BASE}{path}", headers=headers(), json=data)
    return resp


def render_login():
    st.title("IA Agent Platform - Connexion")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")
        if submitted:
            if login(email, password):
                st.success("Connecté")
                st.rerun()
            else:
                st.error("Identifiants invalides")


def render_sidebar():
    st.sidebar.title("Agents")
    resp = api_get("/agents")
    if resp.status_code == 200:
        agents = resp.json()
        agent_names = [a["name"] for a in agents]
        selected = st.sidebar.selectbox("Choisir un agent", agent_names)
        st.session_state.selected_agent = selected
        agent = next((a for a in agents if a["name"] == selected), None)
        if agent:
            st.sidebar.markdown(f"**Description:** {agent['description']}")
            st.sidebar.markdown(f"**Modèle:** {agent['model']}")
    else:
        st.sidebar.error("Impossible de charger les agents")


def render_chat():
    st.title("Chat")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources"):
                    for source in msg["sources"]:
                        st.write(source)
    user_input = st.chat_input("Votre message")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        with st.chat_message("assistant"):
            with st.spinner("Réflexion..."):
                payload = {"message": user_input, "agent_name": st.session_state.get("selected_agent", ""), "conversation_id": st.session_state.get("conversation_id")}
                resp = api_post("/chat", payload)
                if resp.status_code == 200:
                    data = resp.json()
                    st.write(data["content"])
                    if data.get("sources"):
                        with st.expander("Sources"):
                            for source in data["sources"]:
                                st.write(source)
                    st.session_state.messages.append({"role": "assistant", "content": data["content"], "sources": data.get("sources", [])})
                    st.session_state.conversation_id = data["conversation_id"]
                else:
                    st.error(f"Erreur: {resp.text}")


def render_documents():
    st.title("Documents")
    with st.form("upload"):
        uploaded_file = st.file_uploader("Choisir un fichier", type=["pdf", "docx", "txt", "md"])
        collection_name = st.text_input("Collection", value="default")
        chunk_size = st.number_input("Taille de chunk", value=1000)
        chunk_overlap = st.number_input("Chevauchement", value=200)
        submitted = st.form_submit_button("Ingérer")
        if submitted and uploaded_file:
            files = {"file": (uploaded_file.name, uploaded_file.getbuffer())}
            resp = requests.post(f"{API_BASE}/documents/upload", headers=headers(), files=files, data={"collection_name": collection_name, "chunk_size": str(chunk_size), "chunk_overlap": str(chunk_overlap)})
            if resp.status_code in (200, 201):
                st.success("Document ingéré")
            else:
                st.error(f"Erreur: {resp.text}")
    resp = api_get("/documents")
    if resp.status_code == 200:
        docs = resp.json()
        st.dataframe(docs)
    else:
        st.error("Impossible de charger les documents")


def main():
    st.set_page_config(page_title="IA Agent Platform", layout="wide")
    if not get_token():
        render_login()
        return
    with st.sidebar:
        if st.button("Déconnexion"):
            logout()
            st.rerun()
    page = st.sidebar.radio("Navigation", ["Chat", "Documents"])
    if page == "Chat":
        render_sidebar()
        render_chat()
    else:
        render_documents()


if __name__ == "__main__":
    main()
