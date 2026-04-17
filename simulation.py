
class Message:
    def __init__(self, start, end, speed=0.01):
        self.start = start
        self.end = end
        self.progress = 0.0
        self.speed = speed
    def update(self):
        self.progress += self.speed
        return self.progress >= 1.0
    