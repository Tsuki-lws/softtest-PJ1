import hashlib
import sys
import traceback
from typing import Tuple, Callable, Set, Any, List

from runner.runner import Runner
from utils.coverage import Coverage, Location


class FunctionCoverageRunner(Runner):
    def __init__(self, function: Callable) -> None:
        """Initialize.  `function` is a function to be executed"""
        self._coverage: Set[Location] = set()
        self._trace: List[Location] = []
        self.function = function
        self.cumulative_coverage: List[int] = []
        self.all_coverage: Set[Location] = set()
        
    def run_function(self, inp: str) -> Any:
        exc_info = None
        result = None
        with Coverage() as cov:
            try:
                result = self.function(inp)
            except Exception:
                exc_info = sys.exc_info()

        self._coverage = cov.coverage()
        self._trace = list(cov.trace())
        self.all_coverage |= self._coverage
        self.cumulative_coverage.append(len(self.all_coverage))

        if exc_info is not None:
            _, exc, tb = exc_info
            raise exc.with_traceback(tb)

        return result

    def coverage(self) -> Set[Location]:
        return self._coverage

    def trace(self) -> List[Location]:
        return self._trace
    
    def run(self, inp: str) -> Tuple[Any, str]:
        try:
            result = self.run_function(inp)
            outcome = self.PASS
        except Exception as exc:
            stack_trace = "".join(traceback.format_tb(exc.__traceback__))
            result = hashlib.md5(stack_trace.encode()).hexdigest()
            outcome = self.FAIL

        return result, outcome
