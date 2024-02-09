import numpy as np

from genetics.basics import FitnessFunction, Agent, Reference


class NoiseFitnessFunction(FitnessFunction):
    def evaluate(self, agent: Agent, reference: Reference) -> float:
        sumOfCoverage = 0
        step = agent.getStep()
        arrange = np.arange(0, 1 + step, step)

        for t in arrange:
            point = agent.getPointForT(t)
            x = point.getX()
            y = point.getY()
            if x >= reference.xMax() or y >= reference.yMax():
                return 0
            if x <= 0 or y <= 0:
                return 0

            sumOfCoverage += reference.getValueOnPoint(point, agent.getThreshold()) / 1

        return np.exp(-sumOfCoverage)
