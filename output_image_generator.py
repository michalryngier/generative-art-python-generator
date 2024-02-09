import os
import sys
from pathlib import Path
from typing import List
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt  # Added import
from genetics.basics import Agent
from genetics.classes import JsonMainAgentStateAdapter, JsonReference

main_directory = Path(__file__).resolve().parent
outPath = f"{main_directory}/__out"


def main():
    if len(sys.argv) < 1:
        print("Usage: python output__image_generator.py [filepath] [version]")
        sys.exit(1)

    filepath = str(sys.argv[1])
    # version = str(sys.argv[2])
    version = '1707425462'
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
        width = reference.xMax()
        height = reference.yMax()

        minEvaluation = 0.00001
        image = createImage(width, height, agents, minEvaluation)

        aspect_ratio = width / height
        plt.figure(figsize=(10, 10 / aspect_ratio))

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        plt.imshow(image, extent=(0, width, 0, height))
        plt.axis('off')
        # plt.show()
        plt.savefig(imagePath)
        plt.close()

        images.append(Image.open(imagePath))

        iterator += 1
        agents = stateAdapter.load(iterator)

    images[0].save(f"{inputPath}/result.gif",
                   save_all=True,
                   append_images=images[1:],
                   duration=50,
                   loop=0)


def createImage(width: int, height: int, agents: List[Agent], minEvaluation: float = .0):
    image = np.zeros((height, width, 4), dtype=np.uint8)
    image[:, :, :3] = 0
    image[:, :, 3] = 255

    for agent in agents:
        # agent.setStep(0.001)
        color = (255, 255, 255, 255)
        step = agent.getStep()
        arrange = np.arange(0, 1 + step, step)
        if agent.getEvaluationValue() <= minEvaluation:
            continue
        for t in arrange:
            point = agent.getPointForT(t)
            if point.getX() >= width or point.getY() >= height:
                continue

            image[point.getY()][point.getX()] = color

    return image


if __name__ == "__main__":
    main()
