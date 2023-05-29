import string
from typing import List

from genetics.interfaces import Point, AgentPositionIterator, Agent, EvaluationModel


class BCPoint(Point):
    def __init__(self, x: int, y: int):
        self._x = x
        self._y = y

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._x


class BCAgentPositionIterator(AgentPositionIterator):
    def iterate(self) -> [Point]:
        pass


class BCAgent(Agent):

    def __int__(self):
        self._iterator = BCAgentPositionIterator()
        self._score = 0.0
        self._geneticRepresentation = []

    @property
    def score(self) -> float:
        return self._score

    @property
    def iterator(self) -> AgentPositionIterator:
        return self._iterator

    @property
    def geneticRepresentation(self) -> [string]:
        return self._geneticRepresentation

    def getNextPosition(self) -> Point | None:
        pass


class BCEvaluationModel(EvaluationModel):

    def __int__(self, data: List[List[int]]):
        self._data = data

    def getValue(self, point: Point) -> float:
        if len(self._data) <= point.y:
            if len(self._data[point.y]) <= point.x:
                return self._data[point.y][point.x]

        return -1.0
