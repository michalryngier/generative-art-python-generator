import json
import os
import sys
from pathlib import Path

from genetics.classes import JsonReference, RandomMainAgentFactory, JsonMainAgentStateAdapter
from genetics.noise_algorithm.algorithm import NoiseAlgorithm
from genetics.noise_algorithm.crosser import NoiseCrosser
from genetics.noise_algorithm.mutator import NoiseMutator

outPath = './__out'


def main():
    if len(sys.argv) != 1:
        print("Usage: python main.py filename")
        sys.exit(1)

    dirName = int(sys.argv[1])
    directoryPath = Path(f"{outPath}/{dirName}")

    if not directoryPath.is_dir():
        print(f"Not a directory {outPath}/{dirName}")
        sys.exit(1)

    runForOne(directoryPath, dirName)


def runForOne(directoryPath: Path, dirName: str):
    referencePath = f"{directoryPath}/reference.json"
    configPath = f"{directoryPath}/config.json"
    stateFilesDir = f"{directoryPath.name}/__out"

    if not os.path.exists(referencePath) or not os.path.isfile(referencePath):
        print(f"File does not exist {referencePath}")
        sys.exit(1)

    if not os.path.exists(configPath) or not os.path.isfile(configPath):
        print(f"File does not exist {configPath}")
        sys.exit(1)

    if not os.path.exists(configPath) or not os.path.isfile(configPath):
        os.makedirs(stateFilesDir)

    config = readConfig(configPath)

    reference = JsonReference(referencePath)
    agentFactory = RandomMainAgentFactory(
        config["xMax"],
        config["yMax"],
        config["pointsMin"],
        config["pointsMax"],
        config["thresholdMin"],
        config["thresholdMax"],
        config["alleleLength"],
        config["numberOfInterpolationPoints"]
    )
    stateAdapter = JsonMainAgentStateAdapter(stateFilesDir, dirName)
    crosser = NoiseCrosser(config["crossoverChance"], config["crossoverPoints"])
    mutator = NoiseMutator(config["mutationChance"])

    algorithm = NoiseAlgorithm(reference, stateAdapter, crosser, mutator,
                               agentFactory, config)
    algorithm.run()
    algorithm.save()


def readConfig(configPath: str) -> {}:
    with open(configPath, 'r') as file:
        return json.load(file)


if __name__ == "__main__":
    main()
