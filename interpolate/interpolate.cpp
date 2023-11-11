#include <vector>

extern "C" {
    std::vector<double> interpolate(double t, std::vector<std::vector<double> > points) {
        if (t == 0) {
            return points[0];
        }
        int order = points.size() - 1;
        if (t == 1) {
            return points[order];
        }
        double mt = 1 - t;
        std::vector<std::vector<double>> p = points;
        // linear curve
        if (order == 1) {
            return {
                mt * p[0][0] + t * p[1][0],
                mt * p[0][1] + t * p[1][1]
            };
        }
        // quadratic or cubic curve
        if (order >= 2 && order < 4) {
            double mt2 = mt * mt;
            double t2 = t * t;
            double a, b, c, d = 0;
            if (order == 2) {
                p = {p[0], p[1], p[2], {0, 0}};
                a = mt2;
                b = mt * t * 2;
                c = t2;
            } else {
                a = mt2 * mt;
                b = mt2 * t * 3;
                c = mt * t2 * 3;
                d = t * t2;
            }
            return {
                a * p[0][0] + b * p[1][0] + c * p[2][0] + d * p[3][0],
                a * p[0][1] + b * p[1][1] + c * p[2][1] + d * p[3][1]
            };
        }
        // Higher order curves - use de Casteljau's computation.
        std::vector<std::vector<double> > dCpts = points;
        while (dCpts.size() > 1) {
            for (int i = 0; i < dCpts.size() - 1; i++) {
                dCpts[i] = {
                    dCpts[i][0] + (dCpts[i + 1][0] - dCpts[i][0]) * t,
                    dCpts[i][1] + (dCpts[i + 1][1] - dCpts[i][1]) * t
                };
            }
            dCpts.pop_back();
        }
        return dCpts[0];
    }
}
