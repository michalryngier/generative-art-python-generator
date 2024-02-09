import json
from pathlib import Path
from typing import List

import numpy as np
from skimage import io, color, feature, exposure
from skimage.filters import gaussian
from skimage.util import img_as_ubyte


class EdgeMatrixCreator:
    __imagePath: Path
    __outputPath: Path

    def __init__(self, imagePath: Path, outputPath: Path):
        self.__imagePath = imagePath
        self.__outputPath = outputPath

    def createEdgeMatrix(self, cannySigma: float, blur: bool, blurSigma: float):
        image = io.imread(self.__imagePath)

        if image.ndim == 3:
            image = color.rgb2gray(image)

        edges = feature.canny(image, sigma=cannySigma)

        if blur:
            edges = gaussian(edges, sigma=blurSigma)

        edges = edges / np.max(edges)
        edges[edges >= 0.25] = 1

        io.imsave(self.__outputPath, img_as_ubyte(edges))

    def createReferenceJson(self, path: Path):
        image = io.imread(self.__outputPath)
        height, width = image.shape[:2]

        referenceData: List[List[float]] = []

        for row in image:
            columnValues = []
            for column in row:
                bwValue = column / 255
                columnValues.append(bwValue)
            referenceData.append(columnValues)

        with open(path, 'w') as jsonFile:
            json.dump({"xMax": width, "yMax": height, "pointsValues": referenceData}, jsonFile)
