# Testing parameters:
# - crossover chance (0.5 - 1.0)
# - mutation chance ((0) - 0.00005 - 0.1)
# - points min-max (0-10, 0-10)
# - crossover points (1-10)
# For each parameter value 10 tests are performed.
# Crossover chance has a step of 0.2: 10 * 26 = 260 tests
# Mutation chance has a step of 0.00005: 10 * 201 = 2010 tests
# Points min-max has 10 * 55 = 550 tests. 10 * {[10 * (10 + 1)] / 2}
# Crossover points has a step of 1: 10 * 10 = 100 tests
# Altogether there will be: 260 + 2010 + 550 + 100 = 2920 tests

import csv
import fnmatch
import glob
import json
import os
import subprocess
from pathlib import Path
import cv2 as cv
import numpy as np
from skimage import io

from genetics.classes import JsonMainAgentStateAdapter
from ratings.utils import benford
from ratings.utils import fractal_dimension

main_directory = Path(__file__).resolve().parent
outPath = f"{main_directory}/__out"

# Global benford variable
p = 3
x = [i for i in range(1, 10)]
hist_bl = [benford(i) for i in x]
hist_percent = np.array(hist_bl) * 100
dMax = np.power(1 - hist_bl[0], p) + np.sum(np.power(hist_bl[1::], p))


