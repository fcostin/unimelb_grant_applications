import pickle
import numpy

def cosine_similarity(x, y):
    mask = numpy.logical_not(numpy.logical_or(x.mask, y.mask))
    mask_weight = numpy.sum(mask) / float(len(mask))
    x = numpy.array(x[mask], dtype = numpy.float64)
    y = numpy.array(y[mask], dtype = numpy.float64)
    raw_score = numpy.abs(numpy.dot(x, y)) / (numpy.linalg.norm(x) * numpy.linalg.norm(y))
    return mask_weight * raw_score

def get_cols():
    return pickle.load(open('../gen/cols.pickle', 'rb'))

def main():
    cols = get_cols()
    target_name = 'Grant.Status'
    score = {}
    for name in cols:
        try:
            col = cols[name]
            theta = cosine_similarity(col, cols[target_name])
            score[name] = theta
        except ValueError:
            pass

    score_i = score.items()
    # sorting fails hilariously if nans included since they are incomparable
    score_i = [(k, v) for (k, v) in score_i if numpy.isfinite(v)]
    score_i.sort(key = lambda (k, v) : v)
    for name, score in score_i:
        print '%s\t%.3f' % (name, score)

    names = cols.keys()
    names.sort()

    sim = {}
    for name_i in names:
        print name_i
        try:
            x = float(cols[name_i][0])
        except ValueError:
            continue
        for name_j in names:
            if name_i >= name_j:
                continue
            try:
                x = float(cols[name_j][0])
            except ValueError:
                continue
            try:
                sim[(name_i, name_j)] = cosine_similarity(
                    cols[name_i],
                    cols[name_j]
                )
            except ValueError:
                pass
    pickle.dump(sim, open('sim-matrix.pickle', 'wb'))

if __name__ == '__main__':
    main()

