import json
import math
import os
import random
import time
import uuid
from abc import ABC
from typing import List
from textwrap import wrap

from Cython.Shadow import _ArrayType

from genetics.basics import Agent, Point, AlgorithmStateAdapter, Crosser, Mutator, AgentFactory, Reference
import ctypes
import numpy as np

interpolateLib = ctypes.CDLL('./image/interpolate/interpolate.so')
interpolate_function = interpolateLib.interpolate
interpolate_function.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double), ctypes.c_int]
interpolate_function.restype = ctypes.POINTER(ctypes.c_double)


class _BezierCurve:
    __cPoints: ctypes.Array
    __points: List[List[int | int]]
    __pointsSize: int

    def __init__(self, start: [int | int], end: [int | int], innerRawPoints: List[List[int | int]]):
        self.__points = [start] + innerRawPoints + [end]
        self.__cPoints = self.__convertPointsToCDouble(self.__points)
        self.__pointsSize = len(self.__points)

    def __convertPointsToCDouble(self, points: List[List[int | int]]) -> ctypes.Array:
        return (ctypes.c_double * (2 * len(points)))(*[item for sublist in points for item in sublist])

    @classmethod
    def fromGeneticRepresentation(cls, genetic: str, alleleLength: int) -> "_BezierCurve":
        numericSystem = 2
        chunks: List[str] = wrap(genetic, alleleLength)
        start = [int(chunks.pop(0), numericSystem), int(chunks.pop(0), numericSystem)]
        end = [int(chunks.pop(0), numericSystem), int(chunks.pop(0), numericSystem)]
        points = [[int(x, numericSystem), int(y, numericSystem)] for x, y in zip(chunks[::2], chunks[1::2])]

        return _BezierCurve(start, end, points)

    def interpolateForT(self, t) -> Point:
        if t == 0:
            return Point(self.__points[0][0], self.__points[0][1])
        if t == 1:
            return Point(self.__points[-1][0], self.__points[-1][1])

        points = self.__cPoints
        resultPointer = interpolate_function(t, points, self.__pointsSize)
        result = [resultPointer[i] for i in range(2)]

        interpolateLib.reset(resultPointer)

        return Point(result[0], result[1])


class MainAgent(Agent):
    __eval: float
    __geneticRepresentation: str
    __alleleLength: int
    __threshold: int
    __numberOfInterpolationPoints: int
    __innerCurve: _BezierCurve
    __innerCurveDirty = False
    __step: float = None

    def __init__(self, numberOfInterpolationPoints: int, threshold: int = 1, alleleLength: int = 64,
                 geneticRepresentation: str = ''):
        self.__numberOfInterpolationPoints = numberOfInterpolationPoints
        self.__alleleLength = alleleLength
        self.__threshold = threshold
        self.setGeneticRepresentation(geneticRepresentation)

    def getPointForT(self, t: float) -> Point:
        if self.__innerCurveDirty:
            self.__updateInnerCurve()

        return self.__innerCurve.interpolateForT(t)

    def __updateInnerCurve(self):
        self.__innerCurve = _BezierCurve.fromGeneticRepresentation(
            self.__geneticRepresentation,
            self.__alleleLength
        )
        self.__innerCurveDirty = False

    def getStep(self) -> float:
        if self.__step is None:
            self.__step = 1 / self.__numberOfInterpolationPoints

        return self.__step

    def setStep(self, step: float) -> None:
        self.__step = step
        self.__numberOfInterpolationPoints = round(1 / step)

    def getThreshold(self) -> int:
        return self.__threshold

    def getEvaluationValue(self) -> float:
        return self.__eval

    def setEvaluationValue(self, value: float) -> None:
        self.__eval = value

    def getGeneticRepresentation(self) -> str:
        return self.__geneticRepresentation

    def setGeneticRepresentation(self, geneticRepresentation: str) -> None:
        self.__geneticRepresentation = geneticRepresentation
        self.__innerCurveDirty = True

    def getLength(self) -> int:
        return len(self.__geneticRepresentation)

    def clone(self) -> "Agent":
        agent = MainAgent(self.__numberOfInterpolationPoints, self.__threshold, self.__alleleLength,
                          self.__geneticRepresentation)
        agent.setEvaluationValue(self.__eval)

        return agent

    def getAlleleLength(self) -> int:
        return self.__alleleLength

    def setAlleleLength(self, length: int) -> None:
        self.__alleleLength = length

    def toDictionary(self) -> {}:
        return {
            "e": self.__eval,
            "g": self.__geneticRepresentation,
            "a": int(self.__alleleLength),
            "t": int(self.__threshold),
            "n": int(self.__numberOfInterpolationPoints),
        }


