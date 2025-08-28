import streamlit as st
from datetime import datetime
import uuid

# ---------- Page ----------
st.set_page_config(page_title="IndiBot", page_icon="🤖", layout="wide")

# ---------- Session Store (no files, in-memory only) ----------
store = st.session_state.setdefault("store", {"active": {}, "archived": {}})
current_id = st.session_state.setdefault("current_id", None)

def rerun():
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

# ---------- Helpers ----------
def new_chat():
    cid = uuid.uuid4().hex[:8]
    store["active"][cid] = {
        "title": "New Chat",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": []
    }
    st.session_state.current_id = cid
    rerun()

def open_chat(cid):
    st.session_state.current_id = cid
    rerun()

def rename_chat(cid, new_title, bucket="active"):
    if new_title.strip():
        store[bucket][cid]["title"] = new_title.strip()
    rerun()

def delete_chat(cid, bucket="active"):
    store[bucket].pop(cid, None)
    if bucket == "active" and st.session_state.current_id == cid:
        st.session_state.current_id = None
    rerun()

def archive_chat(cid):
    store["archived"][cid] = store["active"].pop(cid)
    if st.session_state.current_id == cid:
        st.session_state.current_id = None
    rerun()

def restore_chat(cid):
    store["active"][cid] = store["archived"].pop(cid)
    rerun()

def export_text(cid, bucket="active"):
    chat = store[bucket][cid]
    lines = [f"Title: {chat['title']}", f"Created: {chat['created_at']}", "-"*40]
    for m in chat["messages"]:
        lines.append(f"{m['role'].capitalize()}: {m['content']}")
    return "\n".join(lines)

def autotitle_if_needed(cid):
    chat = store["active"][cid]
    if chat["title"] == "New Chat":
        for m in chat["messages"]:
            if m["role"] == "user" and m["content"].strip():
                chat["title"] = m["content"].strip()[:40]
                break

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Options")
    st.button("✍️ New chat", use_container_width=True, on_click=new_chat)

    st.markdown("---")
    st.subheader("Chats")

    # Active chats
    if not store["active"]:
        st.caption("No chats yet. Start one!")
    else:
        # show newest first
        for cid, chat in list(store["active"].items())[::-1]:
            c1, c2 = st.columns([0.8, 0.2])
            if c1.button(chat["title"] or "Untitled", key=f"open_{cid}", use_container_width=True):
                open_chat(cid)
            with c2:
                # Simple 3-dots menu as an expander (works on all Streamlit versions)
                with st.expander("⋮"):
                    new_name = st.text_input("Rename", value=chat["title"], key=f"rn_{cid}")
                    if st.button("Save name", key=f"rns_{cid}"):
                        rename_chat(cid, new_name, bucket="active")
                    st.download_button(
                        "⬇️ Download (.txt)",
                        data=export_text(cid, bucket="active"),
                        file_name=f"{(chat['title'] or 'chat')}.txt",
                        key=f"dl_{cid}",
                        use_container_width=True,
                    )
                    if st.button("📦 Archive", key=f"arc_{cid}"):
                        archive_chat(cid)
                    if st.button("🗑️ Delete", key=f"del_{cid}"):
                        delete_chat(cid, bucket="active")

    # Archived chats
    if store["archived"]:
        with st.expander("🗂️ Library"):
            for cid, chat in list(store["archived"].items())[::-1]:
                c1, c2 = st.columns([0.8, 0.2])
                c1.write(f"📄 {chat['title'] or 'Untitled'}")
                with c2:
                    with st.expander("⋮"):
                        new_name = st.text_input("Rename", value=chat["title"], key=f"arn_{cid}")
                        if st.button("Save name", key=f"arns_{cid}"):
                            rename_chat(cid, new_name, bucket="archived")
                        st.download_button(
                            "⬇️ Download (.txt)",
                            data=export_text(cid, bucket="archived"),
                            file_name=f"{(chat['title'] or 'chat')}.txt",
                            key=f"adl_{cid}",
                            use_container_width=True,
                        )
                        if st.button("↩️ Restore", key=f"res_{cid}"):
                            restore_chat(cid)
                        if st.button("🗑️ Delete", key=f"adel_{cid}"):
                            delete_chat(cid, bucket="archived")

# ---------- Main area ----------
st.title("🤖 IndiBot")

if current_id and current_id in store["active"]:
    chat = store["active"][current_id]

    # show messages
    for m in chat["messages"]:
        with st.chat_message("user" if m["role"] == "user" else "assistant"):
            st.write(m["content"])

    # input
    text = st.chat_input("Say something…")
    if text:
        chat["messages"].append({"role": "user", "content": text})
        # simple echo for now; replace with Groq later
        reply = f"Echo: {text}"
        chat["messages"].append({"role": "assistant", "content": reply})
        autotitle_if_needed(current_id)
        rerun()
else:
    st.info("Start a new chat from the sidebar.")
