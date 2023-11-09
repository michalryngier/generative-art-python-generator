import json
import os
import time
import uuid
from abc import ABC, abstractmethod
from typing import List
from textwrap import wrap

import numpy as np

from genetics.basics import Agent, Point, AlgorithmStateAdapter


class _BezierCurve:
    __start: Point
    __end: Point
    __innerPoints: List[Point]
    __alleleLength: int

    def __init__(self, start: Point, end: Point, points: List[Point]):
        self.__start = start
        self.__end = end
        self.__innerPoints = points

    @classmethod
    def fromGeneticRepresentation(cls, genetic: str, alleleLength: int) -> "_BezierCurve":
        numericSystem = 2
        chunks: List[str] = wrap(genetic, alleleLength)
        start = Point(int(chunks.pop(0), numericSystem), int(chunks.pop(0), numericSystem))
        end = Point(int(chunks.pop(0), numericSystem), int(chunks.pop(0), numericSystem))
        points = [Point(int(x, numericSystem), int(y, numericSystem)) for x, y in zip(chunks[::2], chunks[1::2])]

        return _BezierCurve(start, end, points)

    def interpolate(self, step: float) -> List[Point]:
        points: List[Point] = []
        for t in np.arange(0, 1 + step, step):
            points.append(self.__interpolateForT(t))

        return points

    def __interpolateForT(self, t: float) -> Point:
        points = [self.__start] + self.__innerPoints + [self.__end]

        if t == 0:
            return points[0]

        order = len(points) - 1

        if t == 1:
            return points[order]

        mt = 1 - t
        p = points

        # Linear curve
        if order == 1:
            x = mt * p[0].getX() + t * p[1].getX()
            y = mt * p[0].getY() + t * p[1].getY()
            return Point(x, y)

        # Quadratic or cubic curve
        if 2 <= order < 4:
            mt2 = mt * mt
            t2 = t * t
            a, b, c, d = 0, 0, 0, 0

            if order == 2:
                p = [p[0], p[1], p[2], Point(0, 0)]
                a = mt2
                b = mt * t * 2
                c = t2
            else:
                a = mt2 * mt
                b = mt2 * t * 3
                c = mt * t2 * 3
                d = t * t2

            x = a * p[0].getX() + b * p[1].getX() + c * p[2].getX() + d * p[3].getX()
            y = a * p[0].getY() + b * p[1].getY() + c * p[2].getY() + d * p[3].getY()
            return Point(x, y)

        # Higher order curves - use de Casteljau's computation
        dCpts = np.array([(p.getX(), p.getY()) for p in points])
        while len(dCpts) > 1:
            dCpts = (1 - t) * dCpts[:-1] + t * dCpts[1:]

        return Point(float(dCpts[0][0]), float(dCpts[0][1]))

    def getStartPoint(self) -> Point:
        return self.__start

    def getEndPoint(self) -> Point:
        return self.__end

    def getInnerPoints(self) -> List[Point]:
        return self.__innerPoints


class MainAgent(Agent):
    __eval: float
    __geneticRepresentation: str
    __innerCurve: _BezierCurve
    __alleleLength: int
    __threshold: int
    __numberOfInterpolationPoints: int

    def __init__(self, numberOfPoints: int, threshold: int = 0, alleleLength: int = 64,
                 geneticRepresentation: str = ''):
        self.__numberOfInterpolationPoints = numberOfPoints
        self.__alleleLength = alleleLength
        self.__threshold = threshold
        self.__geneticRepresentation = geneticRepresentation

    def getPoints(self, step: float) -> List[Point]:
        self.__innerCurve = _BezierCurve.fromGeneticRepresentation(self.__geneticRepresentation, self.__alleleLength)

        return self.__innerCurve.interpolate(1 / self.__numberOfInterpolationPoints)

    def getThreshold(self) -> int:
        return self.__threshold

    def getEvaluationValue(self) -> float:
        return self.__eval

    def setEvaluationValue(self, value: float) -> None:
        self.__eval = value

    def toDictionary(self) -> {}:
        return {
            "eval": self.__eval,
            "geneticRepresentation": self.__geneticRepresentation,
            "alleleLength": self.__alleleLength,
            "threshold": self.__threshold,
            "numberOfInterpolationPoints": self.__numberOfInterpolationPoints,
        }


class _JsonAgentStateAdapter(AlgorithmStateAdapter, ABC):
    _state: List[Agent] = None
    _filePrefix: str
    _dir: str

    def __init__(self, directory: str, prefix: str):
        self._dir = directory
        self._filePrefix = prefix

    @abstractmethod
    def load(self) -> List[Agent]:
        pass

    @abstractmethod
    def save(self, data: List[Agent]) -> None:
        pass

    def setState(self, state: List[Agent]) -> None:
        self._state = state

    def hasState(self) -> bool:
        return self._state is not None

    def _getStateFileContent(self, path: str) -> List:
        try:
            with open(path, 'r') as jsonFile:
                # Load the JSON data from the file into a Python dictionary
                data_dict = json.load(jsonFile)

                # Now, 'data_dict' contains the contents of the JSON file as a dictionary
                print("Contents of the JSON file:")
                print(data_dict)

        except FileNotFoundError:
            print(f"The file '{path}' was not found.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file '{path}': {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

        return json.load(jsonFile)

    def _getLatestStateFileName(self) -> str | None:
        files = [f for f in os.listdir(self._dir) if os.path.isfile(os.path.join(self._dir, f))]

        if not files:
            return None

        filePathsAndTimes = [(os.path.join(self._dir, f), os.path.getmtime(os.path.join(self._dir, f))) for f in
                             files]

        return max(filePathsAndTimes, key=lambda x: x[1])[0]

    def _createNewStateFileName(self) -> str:
        timestamp = int(time.time())
        random_uuid = str(uuid.uuid4()).replace("-", "")

        return f"{self._filePrefix}_{timestamp}_{random_uuid}"


class JsonMainAgentStateAdapter(_JsonAgentStateAdapter):
    def load(self) -> List[Agent]:
        agents: List[Agent] = []
        latestFileName = self._getLatestStateFileName()

        if latestFileName is None:
            return agents

        stateRawList = self._getStateFileContent(latestFileName)

        for rawAgentData in stateRawList:
            agent = MainAgent(rawAgentData["numberOfInterpolationPoints"], rawAgentData["threshold"],
                              rawAgentData["alleleLength"], rawAgentData("geneticRepresentation"))
            agent.setEvaluationValue(rawAgentData["eval"])
            agents.append(agent)

        return agents

    def save(self, data: List[Agent]) -> None:
        if self.hasState() is False:
            return

        agentsData = [agent.toDictionary() for agent in self._state]

        with open(f"{self._dir}/{self._createNewStateFileName()}.json", 'w') as jsonFile:
            json.dump(agentsData, jsonFile, indent=2)
