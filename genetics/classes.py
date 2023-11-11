import json
import os
import random
import time
import uuid
from abc import ABC
from typing import List
from textwrap import wrap
import numpy as np
from genetics.basics import Agent, Point, AlgorithmStateAdapter, Crosser, Mutator, AgentFactory, Reference
import ctypes

lib = ctypes.CDLL('./../interpolate/interpolate.so')


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

    def interpolateForT(self, t) -> Point:
        points = [
            [int(point.getX()), int(point.getY())]
            for point in [self.__start] + self.__innerPoints + [self.__end]
        ]

        x, y = lib.interpolate(t, points)

        return Point(float(x), float(y))

    def getStartPoint(self) -> Point:
        return self.__start

    def getEndPoint(self) -> Point:
        return self.__end

    def getInnerPoints(self) -> List[Point]:
        return self.__innerPoints


class MainAgent(Agent):
    __eval: float
    __geneticRepresentation: str
    __alleleLength: int
    __threshold: int
    __numberOfInterpolationPoints: int

    __innerCurve: _BezierCurve
    __innerCurveDirty: bool = True

    def __init__(self, numberOfInterpolationPoints: int, threshold: int = 0, alleleLength: int = 64,
                 geneticRepresentation: str = ''):
        self.__numberOfInterpolationPoints = numberOfInterpolationPoints
        self.__alleleLength = alleleLength
        self.__threshold = threshold
        self.__geneticRepresentation = geneticRepresentation

    def getPointForT(self, t: float) -> Point:
        if self.__innerCurveDirty:
            self.__innerCurve = _BezierCurve.fromGeneticRepresentation(self.__geneticRepresentation,
                                                                       self.__alleleLength)
            self.__innerCurveDirty = False

        return self.__innerCurve.interpolateForT(t)

    def getStep(self) -> float:
        return 1 / self.__numberOfInterpolationPoints

    def getThreshold(self) -> int:
        return self.__threshold

    def getEvaluationValue(self) -> float:
        return self.__eval

    def setEvaluationValue(self, value: float) -> None:
        self.__eval = value

    def getGeneticRepresentation(self) -> str:
        return self.__geneticRepresentation

    def setGeneticRepresentation(self, geneticRepresentation: str) -> None:
        self.__innerCurveDirty = True
        self.__geneticRepresentation = geneticRepresentation

    def getLength(self) -> int:
        return len(self.__geneticRepresentation)

    def clone(self) -> "Agent":
        agent = MainAgent(self.__numberOfInterpolationPoints, self.__threshold, self.__alleleLength,
                          self.__geneticRepresentation)
        agent.setEvaluationValue(self.__eval)

        return agent

    def getAlleleLength(self) -> int:
        return self.__alleleLength

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

    def __init__(self, directory: str, prefix: str, ):
        self._dir = directory
        self._filePrefix = prefix

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
        self.setState(data)
        agentsData = [agent.toDictionary() for agent in self._state]

        with open(f"{self._dir}/{self._createNewStateFileName()}.json", 'w') as jsonFile:
            json.dump(agentsData, jsonFile, indent=2)


class BaseCrosser(Crosser, ABC):
    _chance: float
    _crossoverPoints: int

    def __init__(self, chance: float, crossoverPoints: int = 3):
        self._chance = chance
        self._crossoverPoints = crossoverPoints

    def crossover(self, agents: List[Agent]) -> None:
        maxCuttingPoint = min(agent.getLength() for agent in agents)
        cuttingPoints = sorted(random.randint(0, maxCuttingPoint) for _ in range(self._crossoverPoints))

        iterator = 0
        for cuttingPoint in cuttingPoints:
            nextIterator = (iterator + 1) % len(agents)

            agent1, agent2 = agents[iterator], agents[nextIterator]

            gr1, gr2 = agent1.getGeneticRepresentation(), agent2.getGeneticRepresentation()

            agent1.setGeneticRepresentation(self.__cross(gr1, gr2[cuttingPoint:], cuttingPoint))
            agent2.setGeneticRepresentation(self.__cross(gr2, gr1[cuttingPoint:], cuttingPoint))

            iterator = nextIterator

    def __cross(self, inputStr, replaceWith, startingAt):
        return inputStr[:startingAt] + replaceWith


