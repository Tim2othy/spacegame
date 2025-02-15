"""A simple profiler."""

import functools
import time
from collections.abc import Callable
from dataclasses import dataclass, field


# TODO: We should have a way of checking how much
# of main's time we profile in total, lest we
# end up optimising things that aren't great drains
# to begin with.


# As importing `statistics` breaks pygbag for some
# reason, we need to roll our own
def median(values: list[float]) -> float:
    """Return the median of a list of values.

    >>> median([1,2,3])
    2
    >>> median([1,2,3,4])
    2.5

    """
    sorted_values = sorted(values)
    mid = len(values) // 2
    if len(sorted_values) % 2 == 0:
        return sum(sorted_values[mid - 1 : mid + 1]) / 2
    return sorted_values[mid]


def stdev(values: list[float], mean: float) -> float:
    """Return the standard deviation of a list of values."""
    return sum((x - mean) ** 2 for x in values) ** 0.5


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
            f"{'Method':<32} {'Calls':>5} {'Total(μs)':>9} {'Avg(μs)':>7} {'Mdn(μs)':>7} {'StDev(μs)':>9}",
            "─" * 74,
        ]

        for p in sorted(self._profiles.values(), key=lambda x: x.total_time, reverse=True):
            if p.times:
                average_t = p.total_time / p.call_count
                # TODO: Test that this equals sum(profile.times) / len(profile.times)
                median_t = median(p.times)
                stdev_t = stdev(p.times)
            else:
                average_t = median_t = stdev_t = 0.0

            output.append(
                " ".join(
                    [
                        f"{p.name[:32]:<32}",
                        f"{p.call_count:>5}",
                        f"{p.total_time / 1000:9.0f}",
                        f"{average_t / 1000:7.0f}",
                        f"{median_t / 1000:7.0f}",
                        f"{stdev_t / 1000:9.0f}",
                    ]
                )
            )

        return "\n".join(output)


global_profiler = Profiler()
"""Global profiler instance."""
