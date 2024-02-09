from typing import List
import random

from genetics.basics import Agent
from genetics.classes import BaseCrosser


class NoiseCrosser(BaseCrosser):
    def checkIfRun(self, agents: List[Agent]) -> bool:
        rand = random.random()
        agentChances = [agent.getEvaluationValue() * self._chance for agent in agents]

        return any(chance < rand for chance in agentChances) is False

