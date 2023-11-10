from abc import ABC, abstractmethod
from typing import List


class Point:
    __x: int
    __y: int

    def __init__(self, x: float, y: float):
        self.__x = round(x)
        self.__y = round(y)

    def getX(self) -> int:
        return self.__x

    def getY(self) -> int:
        return self.__y


class Agent(ABC):
    @abstractmethod
    def getPoints(self) -> List[Point]:
        pass

    @abstractmethod
    def getThreshold(self) -> int:
        pass

    @abstractmethod
    def getEvaluationValue(self) -> float:
        pass

    @abstractmethod
    def setEvaluationValue(self, value: float) -> None:
        pass

    @abstractmethod
    def getLength(self) -> int:
        pass

    @abstractmethod
    def getGeneticRepresentation(self) -> str:
        pass

    @abstractmethod
    def setGeneticRepresentation(self, geneticRepresentation: str) -> None:
        pass

    @abstractmethod
    def clone(self) -> "Agent":
        pass

    @abstractmethod
    def getAlleleLength(self) -> int:
        pass

    @abstractmethod
    def toDictionary(self) -> {}:
        pass


class AgentFactory(ABC):
    @abstractmethod
    def create(self) -> Agent:
        pass


class Reference(ABC):
    @abstractmethod
    def getValueOnPoint(self, point: Point, threshold: int = 0) -> int | float:
        pass

    @abstractmethod
    def setValueOnPoint(self, value: int | float, point: Point) -> None:
        pass

    @abstractmethod
    def xMax(self) -> int:
        pass

    @abstractmethod
    def yMax(self) -> int:
        pass


class Crosser(ABC):

    @abstractmethod
    def crossover(self, agents: List[Agent]) -> None:
        """Get Agents by the reference and perform cross over updating the Agent objects"""
        pass

    @abstractmethod
    def checkIfRun(self, agents: List[Agent]) -> bool:
        pass


class Mutator(ABC):
    @abstractmethod
    def mutate(self, agent: Agent) -> None:
        """Get Agent by the reference and perform mutation updating the Agent object"""
        pass

    @abstractmethod
    def checkIfMutateAgentBit(self, agent: Agent, bitIndex: int) -> bool:
        pass


class FitnessFunction(ABC):
    @abstractmethod
    def evaluate(self, agent: Agent, reference: Reference) -> float:
        pass


class AlgorithmStateAdapter(ABC):
    @abstractmethod
    def setState(self, state: List[Agent]) -> None:
        pass

    @abstractmethod
    def hasState(self) -> bool:
        pass

    @abstractmethod
    def load(self) -> List[Agent]:
        pass

    @abstractmethod
    def save(self, data: List[Agent]) -> None:
        pass


class GeneticAlgorithm(ABC):
    @abstractmethod
    def run(self) -> None:
        pass

    @abstractmethod
    def addFitnessFunction(self, fitnessFunc: FitnessFunction, wage: float) -> None:
        pass

    @abstractmethod
    def save(self) -> AlgorithmStateAdapter:
        pass

    @abstractmethod
    def load(self, algorithmState: AlgorithmStateAdapter) -> None:
        pass