def main(writeCsv=False):
    global outPath
    images = ['circle', 'square', 'triangle', 'sct']

    if writeCsv:
        # Define the headers for output csv
        headers = ["testName", "imageName", "minEvaluation", "iterations", "pointsMin", "pointsMax",
                   "numberOfInterpolationPoints", "populationSize",
                   "crossoverChance", "crossoverPoints", "mutationChance", "significantAlleles", "Mbl", "Mfd"]
        with open('ratings/output_mbl_mfd.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

    for imageName in images:
        print(crossoverTests(imageName)*3*7)
        print(mutationTests(imageName) * 3 * 7)
        print(crossoverPointsTests(imageName) * 3 * 7 - (1 * 10 * 3 * 7))
        print(pointsMinMaxTests(imageName)*3*7)

        print((crossoverTests(imageName)*3*7) + (mutationTests(imageName) * 3 * 7) + (crossoverPointsTests(imageName) * 3 * 7 - (1 * 10 * 3 * 7)) + (pointsMinMaxTests(imageName)*3*7))
        # benfordAndFractal(imageName)
        # deepCrossover(imageName)
        # print(imageName)
        break

    # agentsEvaluationAcrossIterations('deepCrossover', 'crossoverChance')


def deepCrossover(testImageName: str):
    config = getDefaultConfigFromFile()
    config["savingFreq"] = 2
    config["iterations"] = 200

    for i in range(0, 12):
        config["crossoverChance"] = 0.5 + 0.05 * i
        for j in range(10):
            baseTest(testImageName, config, f'deepCrossover_{config["crossoverChance"]}_{j}')


def getDefaultConfigFromFile():
    with open(f"{main_directory}/default_config.json", "r") as f:
        return json.load(f)


def crossoverTests(testImageName: str):
    config = getDefaultConfigFromFile()
    number = 0

    for i in range(0, 26):
        config["crossoverChance"] = 0.5 + 0.02 * i

        for j in range(10):
            number += 1
            # baseTest(testImageName, config, f'crossover_{config["crossoverChance"]}_{j}')
    return number


def mutationTests(testImageName: str):
    config = getDefaultConfigFromFile()
    number = 0

    for i in range(0, 201):
        config["mutationChance"] = 0.00005 * i

        for j in range(10):
            number += 1
            # baseTest(testImageName, config, f'mutation_{config["mutationChance"]}_{j}')
    return number


def pointsMinMaxTests(testImageName: str):
    config = getDefaultConfigFromFile()
    number = 0

    for i in range(10):
        for j in range(i, 10):
            config["pointsMinMax"] = [i, j]

            for k in range(10):
                number += 1
                # baseTest(testImageName, config, f'points_{config["pointsMinMax"]}_{k}')
    return number


def crossoverPointsTests(testImageName: str):
    config = getDefaultConfigFromFile()
    number = 0

    for i in range(10):
        config["crossoverPoints"] = i
        for j in range(10):
            number += 1
            # baseTest(testImageName, config, f'crossoverPoints_{config["crossoverPoints"]}_{j}')
    return number


def baseTest(testImageName: str, configValues: dict, prefix: str):
    outDir = '/Users/michalryngier/studia/praca-magisterska/art/__out'

    with open(f"{outDir}/{testImageName}/config.json", "w") as f:
        json.dump(configValues, f)

    # run genetic_algorithm.py with the given arguments
    subprocess.Popen(["python", "genetic_algorithm.py", testImageName, prefix]).wait()


def createImage(testImageName: str, version: str, minEvaluation: float):
    # run output_image_generator.py with the given arguments
    subprocess.Popen(
        ["python", "output_image_generator.py", testImageName, version, '1', f'{minEvaluation:.2f}', '1']).wait()


def removeImage(imagePath: str):
    # remove the image from images directory
    subprocess.Popen(["rm", imagePath]).wait()


def benfordAndFractal(testImageName: str):
    global outPath
    pattern = os.path.join(outPath, testImageName, "*", "*.json")
    paths = glob.glob(pattern)
    paths = [path for path in paths if not path.endswith('config.json')]
    minEvaluations = [0.0, 0.01, 0.05, 0.1, 0.5, 0.9, 1.0]

    for jsonFilePath in paths:
        imageDir = jsonFilePath.split("/")[-2]
        testName = imageDir.split("_")[0]
        if testName == "deepCrossover":
            continue

        for minEvaluation in minEvaluations:
            createImage(testImageName, imageDir, minEvaluation)
            imagePath = f"/Users/michalryngier/studia/praca-magisterska/art/__out/{testImageName}/{imageDir}/images-{minEvaluation}/0.png"

            benfordValue = evaluateBenfordForImage(imagePath)
            fractalValue = evaluateFractalDimension(imagePath)

            removeImage(imagePath)

            with open(f"{outPath}/{testImageName}/{imageDir}/config.json", "r") as f:
                config = json.load(f)

            values = [testName, testImageName, minEvaluation, config["iterations"], config["pointsMinMax"][0],
                      config["pointsMinMax"][1],
                      config["numberOfInterpolationPoints"], config["populationSize"], config["crossoverChance"],
                      config["crossoverPoints"], config["mutationChance"], config["significantAlleles"], benfordValue,
                      fractalValue]

            with open('ratings/output_mbl_mfd.csv', 'a', newline='') as csvFile:
                csvWriter = csv.writer(csvFile)
                formattedData = [f'{value:.8f}' if isinstance(value, float) else value for value in values]
                csvWriter.writerow(formattedData)
            print('Csv written')


def agentsEvaluationAcrossIterations(metricName: str, metricKey: str):
    global outPath
    folders = findDeepFolders(outPath, f"{metricName}_*")

    with open(f"{metricKey}_output.csv", 'w', newline='') as csvfile:
        fieldnames = ['imageName', 'metricKey', 'metricValue', 'agentEvaluation', 'iteration']
        csvWriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csvWriter.writeheader()

        for folder in folders:
            configJson = findConfigJsonInFolder(folder)
            with open(configJson, "r") as f:
                config = json.load(f)
            metricValue = config[metricKey]
            imageName = folder.split('/')[-2]

            stateAdapter = JsonMainAgentStateAdapter(folder, '', True)

            for i in range(int(config["iterations"] / config["savingFreq"]) + 1):
                for agent in stateAdapter.load(i):
                    csvWriter.writerow({
                        'imageName': imageName,
                        'metricKey': metricKey,
                        'metricValue': f'{metricValue:.8f}',
                        'agentEvaluation': f'{agent.getEvaluationValue():.8f}',
                        'iteration': i * config["savingFreq"]
                    })


def evaluateBenfordForImage(imagePath: str) -> float:
    global p, hist_bl, dMax

    img = cv.imread(imagePath)
    img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    hist = cv.calcHist([img], [0], None, [10], [0, 256])
    hist = (np.array(hist) / np.sum(hist))
    dTotal = np.sum(np.power(hist - hist_bl, p))

    return (dMax - dTotal) / dMax


def evaluateFractalDimension(imagePath: str) -> float:
    image = io.imread(imagePath)
    thresholdValue = 0.9
    fractalDim, sizes, counts = fractal_dimension(image, threshold=thresholdValue)

    return fractalDim


def findDeepFolders(rootDir: str, pattern: str) -> []:
    deepFolders = []
    for root, dirs, files in os.walk(rootDir):
        for dir_name in dirs:
            if fnmatch.fnmatch(dir_name, pattern):
                deepFolders.append(os.path.join(root, dir_name))
    return deepFolders


def findConfigJsonInFolder(folder: str) -> str | None:
    for root, dirs, files in os.walk(folder):
        for file_name in files:
            if file_name == 'config.json':
                return os.path.join(root, file_name)

    return None


if __name__ == "__main__":
    main(False)
