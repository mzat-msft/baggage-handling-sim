import datetime as dt
import math
import operator
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Union


@dataclass
class Point:
    """Used to represent the position of a Gate."""
    x: float
    y: float

    def to_tuple(self):
        return (self.x, self.y)

    def distance(self, other):
        if not isinstance(other, Point):
            raise TypeError(f"Expected Point, got {type(other)}.")
        return math.dist(self.to_tuple(), other.to_tuple())


class Gate:
    """Class representing a gate at the airport.

    Gates are located somewhere in the airport. They are the place where
    flights arrive to or depart from.
    """
    def __init__(self, number: str, x: float, y: float):
        self.number = number
        self.location = Point(x, y)

    def distance(self, other):
        if isinstance(other, Gate):
            return self.location.distance(other.location)
        else:
            raise TypeError(f"Expected Gate, got {type(other)}.")


@dataclass
class Flight:
    """Class representing a Flight.

    Flights have a series of properties and carry some baggages that must be
    transferred to another flight.
    """
    number: str
    gate_number: str
    scheduled: dt.datetime
    actual: dt.datetime
    baggages: Optional[Dict[str, int]] = None  # (Flight number, N)


@dataclass
class Handler:
    """Class representing an airport handler.

    Handlers are operators that carry baggages from one flight to another.
    In principle, handlers can have different properties. That is some might be
    quicker, able to carry more load etc...
    """
    name: str
    capacity: int = 100
    load_time: int = 10 * 60  # seconds
    unload_time: int = 5 * 60  # seconds
    speed: float = 60.  # mph
    baggages: Optional[Dict[str, int]] = None
    route: Optional[List[str]] = None

    @property
    def n_bags(self):
        return sum(self.baggages.values())

    def take(self, flight_number: str, bags: int):
        if self.baggages is None:
            self.baggages = {}
        if flight_number in self.baggages:
            self.baggages[flight_number] += bags
        else:
            self.baggages[flight_number] = bags


class Airport:
    """Class representing the airport.

    The airport is represented here as a set of Gates. This class is useful for
    storing the distance matrix of the different gates.
    """
    def __init__(self, gates: Iterable[Gate]):
        self.gates: List[Gate] = list(gates)
        self.distance_matrix = self.compute_distance_matrix()

    def compute_distance_matrix(self):
        dist_matrix = []
        # As or-tools expects a symmetric matrix we have to do the naive double loop
        for gate1 in self.gates:
            gate1_distances = []
            for gate2 in self.gates:
                gate1_distances.append(gate1.distance(gate2))
            dist_matrix.append(gate1_distances)
        return dist_matrix

    def get_gate_idx(self, gate_number):
        """Return the index in the distance_matrix for the given gate_number."""
        for i, gate in enumerate(self.gates):
            if gate_number == gate.number:
                return i

    def get_distance(self, gate1, gate2) -> float:
        """Return the distance of two gates."""
        return self.distance_matrix[self.get_gate_idx(gate1)][self.get_gate_idx(gate2)]


class Schedule:
    """Class to represent the airport's schedule.

    Schedule is used to store information on Flights.
    """
    def __init__(self, flights: Iterable[Flight]):
        self.flights: List[Flight] = list(flights)

    def __getitem__(self, flight_number: str) -> Optional[Flight]:
        for flight in self.flights:
            if flight_number == flight.number:
                return flight
        return None

    def sort_by_time(self, which: str):
        return sorted(self.flights, key=operator.attrgetter(which))

    def sort_by_actual(self):
        return self.sort_by_time("actual")

    def sort_by_scheduled(self):
        return self.sort_by_time("scheduled")

    def __str__(self):
        return "\n".join(str(flight) for flight in self.flights)


