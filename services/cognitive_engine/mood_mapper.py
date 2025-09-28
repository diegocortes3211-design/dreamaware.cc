class MoodMapper:
    def __init__(self):
        self.moods = []

    def add_mood(self, mood):
        self.moods.append(mood)

    def get_moods(self):
        return self.moods

    def clear_moods(self):
        self.moods = []
