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

        # 🧍 User profile (personalization)
        self.user_profile = {
            "name": "Fahim",
            "age": 29,
            "gender": "male",
            "medical_conditions": ["asthma"],
            "preferred_tone": "friendly and professional",
            "timezone": "Asia/Tokyo"
        }

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

        # Medication info queries
        if any(word in query for word in ["what is", "purpose", "about", "doctor", "instruction", "note", "who prescribed"]):
            return self._get_medication_details(query)

        # Use Groq AI if available
        if self.client:
            try:
                # 🧠 Include user profile for personalized responses
                profile_info = (
                    f"The user is {self.user_profile['name']}, "
                    f"a {self.user_profile['age']}-year-old {self.user_profile['gender']} "
                    f"with {', '.join(self.user_profile['medical_conditions'])}. "
                    f"Respond in a {self.user_profile['preferred_tone']} tone. "
                    f"The user's timezone is {self.user_profile['timezone']}."
                )

                # Include summary of all medications for context
                meds_summary = ", ".join(
                    [f"{m['name']} ({m['dosage']})" for m in self.med_manager.data["medications"]]
                )

                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are MediCare, a friendly and empathetic medical assistant. "
                            "You speak in a calm, reassuring tone. "
                            "Always provide accurate medical guidance in simple language. "
                            "If the user seems anxious or sick, respond with warmth and encouragement. "
                            "Keep answers clear, concise, and supportive. "
                            + profile_info
                            + f" The user's current medications are: {meds_summary}."
                        ),
                    },
                    {"role": "user", "content": query},
                ]

                # 🧩 Send request to Groq
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    timeout=self.timeout_seconds
                )

                msg = (
                    resp.choices[0].message.content
                    if hasattr(resp.choices[0], "message")
                    else resp.choices[0].text
                )
                return msg.strip()

            except Exception as e:
                return f"⚠️ Groq API error: {e}"
        else:
            return self._offline_reply(query)

    # ------------ LOCAL HELPERS ------------
    def _offline_reply(self, query: str) -> str:
        if "hello" in query or "hi" in query:
            return "👋 Hi Fahim! How are you feeling today? Remember to stay hydrated. 💚"
        if "take" in query:
            meds = self.med_manager.get_current_medications()
            if not meds:
                return "😊 You’re all up to date — no medications are due right now!"
            lines = [f"💊 {m['name']} — {m['dosage']} at {m['schedule_time']}" for m in meds]
            return "Here’s what’s due:\n" + "\n".join(lines)
        return "🤖 I'm here to help with your medication schedule, Fahim. What would you like to check?"

    def _show_schedule(self):
        sched = self.med_manager.get_todays_schedule()
        if not sched:
            return "📅 No medications scheduled for today."
        text = "\n".join(
            [
                f"{s['time']}: {s['medication']} — {s['dosage']} "
                f"({'Taken' if s['taken'] else 'Pending'})"
                for s in sched
            ]
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

    def _get_medication_details(self, query: str) -> str:
        """Return info about a medication (purpose, doctor, notes, etc.)."""
        for med in self.med_manager.data["medications"]:
            if med["name"].lower() in query:
                info = self.med_manager.get_medication_info(med["name"])
                if not info:
                    return "⚠️ I couldn't find details about that medication."

                details = (
                    f"💊 **{info['name']}** — {info['dosage']}\n"
                    f"🩺 *Purpose:* {info['purpose']}\n"
                    f"📋 *Instructions:* {info['instructions']}\n"
                    f"🩹 *Notes:* {info['notes']}\n"
                    f"👨‍⚕️ *Prescribed by:* {info['prescribing_doctor']}\n"
                    f"🕒 *Schedule times:* {', '.join([s['time'] for s in info['schedule']])}"
                )
                return details

        return "❌ I couldn’t find that medication in your list."
