"""Bounded process workers; each owns its signal handlers and cloud cleanup."""
import subprocess


class ActiveJobs:
    def __init__(self, limit):
        self.limit = limit
        self.children = {}

    def reap(self):
        for key, child in list(self.children.items()):
            if child.poll() is not None:
                child.wait()
                del self.children[key]

    def start(self, key, command):
        self.reap()
        if key in self.children or len(self.children) >= self.limit:
            return False
        self.children[key] = subprocess.Popen(command)
        return True

    def stop(self):
        for child in self.children.values():
            if child.poll() is None:
                child.terminate()
        # Workers forward SIGTERM to their guard and await cloud cleanup.
        for child in self.children.values():
            child.wait()
        self.children.clear()
