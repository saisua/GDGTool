import plotly
from plotly import graph_objects as go
import pickle

with open("data.pkl", 'rb') as f:
    (xs, ys, ns) = pickle.load(f)

fig = go.Figure()

for x, y, n in zip(xs, ys, ns):
    fig.add_scatter(x=x, y=y, name=n, mode="markers+lines")

fig.show()