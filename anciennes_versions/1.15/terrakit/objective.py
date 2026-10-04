import json

class Objective:

    def __init__(self, data):
        self.id = data["id"]
        self.title = data["title"]
        self.description = data["description"]

        self.type = data["type"]
        self.target = data["target"]

        self.amount = data["amount"]
        self.progress = data.get("progress", 0)

        self.completed = data.get("completed", False)


    def add_progress(self, value=1):

        if self.completed:
            return

        self.progress += value

        if self.progress >= self.amount:
            self.progress = self.amount
            self.completed = True


    def get_text(self):
        return (
            f"{self.title}\n"
            f"{self.description}\n"
            f"&f{self.progress}/{self.amount}"
        )
    
    
class ObjectiveManager:

    def __init__(self, file="objectives.json"):

        self.objectives = []

        with open(file, "r", encoding="utf8") as f:
            data = json.load(f)

        for obj in data:
            self.objectives.append(Objective(obj))


    def update(self, event_type, target, amount=1):

        for obj in self.objectives:

            if obj.type == event_type and obj.target == target:
                obj.add_progress(amount)


    def get_objectives(self):
        return self.objectives