
class TodoManager:

    def __init__(self):
        self.items = []

    def update(self, items: list) -> str:
        validated, in_progress_count = [], 0
        for item in items:
            status = item.get("status","pending")
            if status == "in_process":
                in_progress_count += 1
            validated.append({
                "id": item["id"], 
                "text": item["text"],
                "status": item["status"]
                })
        if in_progress_count > 1:
            raise ValueError("Only one task can be in_process")
        self.items = validated
        return self.render()
    
    def render(self) -> str:
        if not self.items:
            return "No todos."
        lines = []
        for item in self.items:
            marker = {"pending": "[ ]", "in_progress": "[>]", "completed": "[√]"}[item["status"]]
            lines.append(f"{marker} #{item['id']}: {item['text']}")
        done = sum(1 for t in self.items if t["status"] == "completed")
        lines.append(f"\n({done}/{len(self.items)} completed)")
        return "\n".join(lines)
    
TODO = TodoManager()