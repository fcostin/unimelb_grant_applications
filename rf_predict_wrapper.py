import numpy
import rpy2.robjects
import rpy2.robjects.numpy2ri

R_SOURCE_FILE = 'rf_predict.r'
R_FUNCTION_NAME = 'test.predictive.accuracy'

def rf_predict(*args, **kwargs):
    """
    wraps test.predictive.accuracy function from rf_predict.r

    arguments:
        rdata.dir
        max.na.fraction (default 0.95)
        test.frac       (default 1.0/3.0)
        n.trees         (default 50)
        n.procs         (default 2)
        test.indices    (default NULL)

    value:
        (importance, mse)

        where importance is a dict of variable importance scores (Gini)
        and mse is the mean squared error on the test set.
    """

    r = rpy2.robjects.r
    r_source = open(R_SOURCE_FILE)
    r(r_source.read())
    r_source.close()
    results = r[R_FUNCTION_NAME](*args, **kwargs)
    importance = dict(results[0].iteritems())
    mse = results[1][0]
    return (importance, mse)
