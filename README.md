# Steps to run
1. Compile interpolate.cpp:
```bash
g++ -shared -O3 -std=c++17 -o ./image/interpolate/interpolate.so -fPIC ./image/interpolate/interpolate.cpp 
```
2. Add input image and config.json under `/__out` directory. See `/__out/example`:
   
   - Meaning of some settings in a json file:
      - **iterations** - number of iterations
      - **savingFreq** - save result every n-th iteration,
      - **crossoverPoints** - how many points will be crossover done in
      - **pointsMinMax** - minimum and maximum inner points for a bezier curve
      - **thresholdMinMax** - minimum and maximum threshold (thickness) for a bezier curve
      - **numberOfInterpolationPoints** - how many points in bezier curves will be interpolated
      - **alleleLength** - how many bits represent a single value
      - **startingPositionRadius** - a radius of initial agent points positioning relative to the starting point,
      - **significantAlleles** - how many alleles (bits) of each "gene" (alleleLength long) can be mutated
3. Generate edge matrix (reference):
    ```bash
    python reference_generator.py [filepath] [?cannySigma] [?blurSigma]
    ```
    **Example:**
      ```bash
    python reference_generator.py "example/example.jpg" 3 0.5
    ```
4. Run genetic algorithm:
    ```bash
    python genetic_algorithm.py [filename]
    ```
    **Example:**
      ```bash
    python genetic_algorithm.py "example"
    ```
5. Generate output images:
    ```bash
    python output__image_generator.py [filepath] [version] [scale] [minEvaluation] [legacyMode]
    ```
   **Example:**
    ```bash
    python output__image_generator.py "example" "1707425462" 2 0.0 0
    ```
   `version` is the timestamp of the `__out_{timestamp}` dictionary created under `/__out/example/`.