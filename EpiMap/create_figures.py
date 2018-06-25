from bokeh.models import HoverTool, FactorRange, Range1d
from bokeh.plotting import figure

import numpy as np
from sklearn import linear_model, decomposition, datasets

from bokeh.util.string import encode_utf8


def create_pca_figure(x, y):
    TOOLS = "crosshair,pan,wheel_zoom,box_zoom,reset,box_select,lasso_select,hover"

    digists = datasets.load_digits()
    X_digists = digists.data
    Y_digists = digists.target

    pca = decomposition.PCA()
    pca.fit(X_digists)
    x = range(len(pca.explained_variance_))
    y = pca.explained_variance_

    plot = figure(tools=TOOLS,
                  title='PCA example',
                  x_axis_label='n_components',
                  y_axis_label='explained_variance_')

    plot.line(x, y, legend='PCA', line_width=2)

    return plot
