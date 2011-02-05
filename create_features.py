import numpy
import pickle
import glob
import os

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

def main():
    cols = unpickle('gen/cols.pickle')
    fmts = unpickle('gen/fmts.pickle')
    edges = unpickle('gen/edges-grants-with-min-1-shared-applicants.pickle')

    suffix = '.Rdata'
    rdata_files = glob.glob(os.path.join(rdata_path, '*.Rdata'))
    rdata_cols = [os.path.splitext(os.path.basename(name))[0] for name in rdata_files]

    reduce_funcs = {
        'min' : numpy.min,
        'mean' : numpy.mean,
        'max' : numpy.max,
    }

    valid_dtype = lambda x : issubclass(x, numpy.number) or issubclass(x, numpy.bool)

    new_cols = {}
    new_fmts = {}
    for grant_status in (True, False):
        predicate = grant_status_predicate(cols, grant_status)
        filtered_edges = list(gen_filtered_edges(edges, predicate))
        for col_name in sorted(rdata_cols):
            col = cols[col_name]
            fmt = fmts[col_name]
            _, vartype = fmt
            if fmt == 'factor':
                continue
            if not valid_dtype(col.dtype.type):
                continue
            for reduce_name in reduce_funcs:
                reduce = reduce_funcs[reduce_name]
                x = numpy.ma.zeros(col.shape, dtype = col.dtype)
                for i, filtered_js in filtered_edges:
                    x[i] = reduce(col[filtered_js])
                feature_name = 'derived.%s.%s.%s' % (grant_status, reduce_name,col_name)
                new_cols[feature_name] = x
                new_fmts[feature_name] = fmt
                print 'created %s' % feature_name

    write_cols_to_r_binary_files(
        new_cols,
        new_fmts,
        dump_dir = 'gen/rdata_train_new_features',
    )

if __name__ == '__main__':
    main()
