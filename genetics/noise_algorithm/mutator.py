import random

from genetics.basics import Agent
from genetics.classes import BaseMutator


class NoiseMutator(BaseMutator):
    def checkIfMutateAgentBit(self, agent: Agent, bitIndex: int) -> bool:
        if self._significantAlleles < (bitIndex % (agent.getAlleleLength() - 1)):
            return False

        factor = self._chance if agent.getEvaluationValue() == 0 else self._chance * agent.getEvaluationValue()

        return factor >= random.uniform(0, 1)
