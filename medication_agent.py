import os
from dotenv import load_dotenv
load_dotenv()

from medication_data import MedicationManager

# Optional Groq AI
try:
    from groq import Groq
    groq_available = True
except ImportError:
    groq_available = False


class MedicationAssistant:
    def __init__(self):
        self.med_manager = MedicationManager()
        self.client = None
        self.model = "llama-3.1-8b-instant"
        self.timeout_seconds = 15
        self.api_key = os.getenv("GROQ_API_KEY")

        if groq_available and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                print("✅ Groq client ready.")
            except Exception as e:
                print(f"⚠️ Groq init failed: {e}")
                self.client = None
        else:
            print("⚠️ Running in offline mode (Groq not configured).")

    # ------------ MAIN RUN ------------
    def run(self, query: str) -> str:
        query = query.lower().strip()

        # Simple local intents
        if "schedule" in query:
            return self._show_schedule()
        if "take now" in query or "due" in query:
            return self._show_due_now()
        if query.startswith("mark "):
            return self._mark_from_query(query)

        # Use Groq AI if available
        if self.client:
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful medical assistant."},
                        {"role": "user", "content": query}
                    ],
                    timeout=self.timeout_seconds
                )
                msg = resp.choices[0].message.content if hasattr(resp.choices[0], "message") else resp.choices[0].text
                return msg.strip()
            except Exception as e:
                return f"⚠️ Groq API error: {e}"
        else:
            return self._offline_reply(query)

    # ------------ LOCAL HELPERS ------------
    def _offline_reply(self, query: str) -> str:
        if "hello" in query or "hi" in query:
            return "👋 Hello! How can I help you with your medications today?"
        if "take" in query:
            meds = self.med_manager.get_current_medications()
            if not meds:
                return "You have no medications due right now."
            lines = [f"💊 {m['name']} — {m['dosage']} at {m['schedule_time']}" for m in meds]
            return "Here’s what’s due:\n" + "\n".join(lines)
        return "🤖 AI features unavailable, but I can still manage your medication schedule."

    def _show_schedule(self):
        sched = self.med_manager.get_todays_schedule()
        if not sched:
            return "📅 No medications scheduled for today."
        text = "\n".join(
            [f"{s['time']}: {s['medication']} — {s['dosage']} ({'Taken' if s['taken'] else 'Pending'})" for s in sched]
        )
        return "Today's schedule:\n" + text

    def _show_due_now(self):
        meds = self.med_manager.get_current_medications()
        if not meds:
            return "✅ No medications due right now."
        lines = [f"💊 {m['name']} — {m['dosage']} at {m['schedule_time']}" for m in meds]
        return "These are due now:\n" + "\n".join(lines)
    

    def _mark_from_query(self, query: str):
        parts = query.replace("mark", "").strip().split()
        if len(parts) < 2:
            return "❌ Please specify medication and time, e.g., 'mark aspirin 08:00'"
        med, time = parts[0], parts[1]
        if self.med_manager.mark_medication_taken(med, time):
            return f"✅ {med} at {time} marked as taken."
        return f"⚠️ Could not mark {med} at {time}. Check name or time."
