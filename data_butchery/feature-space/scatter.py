import numpy
import pickle
import pylab


def pretty_hexbin(x, y):
    return pylab.hexbin(
        x,
        y,
        gridsize = 10,
        bins = 'log',
        mincnt = 0,
    )

def main():
    # load cols
    pickle_file = open('../cols.pickle', 'rb')
    cols = pickle.load(pickle_file)
    status = cols['Grant.Status'].filled(False)
    status = numpy.array(status, dtype = numpy.bool)
    x = pickle.load(open('new_feature.pickle', 'rb+'))
    y = pickle.load(open('another_new_feature.pickle', 'rb+'))
    x = numpy.log(x.filled(numpy.min(x) / 2))
    y = numpy.log(y.filled(numpy.min(y) / 2))

    x = x / (x.max() - x.min())
    y = y / (y.max() - y.min())

    jitter = 0.04
    x = x + numpy.random.uniform(-jitter, jitter, x.shape)
    y = y + numpy.random.uniform(-jitter, jitter, y.shape)

    pylab.figure()
    pylab.scatter(x[numpy.logical_not(status)], y[numpy.logical_not(status)], marker = 's', color = 'r')
    pylab.scatter(x[status], y[status], marker = 'x', color = 'g')
    pylab.xlabel('$ won')
    pylab.ylabel('$ fail')
    pylab.show()

if __name__ == '__main__':
    main()
