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
    if len(sys.argv) < 5:
        print(
            "Usage: python single_output__image_generator.py [inputPath] [stateFilePath] [fgColor] [bgColor] [minEvaluation]")
        sys.exit(1)

    inputPath = str(sys.argv[1])
    stateFilePath = str(sys.argv[2])
    fgColor = hex_to_rgba(str(sys.argv[3]))
    bgColor = hex_to_rgba(str(sys.argv[4]))
    minEvaluation = float(sys.argv[5])

    filepath = 'window_image'
    scale = 1

    referencePath = f"{os.path.dirname(inputPath)}/reference.json"

    stateAdapter = JsonMainAgentStateAdapter(inputPath, filepath)
    reference = JsonReference(referencePath)

    agents = stateAdapter.loadByStatePath(stateFilePath)
    imagesPath = f"{inputPath}/images-generated"

    if not os.path.exists(imagesPath):
        os.makedirs(imagesPath)

    imagePath = f"{imagesPath}/{os.path.basename(stateFilePath).split('.')[0]}.png"
    width = reference.xMax() * scale
    height = reference.yMax() * scale

    image = createImage(width, height, agents, minEvaluation, bgColor, fgColor, scale)

    dpi = 300
    plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.imshow(image, extent=(0, width, 0, height))
    plt.axis('off')
    # plt.show()
    plt.savefig(imagePath, format='png', transparent=True, bbox_inches='tight', pad_inches=0)
    plt.close()

    return 0


def createImage(
        width: int,
        height: int,
        agents: List[Agent],
        minEvaluation: float = .0,
        bgColor: tuple = (0, 0, 0, 255),
        fgColor: tuple = (255, 255, 255, 255),
        scale: int = 1
):
    image = np.full((height, width, 4), bgColor, dtype=np.uint8)
    agentsPrintedInIteration = 0

    for agent in agents:
        color = fgColor
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


def hex_to_rgba(hex_color: str):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    rgba = rgb + (255,)

    return rgba


if __name__ == "__main__":
    main()
