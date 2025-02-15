import re
import time

from profiler import Profiler


def test_profiler() -> None:
    profiler = Profiler()

    profiler.start("a")
    time.sleep(0.06)
    profiler.start("c")
    profiler.start("a")
    time.sleep(0.06)
    profiler.start("b")
    time.sleep(0.03)

    log = profiler.log()
    assert re.match(
        r""" 0% c
(17|18|19|20|21|22|23)% b
(77|78|79|80|81|82|83)% a""",
        log,
    ), "If this assertion fails, the above sleep-times might be too short, leading to precision-loss."
