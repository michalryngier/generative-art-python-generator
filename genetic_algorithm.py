import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path
import shutil

from genetics.classes import JsonReference, RandomMainAgentFactory, JsonMainAgentStateAdapter, \
    ClosePositionMainAgentFactory
from genetics.noise_algorithm.algorithm import NoiseAlgorithm
from genetics.noise_algorithm.crosser import NoiseCrosser
from genetics.noise_algorithm.fitness_function import NoiseFitnessFunction
from genetics.noise_algorithm.mutator import NoiseMutator

main_directory = Path(__file__).resolve().parent
outPath = f"{main_directory}/__out"


def main():
    if len(sys.argv) < 2:
        print("Usage: python genetic_algorithm.py [filename]")
        sys.exit(1)

    dirName = str(sys.argv[1])
    directoryPath = Path(f"{outPath}/{dirName}")

    if not directoryPath.is_dir():
        print(f"Not a directory {outPath}/{dirName}")
        sys.exit(1)

    runForOne(directoryPath, dirName)


def runForOne(directoryPath: Path, dirName: str):
    referencePath = f"{directoryPath}/reference.json"
    configPath = f"{directoryPath}/config.json"
    stateFilesDir = f"{directoryPath}/__out_{int(time.time())}"

    if not os.path.exists(referencePath) or not os.path.isfile(referencePath):
        print(f"File does not exist {referencePath}")
        sys.exit(1)

    if not os.path.exists(configPath) or not os.path.isfile(configPath):
        print(f"File does not exist {configPath}")
        sys.exit(1)

    if not os.path.exists(stateFilesDir) or not os.path.isfile(stateFilesDir):
        os.makedirs(stateFilesDir)

    shutil.copyfile(configPath, f"{stateFilesDir}/config.json")
    config = readConfig(configPath)

    reference = JsonReference(referencePath)
    agentFactory = ClosePositionMainAgentFactory(
        reference.xMax(),
        reference.yMax(),
        config["pointsMinMax"][0],
        config["pointsMinMax"][1],
        config["thresholdMinMax"][0],
        config["thresholdMinMax"][1],
        config["alleleLength"],
        config["numberOfInterpolationPoints"],
        config["startingPositionRadius"]
    )
    stateAdapter = JsonMainAgentStateAdapter(stateFilesDir, dirName)
    crosser = NoiseCrosser(config["crossoverChance"], config["crossoverPoints"])
    mutator = NoiseMutator(config["mutationChance"], config["significantAlleles"])

    algorithm = NoiseAlgorithm(reference, stateAdapter, crosser, mutator, agentFactory, config, Pool(processes=12))
    algorithm.addFitnessFunction(NoiseFitnessFunction(), 1)
    start = time.time()
    algorithm.run()
    print(f"time: {time.time() - start}")
    algorithm.save()


def readConfig(configPath: str) -> {}:
    with open(configPath, 'r') as file:
        return json.load(file)


if __name__ == "__main__":
    main()
