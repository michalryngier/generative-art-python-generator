import time
from typing import List
import math
import random

from genetics.basics import GeneticAlgorithm, AlgorithmStateAdapter, Agent, FitnessFunction, Reference, Crosser, \
    Mutator, AgentFactory


class NoiseAlgorithm(GeneticAlgorithm):
    __population: List[Agent]

    __fitnessFunctions: List[FitnessFunction] = []
    __fitnessFunctionsWages: List[float] = []

    __stateAdapter: AlgorithmStateAdapter
    __config: {} = {}
    __reference: Reference
    __crosser: Crosser
    __mutator: Mutator
    __agentFactory: AgentFactory

    def __init__(
            self,
            reference: Reference,
            stateAdapter: AlgorithmStateAdapter,
            crosser: Crosser,
            mutator: Mutator,
            agentFactory: AgentFactory,
            config: {}
    ):
        self.__reference = reference
        self.__stateAdapter = stateAdapter
        self.__crosser = crosser
        self.__mutator = mutator
        self.__agentFactory = agentFactory
        self.__config = config

        self.__initialize()

    def __initialize(self):
        self.__createInitialPopulation()

    def addFitnessFunction(self, fitnessFunc: FitnessFunction, wage: float) -> None:
        self.__fitnessFunctions.append(fitnessFunc)
        self.__fitnessFunctionsWages.append(wage)

    def save(self) -> None:
        self.__stateAdapter.save(self.__population)

    def load(self, algorithmState: AlgorithmStateAdapter) -> None:
        if self.__stateAdapter.hasState():
            self.__population = self.__stateAdapter.load()

    def run(self) -> None:
        for x in range(self.__config["iterations"]):
            start = time.time()
            self.__evaluateAgents()
            print(f"evaluated in: {time.time() - start}")
            self.__crossoverAgents()
            self.__mutateAgents()

            if x % self.__config["savingFreq"] == 0:
                self.save()

            progress = x / self.__config["iterations"] * 100
            print(f"{progress}%")

        self.__evaluateAgents()

    def __evaluateAgents(self) -> None:

        for agent in self.__population:
            eval = 0
            for index, fitnessFunc in enumerate(self.__fitnessFunctions):
                eval += fitnessFunc.evaluate(agent, self.__reference) * self.__fitnessFunctionsWages[index]

            agent.setEvaluationValue(eval)


    def __crossoverAgents(self) -> None:
        divider = 2
        for x in range(math.floor(len(self.__population) / divider)):
            agents = random.sample(self.__population, divider)
            if self.__crosser.checkIfRun(agents):
                self.__crosser.crossover(agents)

    def __mutateAgents(self) -> None:
        for agent in self.__population:
            self.__mutator.mutate(agent)

    def __createInitialPopulation(self) -> None:
        population: List[Agent] = []
        for x in range(int(self.__config["populationSize"])):
            population.append(self.__agentFactory.create())

        self.__population = population
