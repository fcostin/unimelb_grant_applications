import csv
import sys
import numpy

def load_csv(csv_file):
    cols = {}
    col_names = None
    f = csv.reader(csv_file, delimiter = ',', quotechar = '"')
    for i, row in enumerate(f):
        if i == 0:
            col_names = row
            for col_name in row:
                cols[col_name] = []
        else:
            for (name, value) in zip(col_names, row):
                cols[name].append(value)
    return cols

def rfcd_code_to_root(x):
    return (x / 10000) * 10000

def parse_int(s):
    try:
        x = int(s)
        return x
    except ValueError:
        return None

def parse_array_of_ints(a):
    """
    converts arg to array of ints, with unparseable values masked
    """
    a = [parse_int(x) for x in a]
    missing_values = [x is None for x in a]
    a = [0 if x is None else x for x in a]
    return numpy.ma.masked_array(a, mask = missing_values, dtype = numpy.int)

def main():
    # read cols (no conversion is done here, cols are stored as lists of
    # strings)
    cols = load_csv(open(sys.argv[1], 'r'))
    # sanity check to ensure all cols have same length
    assert len(set([len(col) for col in cols.itervalues()])) == 1

    total_rfcd_freq = {}
    # convert RFCD codes
    for i in xrange(1, 5 + 1):
        col_name = 'RFCD.Code.%d' % i
        a = cols[col_name ]
        aa = parse_array_of_ints(a)
        print 'col name %s; number of values is %d of total %d' % (col_name, aa.count(), len(aa))
        b = rfcd_code_to_root(aa)
        freq = {}
        for x in b.compressed(): # only iterate over non-masked values
            if x not in freq:
                freq[x] = 0
            freq[x] += 1
        for x in sorted(freq):
            print '\tvalue: %d; count: %d' % (x, freq[x])
        for x in freq:
            if x not in total_rfcd_freq:
                total_rfcd_freq[x] = 0
            total_rfcd_freq[x] += freq[x]


    print 'TOTAL RFCD frequencies, summed over all 5 codes...'
    for x in sorted(total_rfcd_freq):
        print '\tvalue: %d; count: %d' % (x, total_rfcd_freq[x])

if __name__ == '__main__':
    main()
