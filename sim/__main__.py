import datetime as dt

from .airport import Airport, AirportSim, Flight, Gate, Schedule
from .solver import SequentialSolver

airport = Airport([
    Gate('1', 0., 10.),
    Gate('2', 0., 0.),
])
flights = [
    Flight(
        "LX123",
        "1",
        dt.datetime(2022, 10, 11, 12, 0),
        dt.datetime(2022, 10, 11, 12, 0),
        {"SU123": 10},
    ),
    Flight(
        "SU123",
        "2",
        dt.datetime(2022, 10, 11, 14, 0),
        dt.datetime(2022, 10, 11, 14, 0),
    ),
]
schedule = Schedule(flights)
solver = SequentialSolver()
airport_sim = AirportSim(airport, schedule, handlers=1)
routes = solver.solve(airport_sim)
airport_sim.update_routes(routes)
airport_sim.run_routes()
print(airport_sim.compute_missing_bags())
