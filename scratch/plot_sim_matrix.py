import pickle
import numpy
import pylab

def make_sim_matrix(sim):
    keys = sim.keys()
    names = set()
    for (u, v) in keys:
        names.add(u)
        names.add(v)
    names = list(sorted(list(names)))

    n = len(names)
    a = numpy.zeros((n, n), dtype = numpy.float64)
    for i, name_i in enumerate(names):
        for j, name_j in enumerate(names):
            pair = (name_i, name_j)
            if pair not in sim:
                pair = (name_j, name_i)
            if pair not in sim:
                continue
            theta = sim[pair]
            theta = float(theta)
            if not numpy.isfinite(theta):
                a[i, j] = 0.0
            else:
                a[i, j] = theta
    return a

def main():
    sim = pickle.load(open('sim-matrix.pickle', 'rb'))
    a = make_sim_matrix(sim)
    pylab.figure()
    pylab.imshow(a, interpolation = 'nearest')
    pylab.show()

if __name__ == '__main__':
    main()
