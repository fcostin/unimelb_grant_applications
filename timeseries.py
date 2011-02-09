import numpy
import scipy
import pickle
import glob
import os
import pylab
import rpy2
import rpy2.robjects
import rpy2.robjects.numpy2ri

from butcher_data import write_cols_to_r_binary_files

def unpickle(file_name):
    f = open(file_name, 'rb')
    p = pickle.load(f)
    f.close()
    return p

def gen_filtered_edges(edges, predicate):
    for i, predecessors in enumerate(edges):
        if not predecessors:
            continue
        filtered_js = [j for j in predecessors if predicate(i, j)]
        if not filtered_js:
            continue
        yield i, filtered_js

def grant_status_predicate(cols, status):
    return lambda _, j : cols['Grant.Status'][j] == status

rdata_path = 'gen/rdata_train_base'

def predict_logistic(y_name, train, test, factors = None):
    rpy2.robjects.r("""
        make_logit_prediction <- function(response_name, df_train, df_test) {
            f <- as.formula(paste(response_name, '~', '.', sep = ' '))
            options(warn=2)
            logit.fit <- glm(f, df_train, family = binomial(link = 'logit'))
            prediction <- predict(logit.fit, df_test, type = 'response')
            return(prediction)
        }
    """)

    if factors is None:
        factors = set()

    factor_levels = {}
    for name in factors:
        factor_levels[name] = set(train.get(name, [])).union(set(test.get(name, [])))

    # R chucks a hissy fit if a factor only has one level
    bad_factors = set()
    for name in factors:
        if name == y_name:
            continue
        col = train[name]
        if len(set(col)) == 1:
            bad_factors.add(name)

    for name in bad_factors:
        del train[name]
        del test[name]

    def as_data_frame(d):
        dd = {}
        for name in d:
            if name in factors:
                dd[name] = rpy2.robjects.FactorVector(
                    rpy2.robjects.StrVector(d[name]),
                    levels = rpy2.robjects.StrVector(list(factor_levels[name]))
                )
            else:
                dd[name] = rpy2.robjects.FloatVector(d[name])
        return rpy2.robjects.DataFrame(dd)
    try:
        prediction = rpy2.robjects.r['make_logit_prediction'](
            y_name,
            as_data_frame(train),
            as_data_frame(test),
        )
        prediction = float(prediction[0])
    except rpy2.rinterface.RRuntimeError:
        prediction = 0.5
    return prediction

def make_logit_prediction(min_shared_applicants, predictors, response_name):
    cols = unpickle('gen/cols.pickle')
    edges_file_name = 'gen/edges-grants-with-min-%d-shared-applicants.pickle' % min_shared_applicants
    edges = unpickle(edges_file_name)

    cols['Contract.Value.Midpoint'] = unpickle('gen/Contract.Value.Midpoint.pickle')

    suffix = '.Rdata'
    rdata_files = glob.glob(os.path.join(rdata_path, '*.Rdata'))
    rdata_cols = [os.path.splitext(os.path.basename(name))[0] for name in rdata_files]

    valid_dtype = lambda x : issubclass(x, numpy.number) or issubclass(x, numpy.bool)

    predicate = lambda i, j : True
    filtered_edges = list(gen_filtered_edges(edges, predicate))


    selected_col_names = [response_name] + predictors
    all_factors = set(
        [
            'Grant.Status',
        ]
    )
    factors = []
    for name in all_factors:
        if name in selected_col_names:
            factors.append(name)
    factors = set(factors)

    errors = []
    predictions = {}
    for i, filtered_js in filtered_edges:
        selected_cols = {}
        for name in selected_col_names:
            selected_cols[name] = cols[name][filtered_js]

        selected_col_masks = [x.mask for x in selected_cols.itervalues()]
        nothing_missing_mask = numpy.logical_not(
            numpy.any(
                selected_col_masks,
                axis = 0
            )
        )
        for name in selected_cols:
            selected_cols[name] = selected_cols[name][nothing_missing_mask]

        df_train = selected_cols
        df_test = {}
        for name in df_train:
            df_test[name] = [cols[name][i]]
        if any((v is numpy.ma.masked) or not numpy.isfinite(v) for v in df_test.values()):
            continue

        if len(df_train.values()[0]) < 2:
            continue

        predicted_status = predict_logistic(
            response_name,
            df_train,
            df_test,
            factors
        )
        error = numpy.abs(predicted_status - df_test[response_name][0])
        errors.append(error)
        print '%d; error : %f' % (i, error)
        predictions[i] = predicted_status

    n = len(cols[response_name])
    predictions_col = numpy.zeros(n, dtype = numpy.float)
    for i in xrange(n):
        if i in predictions:
            predictions_col[i] = predictions[i]
        else:
            predictions_col[i] = 0.5

    pylab.figure()
    pylab.title('min shared applicants : %d; predictors %s' % (min_shared_applicants, str(predictors)))
    pylab.hist(errors, bins = 15)


    name = 'Logit.Prediction.%s.SharApp.%d' % ('.'.join(predictors), min_shared_applicants)
    new_fmtcols = {
        name : (('float', 'numeric'), predictions_col)
    }
    return new_fmtcols

def main():
    new_cols = {}
    new_fmts = {}

    for i in xrange(1, 3 + 1):
        for predictors in [['Start.date'], ['Contract.Value.Midpoint'], ['Start.date', 'Contract.Value.Midpoint']]:
            new_fmtcols = make_logit_prediction(
                min_shared_applicants = i,
                predictors = predictors,
                response_name = 'Grant.Status'
            )
            for name in new_fmtcols:
                new_fmts[name], new_cols[name] = new_fmtcols[name]


    pylab.show()

    write_cols_to_r_binary_files(
        new_cols,
        new_fmts,
        dump_dir = 'gen/rdata_train_handcrafted_features/',
    )

if __name__ == '__main__':
    main()
