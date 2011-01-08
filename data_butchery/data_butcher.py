import csv
import sys
import numpy
import datetime

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
    # HACK : csv file seems to have a trailing comma at the end of each row
    # when parsed this gives as a col of name '' containing entries ''
    # so we delete this from our cols
    if '' in cols:
        del cols['']
    return cols

# parsing of basic types

def parse_int(s):
    try:
        x = int(s.strip())
        return x
    except ValueError:
        return None

def parse_float(s):
    try:
        x = float(s.strip())
        return x
    except ValueError:
        return None

def parse_string(s):
    s = s.strip()
    if s == '':
        return None
    else:
        return s

def parse_date(s):
    # transform dd/mm/yyyy into some number of days since origin date, return
    # integer
    try:
        x = datetime.datetime.strptime(s.strip(), '%d/%m/%Y')
    except ValueError:
        return None
    return x.toordinal() # return number of days since jan 1st year 0001

def parse_sparse_logical(s):
    s = s.strip()
    if s == 'Yes':
        return True
    elif s == '':
        return False
    else:
        raise ValueError("sparse logical must be either 'Yes' or '', not '%s'" % str(s))

# handling parsing arrays of things

def parse_array(a, parse_elem, default_value):
    """
    converts arg to array of ints, with unparseable values masked
    """
    a = [parse_elem(x) for x in a]
    missing_values = [x is None for x in a]
    a = [default_value if x is None else x for x in a]
    return numpy.ma.masked_array(a, mask = missing_values)

def parse_array_of_ints(a):
    return parse_array(a, parse_int, default_value = 0)

def parse_array_of_floats(a):
    return parse_array(a, parse_float, default_value = 0.0)

def parse_array_of_strings(a):
    return parse_array(a, parse_string, default_value = '')

def parse_array_of_dates(a):
    return parse_array(a, parse_date, default_value = 0)

def parse_array_of_sparse_logicals(a):
    return parse_array(a, parse_sparse_logical, default_value = False)

# domain-specific transforms

# RFCD categorisation (for coarsening research subject codes)

def extract_rfcd_division(x):
    # division is coarsest designation
    return (x / 10000) * 10000

def extract_rfcd_discipline(x):
    # discipline is second coarsest designation
    return (x / 1000) * 1000

def make_col_formats():
    fmt = {}
    fmt['Grant.Application.ID'] = ('integer', 'id')
    fmt['Grant.Status'] = ('integer', 'factor')

    # nb this is not at all appropriate for use as a factor in R
    # as it has way too many unique values for randomForest to handle
    # as a factor. XXX TODO figure out a coarser coding scheme for this
    fmt['Sponsor.Code'] = ('string', 'id')

    fmt['Grant.Category.Code'] = ('string', 'factor')
    fmt['Contract.Value.Band...see.note.A'] = ('string', 'factor')
    fmt['Start.date'] = ('date', 'number')

    # parse RFCD and SEO weighted classification codes .....
    # these raw codes are not appropriate for use as factors in R
    # as they have way more than 32 values
    max_codes = 5
    for code_type in ['RFCD', 'SEO']:
        for i in xrange(1, max_codes + 1):
            fmt['%s.Percentage.%d' % (code_type, i)] = ('float', 'number')
            fmt['%s.Code.%d' % (code_type, i)] = ('integer', 'id')

    # parse information for each person listed on the grant application
    max_people = 15
    for i in xrange(1, max_people + 1):

        # XXX TODO probably best to drop these ids from the data later on ??
        # keeping this in will give models chance to pick up
        # researcher-specific effects and is therefore unlikely to help that
        # much with prediction when applied to previously unknown researchers
        # on the other hand it might have a large effect on the test data...
        fmt['Person.ID.%d' % i] = ('integer', 'id')

        fmt['Role.%d' % i] = ('string', 'factor')
        fmt['Year.of.Birth.%d' % i] = ('integer', 'number')
        fmt['Country.of.Birth.%d' % i] = ('string', 'factor')
        fmt['Home.Language.%d' % i] = ('string', 'factor')

        # XXX TODO there are a few hundred of these ones, too many for a single factor
        fmt['Dept.No..%d' % i] = ('integer', 'id')
        fmt['Faculty.No..%d' % i] = ('integer', 'factor')
        fmt['With.PHD.%d' % i] = ('sparse_logical', 'factor') # 'Yes' -> True, missing -> False
        fmt['No..of.Years.in.Uni.at.Time.of.Grant.%d' % i] = ('integer', 'number')
        fmt['Number.of.Successful.Grant.%d' % i] = ('integer', 'number')
        fmt['Number.of.Unsuccessful.Grant.%d' % i] = ('integer', 'number')
        # publication counts ....
        fmt['A..%d' % i] = ('integer', 'number')
        fmt['A.%d' % i] = ('integer', 'number')
        fmt['B.%d' % i] = ('integer', 'number')
        fmt['C.%d' % i] = ('integer', 'number')

    return fmt



def main():
    # read cols (no conversion is done here, cols are stored as lists of
    # strings)
    cols = load_csv(open(sys.argv[1], 'r'))
    # sanity check to ensure all cols have same length
    assert len(set([len(col) for col in cols.itervalues()])) == 1

    parsers = {
        'integer' : parse_array_of_ints,
        'float' : parse_array_of_floats,
        'date' : parse_array_of_dates,
        'string' : parse_array_of_strings,
        'sparse_logical' : parse_array_of_sparse_logicals,
    }

    fmts = make_col_formats()

    for col_name in cols:
        fmt = fmts[col_name]
        dtype, vartype = fmt
        print 'parsing col %s as dtype %s' % (col_name, dtype)
        cols[col_name] = parsers[dtype](cols[col_name])



def test():
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
        b = extract_rfcd_division(aa)
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
