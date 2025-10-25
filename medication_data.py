import json
from datetime import datetime
from pathlib import Path


DATA_FILE = Path("medications.json")


class MedicationManager:
    def __init__(self):
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {"patient_name": "Unknown", "medications": []}

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def get_todays_schedule(self):
        """Return today's medication schedule."""
        today = datetime.now().strftime("%Y-%m-%d")
        results = []
        for med in self.data["medications"]:
            for sched in med["schedule"]:
                results.append({
                    "medication": med["name"],
                    "dosage": med["dosage"],
                    "time": sched["time"],
                    "taken": sched["taken"]
                })
        return results

    def get_current_medications(self):
        """Return medications due within 1 hour of now."""
        now = datetime.now()
        current_hour = now.hour
        current_min = now.minute
        current_time = f"{current_hour:02}:{current_min:02}"

        results = []
        for med in self.data["medications"]:
            for sched in med["schedule"]:
                if not sched["taken"]:
                    sched_time = sched["time"]
                    if abs(int(sched_time.split(":")[0]) - current_hour) <= 1:
                        results.append({
                            "name": med["name"],
                            "dosage": med["dosage"],
                            "schedule_time": sched_time
                        })
        return results

    def mark_medication_taken(self, name: str, time: str) -> bool:
        """Mark a medication as taken by name and time."""
        for med in self.data["medications"]:
            if med["name"].lower() == name.lower():
                for sched in med["schedule"]:
                    if sched["time"] == time:
                        sched["taken"] = True
                        self.save()
                        return True
        return False

    def get_medication_info(self, name: str) -> dict:
        """Return full medication details by name (case-insensitive)."""
        for med in self.data["medications"]:
            if med["name"].lower() == name.lower():
                return med
        return {}
