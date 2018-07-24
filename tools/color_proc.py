import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline

model = Pipeline([('poly', PolynomialFeatures(degree=2)),
                  ('linear', LinearRegression(fit_intercept=False))])

X = np.arange(0, 1.01, 0.01).reshape(1,-1).T

df = pd.read_csv(sys.argv[1], header=None)
Y1 = df.iloc[:,0]
Y2 = df.iloc[:,1]
Y3 = df.iloc[:,2]

model.fit(X, Y1)
r = model.named_steps['linear'].coef_
model.fit(X, Y2)
g = model.named_steps['linear'].coef_
model.fit(X, Y3)
b = model.named_steps['linear'].coef_

print "int((%f - %f*x + %f*x*x)*127)," % (r[0], r[1], r[2])
print "int((%f - %f*x + %f*x*x)*127)," % (g[0], g[1], g[2])
print "int((%f - %f*x + %f*x*x)*127)"  % (b[0], b[1], b[2])
