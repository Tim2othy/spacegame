"""A simple profiler."""

import time


class Profiler:
    """A simple profiler."""

    def __init__(self) -> None:
        """Create a new profiler."""
        self.most_recent_time: None | float = None
        self.most_recent_action: None | str = None
        self.times: dict[str, float] = {}

    def start(self, name: str) -> None:
        """Start timing `name`.

        The stopping-time is implicitly the time of the next start-call to `self`, with any name.
        """
        now = time.time()
        if self.most_recent_action is None or self.most_recent_time is None:
            self.most_recent_time = now
            self.most_recent_action = name
            return

        delta = now - self.most_recent_time
        action = self.most_recent_action
        self.most_recent_action = name
        if action in self.times:
            self.times[action] = self.times[action] + delta
        else:
            self.times[action] = delta
        self.most_recent_time = now

    def log(self) -> str:
        """Show the current state of the profiler."""
        times = self.times.copy()

        # Insert currently running timer
        if self.most_recent_action is not None and self.most_recent_time is not None:
            now = time.time()
            delta = now - self.most_recent_time
            action = self.most_recent_action
            if action in times:
                times[action] = times[action] + delta
            else:
                times[action] = delta

        total_time = sum(times[name] for name in times)
        outputs: list[str] = []
        for name, t in sorted(times.items(), key=lambda entry: entry[1]):
            outputs.append(f"{t / total_time * 100:2.0f}% {name}")

        return "\n".join(outputs)
