import string
from abc import ABC, abstractmethod


class Point(ABC):
    @property
    @abstractmethod
    def x(self) -> int:
        pass

    @property
    @abstractmethod
    def y(self) -> int:
        pass


class AgentPositionIterator(ABC):
    @abstractmethod
    def iterate(self) -> [Point]:
        pass


class Agent(ABC):
    @property
    @abstractmethod
    def score(self) -> float:
        pass

    @property
    @abstractmethod
    def iterator(self) -> AgentPositionIterator:
        pass

    @abstractmethod
    def getNextPosition(self) -> Point | None:
        pass

    @property
    @abstractmethod
    def geneticRepresentation(self) -> [string]:
        pass


class EvaluationModel(ABC):
    @abstractmethod
    def getValue(self, point: Point) -> float:
        pass


class AFitnessFunction:

    @property
    @abstractmethod
    def weight(self) -> float:
        pass

    @abstractmethod
    def evaluate(self, agent: Agent, against: EvaluationModel) -> float:
        pass


class FitnessFunctionDecorator(ABC):
    @property
    @abstractmethod
    def fitnessFunction(self) -> AFitnessFunction:
        pass

    @abstractmethod
    def decorate(self, agent: Agent) -> float:
        pass


class FitnessFunction(ABC, AFitnessFunction, FitnessFunctionDecorator):
    @property
    @abstractmethod
    def decorator(self) -> FitnessFunctionDecorator | None:
        pass

    @abstractmethod
    def _applyDecorator(self, agent: Agent, against: EvaluationModel) -> float:
        pass

    @abstractmethod
    def _performEvaluation(self):
        pass


class GeneticOperation(ABC):

    @property
    @abstractmethod
    def chance(self) -> float:
        pass

    @abstractmethod
    def run(self) -> Agent:
        pass


class Mutation(ABC, GeneticOperation):
    @abstractmethod
    def run(self, agent: Agent) -> Agent:
        pass


class Crossover(ABC, GeneticOperation):
    @abstractmethod
    def run(self, agentA: Agent, agentB: Agent) -> Agent:
        pass


class PopulationEvaluator(ABC):
    pass


class PopulationSettings(ABC):
    pass


class Population(ABC):

    @property
    @abstractmethod
    def settings(self) -> PopulationSettings:
        pass

    @property
    @abstractmethod
    def evaluator(self) -> PopulationEvaluator:
        pass

    @property
    @abstractmethod
    def agents(self) -> [Agent]:
        pass

    @abstractmethod
    def performOperation(self, operation: GeneticOperation) -> [Agent]:
        pass

    @abstractmethod
    def evaluate(self, ) -> [Agent]:
        pass
