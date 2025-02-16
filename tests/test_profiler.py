import re
import time

from profiler import global_profiler


def test_profiler() -> None:
    @global_profiler.profile_method
    def method_a() -> None:
        time.sleep(0.02)

    @global_profiler.profile_method
    def method_b() -> None:
        time.sleep(0.01)

    @global_profiler.profile_method
    def method_c() -> None:
        pass

    method_a()
    method_c()
    method_a()
    method_b()

    epsilon = 0.05
    stdev_cap = 1e-4
    c_millisecond_cap = 15

    stats = global_profiler.get_stats()
    a_profile_count, b_profile_count, c_profile_count = 0, 0, 0
    for m in stats:
        if m.name == "test_profiler.<locals>.method_a":
            a_profile_count += 1
            assert abs(1 - m.total_time / 40) < epsilon, "Total time did not match expectation"
            assert abs(1 - m.average_time / 20) < epsilon, "Average time did not match expectation"
            assert abs(1 - m.median_time / 20) < epsilon, "Median time did not match expectation"
            assert m.standard_deviation < stdev_cap, "Standard deviation should be low"
        elif m.name == "test_profiler.<locals>.method_b":
            b_profile_count += 1
            assert abs(1 - m.total_time / 10) < epsilon, "Total time did not match expectation"
            assert abs(1 - m.average_time / 10) < epsilon, "Average time did not match expectation"
            assert abs(1 - m.median_time / 10) < epsilon, "Median time did not match expectation"
            assert m.standard_deviation == 0, "Standard deviation should be exactly zero"
        elif m.name == "test_profiler.<locals>.method_c":
            c_profile_count += 1
            assert 0 <= m.total_time < c_millisecond_cap, "Total time did not match expectation"
            assert 0 <= m.average_time < c_millisecond_cap, "Average time did not match expectation"
            assert 0 <= m.median_time < c_millisecond_cap, "Median time did not match expectation"
            assert m.standard_deviation == 0, "Standard deviation should be exactly zero"

    assert a_profile_count == 1, "method_a should have exactly one entry in stats"
    assert b_profile_count == 1, "method_b should have exactly one entry in stats"
    assert c_profile_count == 1, "method_c should have exactly one entry in stats"
