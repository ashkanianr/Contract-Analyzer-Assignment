"""Streamlit UI: upload PDF, analyze, display compliance results. Chat is informational only."""
import os
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
                return
            except Exception as e:
                st.error(f"Request failed: {e}")
                return

        st.success(f"Done. Pages: {data.get('page_count', 'N/A')}")
        compliance = data.get("compliance", {})
        items = compliance.get("items", [])
        for i, item in enumerate(items):
            state = item.get("compliance_state", "")
            if state == "Fully Compliant":
                badge = "🟢 Fully Compliant"
            elif state == "Partially Compliant":
                badge = "🟡 Partially Compliant"
            else:
                badge = "🔴 Non-Compliant"
            with st.expander(f"**{i+1}. {item.get('compliance_question', 'Question')}** — {badge}", expanded=True):
                quotes = item.get("relevant_quotes", "")
                if isinstance(quotes, list):
                    quotes = "\n".join(f"- {q}" for q in quotes)
                st.markdown(f"**Relevant quotes**\n{quotes}")
                st.markdown(f"**Rationale**\n{item.get('rationale', '')}")
                if item.get("confidence") is not None:
                    st.caption(f"Confidence: {item['confidence']}%")
        st.session_state["last_result"] = data
        st.session_state["analyzed"] = True

    # Chat (bonus) – informational only
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
        prompt = st.text_input("Ask about the contract", key="chat_input")
        if prompt:
            st.session_state["messages"].append({"role": "user", "content": prompt})
            try:
                with httpx.Client(timeout=60.0) as client:
                    r = client.post(
                        f"{base}/chat",
                        json={"message": prompt},
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
