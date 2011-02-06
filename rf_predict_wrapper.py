import numpy
import rpy2.robjects
import rpy2.robjects.numpy2ri

R_SOURCE_FILE = 'rf_predict.r'
R_FUNCTION_NAME = 'test.predictive.accuracy'

def _wrapped_r_call(source_file_name, function_name, *args, **kwargs):
    r = rpy2.robjects.r
    r_source = open(source_file_name)
    r(r_source.read())
    r_source.close()
    return(r[function_name](*args, **kwargs))

def rf_predict_multiproc(*args, **kwargs):
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
        (importance_gini, mse)

        where importance is a dict of variable importance scores (Gini)
        and mse is the mean squared error on the test set.
    """

    results = _wrapped_r_call(
        'rf_predict.r',
        'test.predictive.accuracy',
        *args,
        **kwargs
    )
    results = r[R_FUNCTION_NAME](*args, **kwargs)
    importance_gini = dict(results[0].iteritems())
    mse = results[1][0]
    return (importance_gini, mse)

def rf_predict_uniproc(*args, **kwargs):
    """
    wraps test.predictive.accuracy function from rf_predict_uniproc.r

    arguments:
        rdata.dir
        max.na.fraction (default 0.95)
        test.frac       (default 1.0/3.0)
        n.trees         (default 50)
        test.indices    (default None)
        draw.plots      (default False)

    value:
        (importance_mse, importance_gini, test_mse)

        where the importances are dicts of oob mse and gini scores per
        variable, and test.mse is the mean squared error on the test set.
    """

    results = _wrapped_r_call(
        'rf_predict_uniproc.r',
        'test.predictive.accuracy.uniproc',
        *args,
        **kwargs
    )
    importance_mse = dict(results[0].iteritems())
    importance_gini = dict(results[1].iteritems())
    train_mse = results[1][0]
    return (importance_mse, importance_gini, train_mse)

