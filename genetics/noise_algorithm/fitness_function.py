import math

from genetics.basics import FitnessFunction, Agent, Reference


class NoiseFitnessFunction(FitnessFunction):
    def evaluate(self, agent: Agent, reference: Reference) -> float:
        sumOfCoverage = 0
        points = agent.getPoints()

        for point in agent.getPoints():
            if point.getX() > reference.xMax() or point.getY() > reference.yMax():
                return 0

            sumOfCoverage += reference.getValueOnPoint(point, agent.getThreshold())

        return math.exp(-sumOfCoverage / len(points))