class BaseMutator(Mutator, ABC):
    _chance: float
    _significantAlleles: int

    def __init__(self, chance: float, significantAlleles: int = 4):
        self._chance = chance
        self._significantAlleles = significantAlleles

    def mutate(self, agent: Agent) -> None:
        geneticRepresentation = agent.getGeneticRepresentation()
        newGeneticRepresentation = ''

        for index, bit in enumerate(geneticRepresentation):
            if self.checkIfMutateAgentBit(agent, index):
                bit = "1" if bit == "0" else "0"

            newGeneticRepresentation += bit

        agent.setGeneticRepresentation(newGeneticRepresentation)


class RandomMainAgentFactory(AgentFactory):
    __xMax: int
    __yMax: int
    __pointsMin: int
    __pointsMax: int
    __thresholdMin: int
    __thresholdMax: int
    __alleleLength: int
    __numberOfInterpolationPoints: int

    def __init__(
            self,
            xMax: int,
            yMax: int,
            pointsMin: int,
            pointsMax: int,
            thresholdMin: int,
            thresholdMax: int,
            alleleLength: int,
            numberOfInterpolationPoints: int
    ):
        self.__xMax = xMax
        self.__yMax = yMax
        self.__pointsMin = pointsMin
        self.__pointsMax = pointsMax
        self.__thresholdMin = thresholdMin
        self.__thresholdMax = thresholdMax
        self.__alleleLength = alleleLength
        self.__numberOfInterpolationPoints = numberOfInterpolationPoints

    def create(self) -> Agent:
        numberOfPoints = random.randint(self.__pointsMin, self.__pointsMax)
        innerPoints = [self.__createRandomPointGeneticRepresentation() for _ in range(numberOfPoints)]
        geneticRepresentation = (self.__createRandomPointGeneticRepresentation() +
                                 self.__createRandomPointGeneticRepresentation() +
                                 ''.join(innerPoints))
        threshold = random.randint(self.__thresholdMin, self.__thresholdMax)

        return MainAgent(
            self.__numberOfInterpolationPoints,
            threshold,
            self.__alleleLength,
            geneticRepresentation
        )

    def __createRandomPointGeneticRepresentation(self) -> str:
        return self.__createBinaryString(random.randint(0, self.__xMax)) + self.__createBinaryString(
            random.randint(0, self.__yMax))

    def __createBinaryString(self, value: int) -> str:
        binaryStr = bin(value)[2:]

        return binaryStr.rjust(self.__alleleLength, '0')


class JsonReference(Reference):
    __pointsValues = List[List[float]]
    __filePath: str

    def __init__(self, filePath):
        self.__filePath = filePath
        self.__getDataFromFile()

    def getValueOnPoint(self, point: Point, threshold: int = 0) -> int | float:
        if threshold > 0:
            return self.__getNeumannAverage(point.getX(), point.getY(), threshold)

        return self.__pointsValues[point.getY()][point.getX()]

    def setValueOnPoint(self, value: float, point: Point) -> None:
        if point.getX() > self.__xMax or point.getY() > self.__yMax:
            return

        self.__pointsValues[point.getY()][point.getX()] = value

    def xMax(self) -> int:
        return self.__xMax

    def yMax(self) -> int:
        return self.__yMax

    def __getNeumannAverage(self, x: int, y: int, threshold: int) -> float:
        height, width = self.yMax(), self.xMax()
        points = np.array(self.__pointsValues)

        y_range = slice(max(0, y - threshold), min(height, y + threshold + 1))
        x_range = slice(max(0, x - threshold), min(width, x + threshold + 1))

        neighbors = points[y_range, x_range].flatten()

        return np.mean(neighbors) if neighbors.size > 0 else 0.

    def __getDataFromFile(self) -> None:
        try:
            with open(self.__filePath, 'r') as file:
                data = json.load(file)

            if isinstance(data, dict) and 'pointsValues' in data:
                pointsValues = data['pointsValues']
                self.__xMax = data['xMax']
                self.__yMax = data['yMax']

                if isinstance(pointsValues, list):
                    self.__pointsValues = [[float(value) for value in row] for row in pointsValues]
                else:
                    print("Error: 'pointsValues' in JSON file is not an array.")
            else:
                print("Error: JSON file does not contain 'pointsValues' field or it's not a dictionary.")

        except FileNotFoundError:
            print(f"Error: File not found at {self.__filePath}.")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format.")
