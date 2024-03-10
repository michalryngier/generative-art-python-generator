import time
from multiprocessing import Pool
from typing import List
import math
import random

import numpy as np

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

    __executor: Pool

    def __init__(
            self,
            reference: Reference,
            stateAdapter: AlgorithmStateAdapter,
            crosser: Crosser,
            mutator: Mutator,
            agentFactory: AgentFactory,
            config: {},
            executor: Pool
    ):
        self.__reference = reference
        self.__stateAdapter = stateAdapter
        self.__crosser = crosser
        self.__mutator = mutator
        self.__agentFactory = agentFactory
        self.__config = config
        self.__executor = executor

        self.__initialize()

    def __initialize(self):
        self.__createInitialPopulation()

    def addFitnessFunction(self, fitnessFunc: FitnessFunction, wage: float) -> None:
        self.__fitnessFunctions.append(fitnessFunc)
        self.__fitnessFunctionsWages.append(wage)

    def save(self) -> None:
        self.__stateAdapter.save([agent.clone() for agent in self.__population])

    def load(self, algorithmState: AlgorithmStateAdapter) -> None:
        if self.__stateAdapter.hasState():
            self.__population = self.__stateAdapter.load()

    def run(self) -> None:
        iterations = self.__config["iterations"]

        for x in range(iterations):
            self.__evaluateAgents()

            # when without first population
            # if x != 0 and x % self.__config["savingFreq"] == 0:

            # when with first population
            if x % self.__config["savingFreq"] == 0:
                self.save()

            self.__sortAgents()
            self.__normalizeAgents()

            self.__crossoverAgents()
            self.__mutateAgents()

            progress = round(x / iterations * 100, 2)
            print(f"{progress}")

        self.__evaluateAgents()
        print(f"{100.0}")

    def __sortAgents(self, ) -> None:
        self.__population = sorted(self.__population, key=lambda x: x.getEvaluationValue(), reverse=False)

    def __normalizeAgents(self) -> None:
        fitnessScores = np.array([agent.getEvaluationValue() for agent in self.__population])
        minScore = fitnessScores[0]
        maxScore = fitnessScores[-1]

        for agent in self.__population:
            newScore = 1
            if minScore != maxScore:
                newScore = abs((agent.getEvaluationValue() - maxScore) / (minScore - maxScore))

            agent.setEvaluationValue(newScore)

    def __evaluateAgents(self):
        agents = self.__population
        fitnessFunctions = self.__fitnessFunctions
        fitnessFunctionsWages = self.__fitnessFunctionsWages
        reference = self.__reference

        evals = self.__executor.starmap(
            evaluateAgent,
            [(agent, fitnessFunctions, fitnessFunctionsWages, reference) for agent in agents]
        )

        for agent, eval_value in zip(agents, evals):
            agent.setEvaluationValue(eval_value)

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


def evaluateAgent(agent: Agent, fitnessFunctions, fitnessFunctionsWages, reference) -> float:
    eval = 0
    for index, fitnessFunc in enumerate(fitnessFunctions):
        eval += fitnessFunctionsWages[index] * fitnessFunc.evaluate(agent, reference)
    agent.setEvaluationValue(eval)
    return eval
