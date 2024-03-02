import math
import os
import sys
from pathlib import Path
from typing import List

import imageio.v2 as imageio
import numpy as np
import matplotlib.pyplot as plt  # Added import
from genetics.basics import Agent, Point
from genetics.classes import JsonMainAgentStateAdapter, JsonReference

main_directory = Path(__file__).resolve().parent
outPath = f"{main_directory}/__out"


def main():
    if len(sys.argv) < 1:
        print("Usage: python output__image_generator.py [filepath] [version] [scale] [threshold]")
        sys.exit(1)

    filepath = str(sys.argv[1])
    version = str(sys.argv[2])
    scale = 1
    threshold = None
    if len(sys.argv) > 3:
        scale = int(sys.argv[3])
    if len(sys.argv) > 4:
        threshold = int(sys.argv[4])

    referencePath = f"{outPath}/{filepath}/reference.json"
    inputPath = f"{outPath}/{filepath}/__out_{version}"

    stateAdapter = JsonMainAgentStateAdapter(inputPath, filepath)
    reference = JsonReference(referencePath)

    iterator = 0
    agents = stateAdapter.load(iterator)
    images = []

    imagesPath = f"{inputPath}/images"
    if not os.path.exists(imagesPath):
        os.makedirs(imagesPath)

    while len(agents) > 0:
        print(iterator)
        imagePath = f"{imagesPath}/{iterator}.png"
        width = reference.xMax() * scale
        height = reference.yMax() * scale

        minEvaluation = 0.00001
        image = createImage(width, height, agents, minEvaluation, scale, threshold)

        dpi = 300
        plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        plt.imshow(image, extent=(0, width, 0, height))
        plt.axis('off')
        # plt.show()
        plt.savefig(imagePath, format='png', transparent=True, bbox_inches='tight', pad_inches=0)
        plt.close()

        images.append(imagePath)

        iterator += 1
        agents = stateAdapter.load(iterator)

    with imageio.get_writer(f"{inputPath}/result.gif", mode="I") as writer:
        for png_file in images:
            image = imageio.imread(png_file)
            writer.append_data(image)


def createImage(width: int, height: int, agents: List[Agent], minEvaluation: float = .0, scale: int = 1, threshold: int = None):
    image = np.zeros((height, width, 4), dtype=np.uint8)
    image[:, :, :3] = 0
    image[:, :, 3] = 255

    threshold = None if threshold is None else (threshold * scale)

    for agent in agents:
        color = (255, 255, 255, 255)
        step = agent.getStep()
        arrange = np.arange(0, 1 + step, step)
        points = []

        if agent.getEvaluationValue() <= minEvaluation:
            continue

        for t in arrange:
            point = agent.getPointForT(t)
            points.append(point)

        threshold = (agent.getThreshold() * scale) if threshold is None else threshold
        maxDistance = threshold * math.sqrt(2)

        points = [Point(point.getX() * scale, point.getY() * scale) for point in points]

        for point in points:
            x, y = point.getX(), point.getY()
            for yy in range(y - threshold, y + threshold + 1):
                for xx in range(x - threshold, x + threshold + 1):
                    if xx >= width or yy >= height or xx < 0 or yy < 0:
                        continue

                    alpha = 255
                    distance = math.sqrt((x - xx) ** 2 + (y - yy) ** 2)

                    if distance > 0:
                        alpha = int(calculateAlpha(distance, maxDistance))

                    image[yy][xx] = (color[0], color[1], color[2], alpha)

    return image


def calculateAlpha(distance: float, maxDistance: float) -> int:
    minAlpha = 5
    maxAlpha = 255
    alpha = max(minAlpha, int(maxAlpha - ((distance / maxDistance) * (maxAlpha - minAlpha))))

    return int(alpha)


if __name__ == "__main__":
    main()
