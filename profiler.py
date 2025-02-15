"""A simple profiler."""

import functools
import time
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class MethodProfile:
    """Stores profiling information for a method."""

    name: str
    call_count: int = 0
    total_time: float = 0.0
    times: list[float] = field(default_factory=list)


class Profiler:
    """A class to profile methods and display statistics."""

    def __init__(self) -> None:
        """Initialize the profiler."""
        self._profiles: dict[str, MethodProfile] = {}

    def profile_method(self, func: Callable) -> Callable:
        """Profiles the execution time of a method."""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            start_time = time.perf_counter_ns()
            result = func(*args, **kwargs)
            end_time = time.perf_counter_ns()

            execution_time = end_time - start_time
            method_name = f"{func.__qualname__}"

            if method_name not in self._profiles:
                self._profiles[method_name] = MethodProfile(name=method_name)

            profile = self._profiles[method_name]
            profile.call_count += 1
            profile.total_time += execution_time
            profile.times.append(execution_time)

            return result

        return wrapper

    def log_stats(self) -> str:
        """Return statistics for all profiled methods."""
        output = [
            f"{'Method':<16} {'Calls':<8} {'Total':<10} {'Avg (ns)':<10} {'Min (ns)':<10} {'Max (ns)':<10}",
            "-" * 80,
        ]

        for p in sorted(self._profiles.values(), key=lambda x: x.total_time, reverse=True):
            if p.times:
                avg_t = p.total_time / p.call_count
                # TODO: Test that this equals sum(profile.times) / len(profile.times)
                min_t = min(p.times)
                max_t = max(p.times)
            else:
                avg_t = min_t = max_t = 0.0

            output.append(
                " ".join(
                    [
                        f"{p.name[:16]:<16}",
                        f"{p.call_count:<8}",
                        f"{p.total_time:<10.0f}",
                        f"{avg_t:<10.1f}",
                        f"{min_t:<10.0f}",
                        f"{max_t:<10.0f}",
                    ]
                )
            )

        return "\n".join(output)


global_profiler = Profiler()
"""Global profiler instance."""
