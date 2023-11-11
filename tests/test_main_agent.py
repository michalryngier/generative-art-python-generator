import unittest

from genetics.basics import Point
from genetics.classes import MainAgent, _BezierCurve


class TestMainAgent(unittest.TestCase):
    def test_getThreshold(self):
        agent = MainAgent(numberOfPoints=6, threshold=3)

        result = agent.getThreshold()

        self.assertEqual(result, 3)


class Test_BezierCurve(unittest.TestCase):
    def test_fromGeneticRepresentation(self):
        geneticRepresentation = '00000000010000000001000000001100000000010000000011000000000100000000000000000001'
        alleleLength = 10

        curve = _BezierCurve.fromGeneticRepresentation(geneticRepresentation, alleleLength)

        self.assertEqual(curve.getStartPoint().getX(), 1)
        self.assertEqual(curve.getStartPoint().getY(), 1)

        self.assertEqual(curve.getEndPoint().getX(), 3)
        self.assertEqual(curve.getEndPoint().getY(), 1)

        self.assertEqual(len(curve.getInnerPoints()), 2)

        self.assertEqual(curve.getInnerPoints()[0].getX(), 3)
        self.assertEqual(curve.getInnerPoints()[0].getY(), 1)

        self.assertEqual(curve.getInnerPoints()[1].getX(), 0)
        self.assertEqual(curve.getInnerPoints()[1].getY(), 1)


if __name__ == '__main__':
    unittest.main()
