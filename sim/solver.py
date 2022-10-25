import abc
from typing import Dict, List, Optional

from .airport import AirportSim


class Solver(abc.ABC):
    def __init__(self):
        """Initialize the solver class."""

    @abc.abstractmethod
    def solve(
        self,
        airport_sim: AirportSim,
    ) -> Dict[str, Optional[List[str]]]:
        """
        Return the handlers' routes as dictionary.

        The keys of the dictionary are the handlers' names and the values are
        lists containing the number of the flights they will visit
        sequentially.
        """


class SequentialSolver(Solver):
    """Solver class implementing a simple algorithm for testing purpose."""
    def solve(self, airport_sim):
        handlers = list(airport_sim.handlers)
        routes = {
            handlers.pop().name: [
                flight.number for flight in airport_sim.schedule.sort_by_actual()
            ]
        }
        for handler in handlers:
            routes[handler] = None
        return routes
