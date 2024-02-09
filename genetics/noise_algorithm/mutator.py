import random

from genetics.basics import Agent
from genetics.classes import BaseMutator


class NoiseMutator(BaseMutator):
    def checkIfMutateAgentBit(self, agent: Agent) -> bool:
        evaluationValue = agent.getEvaluationValue()
        factor = self._chance if evaluationValue == 0 else self._chance * evaluationValue
        return factor >= random.random()
