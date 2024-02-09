import json
import os
import random
import time
import uuid
from abc import ABC
from typing import List
from textwrap import wrap

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

    def __init__(self, numberOfInterpolationPoints: int, threshold: int = 0, alleleLength: int = 64,
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
            "eval": self.__eval,
            "geneticRepresentation": self.__geneticRepresentation,
            "alleleLength": int(self.__alleleLength),
            "threshold": int(self.__threshold),
            "numberOfInterpolationPoints": int(self.__numberOfInterpolationPoints),
        }


class _JsonAgentStateAdapter(AlgorithmStateAdapter, ABC):
    _state: List[Agent] = None
    _filePrefix: str
    _dir: str

    def __init__(self, directory: str, prefix: str):
        self._dir = directory
        self._filePrefix = prefix

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

        files = filter(lambda x: x != 'config.json', files)

        return sorted([os.path.join(self._dir, f) for f in files], key=lambda f: os.path.getctime(f))

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

        for rawAgentData in stateRawList:
            agent = MainAgent(rawAgentData["numberOfInterpolationPoints"], rawAgentData["threshold"],
                              rawAgentData["alleleLength"], rawAgentData["geneticRepresentation"])
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
        points = self.__npPointsValues

        yRange = slice(max(0, y - threshold), min(height, y + threshold + 1))
        xRange = slice(max(0, x - threshold), min(width, x + threshold + 1))

        neighbors = points[yRange, xRange].flatten()

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
                    self.__npPointsValues = np.array(self.__pointsValues)
                else:
                    print("Error: 'pointsValues' in JSON file is not an array.")
            else:
                print("Error: JSON file does not contain 'pointsValues' field or it's not a dictionary.")

        except FileNotFoundError:
            print(f"Error: File not found at {self.__filePath}.")
        except json.JSONDecodeError:
            print("Error: Invalid JSON format.")
