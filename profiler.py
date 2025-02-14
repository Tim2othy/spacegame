"""A simple profiler."""

import time


class Profiler:
    """A simple profiler."""

    def __init__(self) -> None:
        """Start the profiler."""
        self.most_recent_time = time.time()
        self.times: dict[str, float] = {}

    def start(self, name: str) -> None:
        """Start timing `name`.

        The stopping-time is implicitly the time of the next start-call to `self`, with any name.
        """
        now = time.time()
        delta = now - self.most_recent_time
        if name in self.times:
            self.times[name] = self.times[name] + delta
        else:
            self.times[name] = delta
        self.most_recent_time = now

    def log(self) -> str:
        """Show the current state of the profiler."""
        total_time = sum(self.times[name] for name in self.times)
        outputs: list[str] = []
        for name, t in sorted(self.times.items(), key=lambda entry: entry[1]):
            outputs.append(f"{t / total_time * 100:.2f}% {name}")

        return "\n".join(outputs)
