import csv

import pandas as pd

testsForImage = 10
populationSize = 1600
iterations = 200
savingFreq = 2
numberOfResults = int(iterations / savingFreq) + 1

chunk_size = populationSize * numberOfResults
headers = ['imageName', 'metricKey', 'metricValue', 'agentEvaluation', 'iteration']
chunks = pd.read_csv('crossoverChance_output.csv', chunksize=chunk_size, delimiter=',', names=headers, header=None)

valuesPerImage = {}

evals = [0.1, 0.5, 0.75, 1.0]

# Write headers to csv as kes_crossover_postprocessed.csv
with open('kes_crossover_postprocessed.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['imageName', 'metricValue', 'iteration', 'evalValue', 'count'])

csvRows = []
imageNames = []
iterations = []
metricValues = []

for chunk in chunks:
    imageName = chunk['imageName'].iloc[0]
    imageNames.append(imageName)

    metricValue = chunk['metricValue'].iloc[0]
    metricValues.append(metricValue)

    if imageName not in valuesPerImage:
        valuesPerImage[imageName] = {}

    if metricValue not in valuesPerImage[imageName]:
        valuesPerImage[imageName][metricValue] = {}

    for _, row in chunk.iterrows():  # Iteracja przez wiersze w chunku
        agentEvaluation = row['agentEvaluation']
        iteration = (row['iteration'] - 1) * 2

        if iteration not in valuesPerImage[imageName][metricValue]:
            valuesPerImage[imageName][metricValue][iteration] = {}

            if iteration not in iterations:
                iterations.append(iteration)

        for evalValue in evals:
            evalKey = f'{evalValue}'
            if evalKey not in valuesPerImage[imageName][metricValue][iteration]:
                valuesPerImage[imageName][metricValue][iteration][evalKey] = 0

            if agentEvaluation >= evalValue:
                valuesPerImage[imageName][metricValue][iteration][evalKey] += 1
    print('All rows of chunk processed')

imageNames = list(set(imageNames))
imageNames.sort()

iterations = list(set(iterations))
iterations.sort()

metricValues = list(set(metricValues))
metricValues.sort()

for imageName in imageNames:
    for metricValue in metricValues:
        for iteration in iterations:
            for evalValue in evals:
                csvRows.append([imageName, metricValue, iteration, evalValue,
                                (valuesPerImage[imageName][metricValue][iteration][
                                     f'{evalValue}'] / testsForImage)])

with open('kes_crossover_postprocessed.csv', 'a', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(csvRows)

print('End')
