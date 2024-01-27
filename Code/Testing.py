from bokeh.io import curdoc
from bokeh.plotting import figure, output_file, show

x = [1, 2, 3, 4, 5]
y = [6, 7, 6, 4, 5]

output_file("dark_minimal.html")

curdoc().theme = 'dark_minimal'

p = figure(title='dark_minimal', width=300, height=300)
p.line(x, y)

show(p)