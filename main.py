import numpy
import glob
import os
import pickle
import itertools

from rf_predict_wrapper import rf_predict_uniproc as rf

def plot_stuff(imp_mse, imp_gini):
    import pylab
    x = numpy.asarray(imp_mse.values())
    y = numpy.asarray(imp_gini.values())
    pylab.figure()
    pylab.scatter(x, y)
    for name_i in imp_mse:
        x_i = imp_mse[name_i]
        y_i = imp_gini[name_i]
        pylab.text(x_i, y_i, name_i)
    pylab.xlabel('mse')
    pylab.ylabel('gini')
    pylab.show()

def run_experiment(rdata_path, selected_vars):
    imp_mse, imp_gini, test_mse = rf(
        rdata_path,
        selected_vars,
        n_trees = 50
    )
    return (imp_mse, imp_gini, test_mse)


def min_weight():
    return 0.05

def make_initial_weights(all_vars):
    var_weights = {}
    for var in all_vars:
        var_weights[var] = [min_weight()]
    return var_weights

def compress_weights(var_weights):
    weights = {}
    for var in var_weights:
        weights[var] = max(
            numpy.mean(var_weights[var]),
            min_weight()
        )
    return weights

def choose_vars(weights, n_vars):
    names, weights = zip(*weights.items())
    names = list(names)
    weights = list(weights)
    net_weight = sum(weights)
    chosen_vars = []
    while len(chosen_vars) < n_vars:
        # pick a variable according to the current weights
        cumulative = numpy.add.accumulate(weights)
        x = numpy.random.uniform(0.0, net_weight)
        i = numpy.searchsorted(cumulative, x, side = 'right')
        # update the weights as we're not sampling with replacement
        chosen_vars.append(names[i])
        net_weight -= weights[i]
        weights[i] = 0.0
    return chosen_vars

def make_normalisation(x):
    x = numpy.array(x)
    lo = x.min()
    hi = x.max()
    if hi > lo:
        return lambda z : (z - lo) / (hi - lo)
    else:
        return lambda _ : 0

def update_weights(var_weights, mse_scores, gini_scores):
    """
    *** in place modification of var_weights! ***
    """

    # normalise mse and gini scores so they are somewhat comparable
    normalise_mse = make_normalisation(mse_scores.values())
    normalise_gini = make_normalisation(gini_scores.values())

    for var in var_weights:
        if var not in mse_scores:
            continue
        if var not in gini_scores:
            continue
        score = 0.0
        mse = normalise_mse(mse_scores[var])
        gini = normalise_gini(gini_scores[var])
        score += max(mse, 0.0)
        score += max(gini, 0.0)
        var_weights[var].append(score)
    return var_weights

def log_progress(key, **kwargs):
    log_path = os.path.join('log', '%s.pickle' % key)
    if not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path))
    log_file = open(log_path, 'wb')
    pickle.dump(kwargs, log_file)
    log_file.close()

def display_var_weights(compressed_weights, shortlist_length= 30):
    items = compressed_weights.items()
    items = sorted(items, key = lambda x : x[1], reverse = True)
    print '\tHighest scoring variables:'
    for (name, score) in items[:shortlist_length]:
        print '\t%.3f\t\t%s' % (score, name)

def optimise_vars(rdata_path, all_vars, n_vars_per_experiment):
    var_weights = make_initial_weights(all_vars)
    for i in itertools.count():
        print '[ ITER %d ]' % i
        compressed_weights = compress_weights(var_weights)

        display_var_weights(compressed_weights)

        selected_vars = choose_vars(compressed_weights, n_vars_per_experiment)

        mse_scores, gini_scores, test_mse = run_experiment(
            rdata_path,
            selected_vars
        )
        # XXX TODO : indication of horrible bug test_mse doesnt always seem to
        # agree with what R prints (issue with list of results ???)
        # if so this might catch it
        assert set(mse_scores.keys()) == set(gini_scores.keys())
        print '\n\tmse test score: %.3f' % test_mse

        update_weights(var_weights, mse_scores, gini_scores)

        log_progress(
            i, # key by iteration
            compressed_weights = compressed_weights,
            selected_vars = selected_vars,
            test_mse = test_mse,
            mse_scores = mse_scores,
            gini_scores = gini_scores
        )

def get_all_vars(rdata_path, rdata_suffix = '.Rdata'):
    rdata_files = glob.glob(os.path.join(rdata_path, ('*' + rdata_suffix)))
    all_vars = [os.path.splitext(os.path.basename(name))[0] for name in rdata_files]
    return all_vars

def main():
    rdata_path = 'gen/rdata_train_augmented'

    optimise_vars(
        rdata_path,
        all_vars = get_all_vars(rdata_path),
        n_vars_per_experiment = 100
    )

if __name__ == '__main__':
    main()