class _JsonAgentStateAdapter(AlgorithmStateAdapter, ABC):
    _state: List[Agent] = None
    _filePrefix: str
    _dir: str
    _legacy: bool

    def __init__(self, directory: str, prefix: str, legacy: bool = False):
        self._dir = directory
        self._filePrefix = prefix
        self._legacy = legacy

    def setState(self, state: List[Agent]) -> None:
        self._state = state

    def hasState(self) -> bool:
        return self._state is not None

    def _getStateFileContent(self, path: str) -> List:
        try:
            with open(path, 'r') as jsonFile:
                return json.load(jsonFile)
        except FileNotFoundError:
            print(f"The file '{path}' was not found.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in file '{path}': {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def _getStateFileNames(self) -> List[str] | None:
        files = [f for f in os.listdir(self._dir) if os.path.isfile(os.path.join(self._dir, f))]

        if not files:
            return None

        files = filter(lambda x: x != 'config.json' and x != '.DS_Store', files)

        return sorted([os.path.join(self._dir, f) for f in files])

    def _getLatestStateFileName(self) -> str | None:
        files = self._getStateFileNames()

        if not files:
            return None

        filePathsAndTimes = [(f, os.path.getmtime(os.path.join(self._dir, f))) for f in files]

        return max(filePathsAndTimes, key=lambda x: x[1])[0]

    def _createNewStateFileName(self) -> str:
        timestamp = int(time.time())
        random_uuid = str(uuid.uuid4()).replace("-", "")

        return f"{self._filePrefix}_{timestamp}_{random_uuid}"


class JsonMainAgentStateAdapter(_JsonAgentStateAdapter):
    def load(self, index: int = None) -> List[Agent]:
        agents: List[Agent] = []
        latestFileName = None

        if index is not None:
            fileNames = self._getStateFileNames()
            if len(fileNames) > index:
                latestFileName = fileNames[index]
            else:
                return agents

        if latestFileName is None:
            latestFileName = self._getLatestStateFileName()

        if latestFileName is None:
            return agents

        stateRawList = self._getStateFileContent(latestFileName)

        if stateRawList is None:
            return agents

        # Legacy mode
        if self._legacy:
            for rawAgentData in stateRawList:
                agent = MainAgent(rawAgentData["numberOfInterpolationPoints"], rawAgentData["threshold"],
                                  rawAgentData["alleleLength"], rawAgentData["geneticRepresentation"])
                agent.setEvaluationValue(rawAgentData["eval"])
                agents.append(agent)
        else:
            for rawAgentData in stateRawList:
                agent = MainAgent(rawAgentData["n"], rawAgentData["t"],
                                  rawAgentData["a"], rawAgentData["g"])
                agent.setEvaluationValue(rawAgentData["e"])
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

        for index, char in enumerate(geneticRepresentation):
            segmentSize = agent.getAlleleLength()
            if self._significantAlleles >= (index % (segmentSize - 1)):
                if self.checkIfMutateAgentBit(agent):
                    newGeneticRepresentation += '1' if char == '0' else '0'
                else:
                    newGeneticRepresentation += char
            else:
                newGeneticRepresentation += char

        agent.setGeneticRepresentation(newGeneticRepresentation)


class RandomMainAgentFactory(AgentFactory):
    _xMax: int
    _yMax: int
    _pointsMin: int
    _pointsMax: int
    _thresholdMin: int
    _thresholdMax: int
    _alleleLength: int
    _numberOfInterpolationPoints: int

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
        self._xMax = xMax
        self._yMax = yMax
        self._pointsMin = pointsMin
        self._pointsMax = pointsMax
        self._thresholdMin = thresholdMin
        self._thresholdMax = thresholdMax
        self._alleleLength = alleleLength
        self._numberOfInterpolationPoints = numberOfInterpolationPoints

    def create(self) -> Agent:
        numberOfPoints = random.randint(self._pointsMin, self._pointsMax)
        innerPoints = [self._createRandomPointGeneticRepresentation() for _ in range(numberOfPoints)]
        geneticRepresentation = (self._createRandomPointGeneticRepresentation() +
                                 self._createRandomPointGeneticRepresentation() +
                                 ''.join(innerPoints))
        threshold = random.randint(self._thresholdMin, self._thresholdMax)

        return MainAgent(
            self._numberOfInterpolationPoints,
            threshold,
            self._alleleLength,
            geneticRepresentation
        )

    def _createRandomPointGeneticRepresentation(self) -> str:
        return self._createBinaryString(random.randint(0, self._xMax)) + self._createBinaryString(
            random.randint(0, self._yMax))

    def _createBinaryString(self, value: int) -> str:
        binaryStr = bin(value)[2:]

        return binaryStr.rjust(self._alleleLength, '0')


class ClosePositionMainAgentFactory(RandomMainAgentFactory):
    __startPositionRadius: int

    def __init__(
            self,
            xMax: int,
            yMax: int,
            pointsMin: int,
            pointsMax: int,
            thresholdMin: int,
            thresholdMax: int,
            alleleLength: int,
            numberOfInterpolationPoints: int,
            startPositionRadius: int
    ):
        super().__init__(xMax, yMax, pointsMin, pointsMax, thresholdMin, thresholdMax, alleleLength,
                         numberOfInterpolationPoints)
        self.__startPositionRadius = startPositionRadius

    def _createRandomPointGeneticRepresentation(self) -> str:
        startX, startY = (random.randint(0, self._xMax), random.randint(0, self._yMax))
        angle = random.uniform(0, 2 * math.pi)
        randomRadius = random.uniform(0, self.__startPositionRadius)
        x = int(startX + randomRadius * math.cos(angle))
        y = int(startY + randomRadius * math.sin(angle))
        x = max(0, min(x, self._xMax))
        y = max(0, min(y, self._yMax))

        return self._createBinaryString(int(x)) + self._createBinaryString(int(y))


class JsonReference(Reference):
    __pointsValues: np.ndarray
    __filePath: str

    def __init__(self, filePath):
        self.__filePath = filePath
        self.__getDataFromFile()

    def getValueOnPoint(self, point: Point, threshold: int = 0) -> int | float:
        x, y = point.getX(), point.getY()
        if threshold > 1:
            return self.__getNeumannAverage(x, y, threshold)

        return float(self.__pointsValues[y, x])

    def setValueOnPoint(self, value: float, point: Point) -> None:
        x, y = point.getX(), point.getY()
        if 0 <= x <= self.__xMax and 0 <= y <= self.__yMax:
            self.__pointsValues[y, x] = value

    def xMax(self) -> int:
        return self.__xMax

    def yMax(self) -> int:
        return self.__yMax

    def __getNeumannAverage(self, x: int, y: int, threshold: int) -> float:
        threshold = math.floor(threshold / 2)
        yMin, yMax = max(0, y - threshold), min(self.yMax(), y + threshold + 1)
        xMin, xMax = max(0, x - threshold), min(self.xMax(), x + threshold + 1)

        neighbors = self.__pointsValues[yMin:yMax, xMin:xMax].flatten()

        return np.mean(neighbors) if neighbors.size > 0 else 0.0

    def __getDataFromFile(self) -> None:
        try:
            with open(self.__filePath, 'r') as file:
                data = json.load(file)

            if isinstance(data, dict) and 'pointsValues' in data:
                pointsValues = data['pointsValues']
                self.__xMax = data['xMax']
                self.__yMax = data['yMax']

                if isinstance(pointsValues, list):
                    self.__pointsValues = np.array(pointsValues, dtype=float)
                    self.__yMax, self.__xMax = self.__pointsValues.shape[0] - 1, self.__pointsValues.shape[1] - 1
                else:
                    print("Error: 'pointsValues' in JSON file is not an array.")
            else:
                print("Error: JSON file does not contain 'pointsValues' field or it's not a dictionary.")

        except FileNotFoundError:
            print(f"Error: File not found at {self.__filePath}.")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format.")