class BaggageMatrix:
    """Class for representing the routing of baggages.

    We use this class to store information on where baggages from a fligth
    should go. All flights relationship can be obtained: the first index of the
    matrix is the flight number that has the baggage that the flight at the
    second index will need. The actual value of the matrix is the number of
    baggages that must go from flight A to flight B.
    """
    def __init__(self, flights: List[Flight]):
        self.matrix = self.fill_matrix(flights)
        self.initial_baggages = len(self)

    @staticmethod
    def fill_matrix(flights):
        matrix = defaultdict(dict)
        for flight in flights:
            if flight.baggages is None:
                continue
            for to_flight, baggages in flight.baggages.items():
                matrix[flight.number][to_flight] = baggages
        return matrix

    def remove_entry(self, flight_from, flight_to):
        self.matrix.pop(flight_from, flight_to)

    def __len__(self):
        """Return the number of baggages in the matrix."""
        baggages = 0
        for flight_from, val in self.matrix.items():
            for flight_to, bags in val.items():
                baggages += bags
        return baggages

    def __getitem__(self, flight_number):
        """Return which flights wait for baggages loaded in flight_number."""
        return {key: val for key, val in self.matrix[flight_number].items()}

    def __str__(self):
        return "\n".join(
            f"{key1}, {key2}: {val2}"
            for key1, val in self.matrix.items()
            for key2, val2 in val.items()
        )


class AirportSim:
    """Class representing the airport and its evolution in time.

    The airport is initialized with Gates and Schedule.
    Currently the simulation is just one step:
    - step 0: the baggage matrix is computed and all other variables are passed
      to the Solver. The Solver obtains the best routes for the handlers for
      the given configuration.
    - step 1: the simulation runs the different routes and checks how many
      baggages where missed. Baggages can be missed either because no handlers
      pick them up from a flight or because handlers arrive to the gate after a
      flight's departure.
    """

    def __init__(
        self,
        airport: Airport,
        schedule: Schedule,
        handlers: Union[int, List[Handler]],
    ):
        self.airport = airport
        self.schedule = schedule
        self.baggage_matrix = BaggageMatrix(self.schedule.flights)
        self.handlers = self._get_handlers(handlers)

    @staticmethod
    def _get_handlers(handlers: Union[int, List[Handler]]) -> List[Handler]:
        if isinstance(handlers, int):
            return [Handler(str(idx)) for idx in range(handlers)]
        elif all(isinstance(handler, Handler) for handler in handlers):
            return handlers
        else:
            raise TypeError(f'Expected int or List[Handler], got {type(handlers)}')

    def update_routes(self, routes: Dict[str, Optional[List[str]]]):
        for handler in self.handlers:
            handler.route = routes.get(handler.name)

    def unload_plane(self, flight, handler):
        # handler takes baggages from flight
        for flight_number, bags in self.baggage_matrix[flight].items():
            if flight_number not in handler.route:
                continue
            handler.take(flight_number, bags)
            self.baggage_matrix.remove_entry(flight, bags)

    def run_routes(self):
        """Let the handlers follow their routes."""
        for handler in self.handlers:
            time = None
            prev_flight = None
            for cur in handler.route:
                cur_flight = self.schedule[cur]

                if time is None:
                    time = cur_flight.actual

                if prev_flight is not None:
                    distance_leg = self.airport.get_distance(
                        prev_flight.gate_number, cur_flight.gate_number
                    )
                    time += dt.timedelta(hours=distance_leg / handler.speed)

                if cur_flight.baggages is None:
                    if time < cur_flight.actual:
                        handler.baggages.pop(cur)
                else:
                    if time < cur_flight.actual:
                        time = cur_flight.actual
                    self.unload_plane(cur, handler)
                    time += dt.timedelta(seconds=handler.unload_time)

                prev_flight = cur_flight

    def compute_missing_bags(self):
        """Return the number of bags that are not loaded onto their flight."""
        bags = 0
        bags += len(self.baggage_matrix)
        for handler in self.handlers:
            bags += handler.n_bags
        return bags / self.baggage_matrix.initial_baggages
