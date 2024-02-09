import unittest

from genetics.classes import MainAgent


class TestMainAgent(unittest.TestCase):
    def test_getThreshold(self):
        agent = MainAgent(numberOfInterpolationPoints=6, threshold=3)

        result = agent.getThreshold()

        self.assertEqual(result, 3)


if __name__ == '__main__':
    unittest.main()
