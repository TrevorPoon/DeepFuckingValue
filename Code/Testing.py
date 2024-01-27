import pandas as pd
import numpy as np
import matplotlib as mat

np.random.seed(24)
df = pd.DataFrame({'A': np.linspace(1, 10, 10)})
df = pd.concat([df, pd.DataFrame(np.random.randn(10, 4), columns=list('BCDE'))],
               axis=1)
df.iloc[0, 2] = np.nan

cm = mat.colormaps.get_cmap('RdYlGn')

s = df.style.background_gradient(cmap=cm)
print(s)