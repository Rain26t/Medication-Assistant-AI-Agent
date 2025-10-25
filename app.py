import streamlit as st
from datetime import datetime
from medication_data import MedicationManager
from medication_agent import MedicationAssistant

# ---------- Initialize ----------
def init_session():
    if "assistant" not in st.session_state:
        st.session_state.assistant = MedicationAssistant()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_input" not in st.session_state:
        st.session_state.current_input = ""

# ---------- UI Style ----------
STYLE = """
<style>
.user-msg {
    background: #e7f3ff;
    color: #000000;
    padding: 12px;
    border-radius: 10px;
    margin: 8px 0;
    border-left: 4px solid #2E86AB;
}
.assistant-msg {
    background: #f1f9f2;
    color: #000000;
    padding: 12px;
    border-radius: 10px;
    margin: 8px 0;
    border-left: 4px solid #34a853;
}
.alert-box {
    background: #ff6b6b;
    color: white;
    padding: 12px;
    border-radius: 8px;
    margin: 10px 0;
}
button[kind="primary"] {
    background-color: #2E86AB !important;
    color: white !important;
    border-radius: 8px !important;
}
</style>
"""

# ---------- Main ----------
def main():
    st.set_page_config(page_title="MediCare Companion", page_icon="💊", layout="wide")
    st.markdown(STYLE, unsafe_allow_html=True)
    init_session()

    st.title("💊 MediCare Companion")
    st.write(f"🕒 **Time:** {datetime.now().strftime('%I:%M %p')}")

    assistant = st.session_state.assistant
    med_manager = assistant.med_manager

    # ---------- Sidebar ----------
    with st.sidebar:
        st.header("Quick Actions")
        if st.button("What should I take now?"):
            st.session_state.current_input = "What should I take now?"
            st.rerun()
        if st.button("Show my schedule"):
            st.session_state.current_input = "Show my schedule"
            st.rerun()
        if st.button("Clear chat"):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.header("Due Now")

        due_now = med_manager.get_current_medications()
        if due_now:
            for med in due_now:
                time_label = med.get("schedule_time", "")
                st.write(f"**{med['name']}** — {med['dosage']} at {time_label}")
                if st.button(f"Mark {med['name']} ({time_label}) as taken", key=f"{med['name']}_{time_label}"):
                    success = med_manager.mark_medication_taken(med["name"], time_label)
                    if success:
                        st.success(f"✅ {med['name']} at {time_label} marked as taken.")
                    else:
                        st.warning("⚠️ Could not mark as taken (time mismatch or already taken).")
                    st.rerun()
        else:
            st.success("✅ No medications due right now.")

    # ---------- Main chat ----------
    col1, col2 = st.columns([2, 1])
    with col1:
        st.header("Chat with Assistant")

        if med_manager.get_current_medications():
            st.markdown('<div class="alert-box">🚨 You have medications due right now!</div>', unsafe_allow_html=True)

        # ✅ Chat input with "Send" button next to the text box
        with st.form(key="chat_form", clear_on_submit=True):
            input_col, btn_col = st.columns([4, 1])
            with input_col:
                user_input = st.text_input(
                    "Type your message:",
                    key="chat_input",
                    placeholder="Ask about your medications..."
                )
            with btn_col:
                send = st.form_submit_button("Send 💬")

            if send and user_input.strip():
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.spinner("Thinking..."):
                    reply = assistant.run(user_input)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                # Input clears automatically due to clear_on_submit=True

        st.markdown("---")

        # ✅ Display chat messages (newest at TOP)
        for msg in reversed(st.session_state.messages):
            css = "user-msg" if msg["role"] == "user" else "assistant-msg"
            prefix = "**You:** " if msg["role"] == "user" else ""
            st.markdown(f'<div class="{css}">{prefix}{msg["content"]}</div>', unsafe_allow_html=True)

    # ---------- Right column ----------
    with col2:
        st.header("Today's Schedule")
        schedule = med_manager.get_todays_schedule()
        for s in schedule:
            color = "#000000" if s["taken"] else "#000000"
            status = "✅ Taken" if s["taken"] else "⏰ Upcoming"
            st.markdown(f"""
            <div style="background:{color};padding:8px;margin:4px 0;border-radius:5px;">
                <strong>{s['time']}</strong> - {s['medication']}<br>
                <small>{s['dosage']} • {status}</small>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
