import json
from datetime import datetime
from pathlib import Path

DATA_FILE = Path("medications.json")

class MedicationManager:
    def __init__(self):
        self.data = {"medications": []}
        self.load_data()

    def load_data(self):
        if DATA_FILE.exists():
            try:
                self.data = json.loads(DATA_FILE.read_text())
            except Exception:
                self.data = {"medications": []}

    def save_data(self):
        DATA_FILE.write_text(json.dumps(self.data, indent=2))

    def get_todays_schedule(self):
        today = datetime.now().strftime("%Y-%m-%d")
        schedule = []
        for med in self.data["medications"]:
            for s in med.get("schedule", []):
                if s.get("date") == today:
                    schedule.append({
                        "time": s["time"],
                        "medication": med["name"],
                        "dosage": med["dosage"],
                        "taken": s.get("taken", False)
                    })
        return sorted(schedule, key=lambda x: x["time"])

    def get_current_medications(self):
        now = datetime.now().strftime("%H:%M")
        due = []
        for med in self.data["medications"]:
            for s in med.get("schedule", []):
                if s.get("time") == now and not s.get("taken", False):
                    due.append({
                        "name": med["name"],
                        "dosage": med["dosage"],
                        "schedule_time": s["time"]
                    })
        return due
    

    def mark_medication_taken(self, med_name: str, schedule_time: str) -> bool:
        changed = False
        for med in self.data["medications"]:
            if med["name"].lower() == med_name.lower():
                for s in med.get("schedule", []):
                    if s.get("time") == schedule_time:
                        s["taken"] = True
                        changed = True
        if changed:
            self.save_data()
        return changed
