import math
import os
import subprocess
import sys
from pathlib import Path
from typing import List

import numpy as np
import matplotlib.pyplot as plt

from genetics.basics import Agent
from genetics.classes import JsonMainAgentStateAdapter, JsonReference

main_directory = Path(__file__).resolve().parent
outPath = f"{main_directory}/__out"


agentsPrinted = []

def main():
    if len(sys.argv) < 1:
        print("Usage: python output__image_generator.py [filepath] [version] [scale] [minEvaluation] [legacyMode]")
        sys.exit(1)

    filepath = str(sys.argv[1])
    version = str(sys.argv[2])
    scale = 1
    minEvaluation = 0.5
    legacyMode = False

    if len(sys.argv) > 3:
        scale = int(sys.argv[3])
    if len(sys.argv) > 4:
        minEvaluation = float(sys.argv[4])
    if len(sys.argv) > 5:
        legacyMode = bool(sys.argv[5])

    referencePath = f"{outPath}/{filepath}/reference.json"

    inputPath = ''
    if len(version) == 10:
        inputPath = f"{outPath}/{filepath}/__out_{version}"
    else:
        inputPath = f"{outPath}/{filepath}/{version}"

    stateAdapter = JsonMainAgentStateAdapter(inputPath, filepath, legacyMode)
    reference = JsonReference(referencePath)

    iterator = 0
    agents = stateAdapter.load(iterator)
    imagePaths = []

    imagesPath = f"{inputPath}/images-{str(minEvaluation)}"
    if not os.path.exists(imagesPath):
        os.makedirs(imagesPath)

    while len(agents) > 0:
        print(iterator)
        imagePath = f"{imagesPath}/{iterator}.png"
        width = reference.xMax() * scale
        height = reference.yMax() * scale

        image = createImage(width, height, agents, minEvaluation, scale)

        dpi = 300
        plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        plt.imshow(image, extent=(0, width, 0, height))
        plt.axis('off')
        # plt.show()
        plt.savefig(imagePath, format='png', transparent=True, bbox_inches='tight', pad_inches=0)
        plt.close()

        imagePaths.append(imagePath)

        iterator += 1
        agents = stateAdapter.load(iterator)

    # Create gif
    if len(imagePaths) > 2:
        image_files = sorted([f for f in os.listdir(imagesPath) if f.endswith('.png')],
                             key=lambda x: int(os.path.splitext(x)[0]))

        cmd = [
            "convert",
            "-delay", str(10),
            "-loop", str(0),
        ]

        # Add image filenames to the command
        cmd.extend([f"{imagesPath}/{filename}" for filename in image_files])

        cmd.extend([
            "-alpha", "set",
            f"{inputPath}/result-{minEvaluation}.gif"
        ])

        # Run the command
        subprocess.run(cmd)

    with open(f'{imagesPath}/agentsPrinted-{str(minEvaluation)}.csv', 'w') as file:
        file.write("Index, Agents\n")
        for i in range(0, len(agentsPrinted)):
            index = i
            agents = agentsPrinted[i]
            file.write(f"{index}, {agents}\n")


def createImage(width: int, height: int, agents: List[Agent], minEvaluation: float = .0, scale: int = 1):
    image = np.zeros((height, width, 4), dtype=np.uint8)
    image[:, :, :3] = 255
    image[:, :, 3] = 255

    agentsPrintedInIteration = 0

    for agent in agents:
        color = (0, 0, 0, 255)
        step = agent.getStep()
        arrange = np.arange(0, 1 + step, step)
        points = []

        if agent.getEvaluationValue() < minEvaluation:
            continue

        agentsPrintedInIteration += 1
        for t in arrange:
            point = agent.getPointForT(t)
            points.append(point)

        threshold = agent.getThreshold()
        threshold = math.floor((threshold * scale) / 2)

        maxDistance = threshold * math.sqrt(2)

        for point in points:
            x, y = point.getX() * scale, point.getY() * scale
            xMin, xMax, yMin, yMax = max(0, x - threshold), min(width, x + threshold + 1), max(0, y - threshold), min(
                height, y + threshold + 1)

            for yy in range(yMin, yMax):
                for xx in range(xMin, xMax):
                    alpha = 255
                    distance = math.sqrt((x - xx) ** 2 + (y - yy) ** 2)

                    if distance > 0:
                        alpha = int(calculateAlpha(distance, maxDistance))

                    image[yy][xx] = (color[0], color[1], color[2], alpha)
    agentsPrinted.append(agentsPrintedInIteration)

    return image


def calculateAlpha(distance: float, maxDistance: float) -> int:
    minAlpha = 5
    maxAlpha = 255
    alpha = max(minAlpha, int(maxAlpha - ((distance / maxDistance) * (maxAlpha - minAlpha))))

    return int(alpha)


if __name__ == "__main__":
    main()
