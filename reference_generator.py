import sys
from pathlib import Path

from image.reference_image import EdgeMatrixCreator

main_directory = Path(__file__).resolve().parent
outPath = f"{main_directory}/__out"


def main():
    if len(sys.argv) < 2:
        print("Usage: python reference_generator.py filepath")
        sys.exit(1)

    # Required
    filepath = str(sys.argv[1])

    # Optional
    cannySigma = 3.5
    blur = True
    blurSigma = 1
    try:
        cannySigma = float(sys.argv[2])
        blur = bool(sys.argv[3])
        blurSigma = float(sys.argv[3])
    except IndexError:
        pass

    inputPath = f"{outPath}/{filepath}"

    name, extension = filepath.split(".")
    outputFilepath = f"{name}_em.{extension}"
    outputPath = f"{outPath}/{outputFilepath}"

    dirName = filepath.split("/")
    referenceOutputPath = f"{outPath}/{dirName[0]}/reference.json"

    directoryPath = Path(inputPath)

    if not directoryPath.exists() or not directoryPath.is_file():
        print(f"Not a file {outPath}/{filepath}")
        sys.exit(1)

    referenceGenerator = EdgeMatrixCreator(Path(inputPath), Path(outputPath))
    referenceGenerator.createEdgeMatrix(cannySigma, blur, blurSigma)
    referenceGenerator.createReferenceJson(Path(referenceOutputPath))


if __name__ == "__main__":
    main()
