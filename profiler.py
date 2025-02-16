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


@dataclass
class MethodStats:
    """Stores statistical information for a method."""

    name: str
    call_count: int
    total_time: float
    average_time: float
    median_time: float
    standard_deviation: float


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

    def get_stats(self) -> list[MethodStats]:
        """Return statistical information for all profiled methods.

        The list is sorted by total execution time, highest to lowest.
        Units are milliseconds (ms).
        """

        def to_stat(profile: MethodProfile) -> MethodStats:
            if profile.times:
                average_t = profile.total_time / profile.call_count
                # TODO: Test that this equals sum(profile.times) / len(profile.times)
                median_t = median(profile.times)
                stdev_t = stdev(profile.times, average_t)
            else:
                average_t = median_t = stdev_t = 0.0

            return MethodStats(
                name=profile.name,
                call_count=profile.call_count,
                total_time=profile.total_time * 1e-6,
                average_time=average_t * 1e-6,
                median_time=median_t * 1e-6,
                standard_deviation=stdev_t * 1e-12,
            )

        return [to_stat(p) for p in sorted(self._profiles.values(), key=lambda x: x.total_time, reverse=True)]

    def stats_to_str(self) -> str:
        """Return statistics for all profiled methods."""
        output = [
            f"{'Method':<32} {'Calls':>5} {'Total(ms)':>9} {'Avg(ms)':>9} {'Mdn(ms)':>9} {'StdDev':>12}",
            "-" * 81,
        ]

        output.extend(
            " ".join(
                [
                    f"{method.name[:32]:<32}",
                    f"{method.call_count:>5}",
                    f"{method.total_time:>9.3f}",
                    f"{method.average_time:>9.3f}",
                    f"{method.median_time:>9.3f}",
                    f"{method.standard_deviation:>12.0f}",
                ]
            )
            for method in self.get_stats()
        )

        return "\n".join(output)


global_profiler = Profiler()
"""Global profiler instance."""
