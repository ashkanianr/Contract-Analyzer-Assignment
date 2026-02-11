"""Streamlit UI: upload PDF, analyze, display compliance results. Chat is informational only."""
import os
import pandas as pd
import streamlit as st
import httpx

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_PREFIX = "/api"


def main():
    st.set_page_config(page_title="Contract Analyzer", layout="wide")
    st.title("Contract Analyzer")
    st.caption("Upload a PDF contract to get structured compliance analysis (Table 1).")

    # Sidebar: backend URL
    with st.sidebar:
        backend_url = st.text_input("Backend URL", value=BACKEND_URL, key="backend_url")
        base = backend_url.rstrip("/") + API_PREFIX

    # Upload and Analyze
    uploaded = st.file_uploader("Upload PDF contract", type=["pdf"], key="pdf_upload")
    if uploaded and st.button("Analyze", type="primary"):
        with st.spinner("Processing… parsing PDF and running compliance analysis."):
            try:
                with httpx.Client(timeout=120.0) as client:
                    r = client.post(
                        f"{base}/analyze",
                        files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                    )
                r.raise_for_status()
                data = r.json()
            except httpx.HTTPStatusError as e:
                st.error(f"Analysis failed: {e.response.status_code} – {e.response.text[:500]}")
            except Exception as e:
                st.error(f"Request failed: {e}")
            else:
                st.session_state["last_result"] = data
                st.session_state["analyzed"] = True
                st.session_state["messages"] = []  # clear chat when new analysis

    # Always show compliance results if we have them (so they don't disappear when using chat)
    if st.session_state.get("last_result"):
        data = st.session_state["last_result"]
        st.success(f"Analysis complete. Pages: {data.get('page_count', 'N/A')}")
        compliance = data.get("compliance", {})
        items = compliance.get("items", [])
        rows = []
        for item in items:
            quotes = item.get("relevant_quotes", "")
            if isinstance(quotes, list):
                quotes = "\n".join(f"- {q}" for q in quotes) if quotes else ""
            rows.append({
                "Compliance Question": item.get("compliance_question", ""),
                "Compliance State": item.get("compliance_state", ""),
                "Confidence": f"{item['confidence']}%" if item.get("confidence") is not None else "-",
                "Relevant Quotes": str(quotes),
                "Rationale": item.get("rationale", ""),
            })
        df = pd.DataFrame(rows)
        df.index = range(1, len(df) + 1)
        st.dataframe(df, use_container_width=True)

    # Chat (bonus) – informational only; use form so question is sent once
    st.markdown("---")
    st.subheader("Chat (informational only)")
    st.caption("Compliance decisions always come from the structured analyzer above. This chat is for Q&A over the document only.")
    if st.session_state.get("analyzed"):
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        for msg in st.session_state["messages"]:
            role = msg["role"]
            st.markdown(f"**{role}:**")
            st.write(msg["content"])
            st.markdown("")

        with st.form("chat_form", clear_on_submit=True):
            prompt = st.text_input("Ask about the contract", key="chat_input")
            submitted = st.form_submit_button("Send")
        if submitted and prompt and prompt.strip():
            user_msg = prompt.strip()
            st.session_state["messages"].append({"role": "user", "content": user_msg})
            with st.spinner("Thinking…"):
                try:
                    history = st.session_state["messages"][:-1]
                    with httpx.Client(timeout=60.0) as client:
                        r = client.post(
                            f"{base}/chat",
                            json={"message": user_msg, "messages": history},
                        )
                    r.raise_for_status()
                    reply = r.json().get("reply", "No reply.")
                except Exception as e:
                    reply = f"Error: {e}"
            st.session_state["messages"].append({"role": "assistant", "content": reply})
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()
    else:
        st.info("Upload and analyze a PDF first to enable chat.")


if __name__ == "__main__":
    main()
