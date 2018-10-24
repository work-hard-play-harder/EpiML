from bokeh.models import HoverTool, FactorRange, Range1d
from bokeh.plotting import figure
from bokeh.palettes import d3

import numpy as np
from sklearn import linear_model, decomposition, datasets

from bokeh.util.string import encode_utf8

import rpy2.robjects as robjects
from rpy2.robjects.packages import importr


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


def create_lasso_figure(fit_file):
    # import r library
    glmnet = importr('glmnet')

    TOOLS = "crosshair,pan,wheel_zoom,box_zoom,reset,box_select,lasso_select,hover"
    # load lasso fit model
    robjects.r['load'](fit_file)
    fit = robjects.r['fit']

    lasso_lambda = fit[4]
    lasso_lambda = np.log(np.array(lasso_lambda))
    print(lasso_lambda)

    # first using 'as.matrix' function convert RS4 class to a matrix
    lasso_beta = fit[1]
    lasso_beta = np.array(robjects.r['as.matrix'](lasso_beta))
    print(lasso_beta[0])

    plot = figure(tools=TOOLS,
                  title='LASSO coefficients',
                  x_axis_label='Log Lambda',
                  y_axis_label='Coefficients',
                  plot_width=500,
                  plot_height=500)

    colors = d3['Category20'][20]
    for i, color in zip(range(20), colors):
        plot.line(lasso_lambda, lasso_beta[i], color=color)
    return plot
