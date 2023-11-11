import numpy as np

from genetics.basics import FitnessFunction, Agent, Reference


class NoiseFitnessFunction(FitnessFunction):
    def evaluate(self, agent: Agent, reference: Reference) -> float:
        sumOfCoverage = 0
        step = agent.getStep()
        arrange = np.arange(0, 1 + step, step)

        for t in arrange:
            point = agent.getPointForT(t)
            if point.getX() >= reference.xMax() or point.getY() >= reference.yMax():
                return 0

            sumOfCoverage += reference.getValueOnPoint(point, agent.getThreshold())

        return np.exp(-(sumOfCoverage / len(arrange)))
