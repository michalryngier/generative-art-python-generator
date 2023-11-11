import unittest
from typing import List
from unittest.mock import patch

from genetics.basics import Point, Agent
from genetics.classes import MainAgent, _BezierCurve, BaseCrosser
from genetics.noise_algorithm.crosser import NoiseCrosser


class MockCrosser(BaseCrosser):

    def checkIfRun(self, agents: List[Agent]) -> bool:
        raise NotImplementedError


class Test_BaseCrosser(unittest.TestCase):
    @patch('random.randint')
    def test_crossover(self, mockRandint):
        mockRandint.side_effect = [3]
        geneticRepresentation1 = 'ABCDEFGH'
        geneticRepresentation2 = 'IJKL'

        agent1 = MainAgent(100, alleleLength=2, geneticRepresentation=geneticRepresentation1)
        agent2 = MainAgent(100, alleleLength=2, geneticRepresentation=geneticRepresentation2)

        crosser = MockCrosser(0.5, 1)

        crosser.crossover([agent1, agent2])

        self.assertEqual('ABCL', agent1.getGeneticRepresentation())
        self.assertEqual('IJKDEFGH', agent2.getGeneticRepresentation())


if __name__ == '__main__':
    unittest.main()
