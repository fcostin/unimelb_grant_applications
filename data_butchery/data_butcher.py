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
    # XXX TODO FIXME HACK : csv file seems to have a trailing comma at the end of each row
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

# SOR categorisation

def extract_sor_division(x):
    return (x / 10000) * 10000

# define column formatting
def make_col_formats():
    fmt = {}
    fmt['Grant.Application.ID'] = ('integer', 'row_id')
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
            fmt['%s.Code.%d' % (code_type, i)] = ('integer', 'factor')

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

def make_division_cols(cols, division_type):
    if division_type == 'RFCD':
        extract = extract_rfcd_division
    elif division_type == 'SEO':
        extract = extract_sor_division
    else:
        raise ValueError('unknown division_type: %s' % str(division_type))

    # first see which divisions are present in the data
    max_codes = 5
    known_divs = set()
    div_cols = []
    for i in xrange(1, max_codes + 1):
        col_name = '%s.Code.%d' % (division_type, i)
        percent_col_name = '%s.Percentage.%d' % (division_type, i)
        codes = cols[col_name]
        div_codes = extract(codes)
        div_cols.append((div_codes, cols[percent_col_name]))
        for div in numpy.unique(div_codes.compressed()): # nb compressed() returns non masked values only
            known_divs.add(div)

    # then make a bunch of new cols that sum percentages
    # over all codes belonging to the identified
    # divisions.
    out_div_cols = {}
    for div in known_divs:
        print 'creating new column for %s division %d' % (division_type, div)
        new_col_name = '%s.Division.Percentage.%d' % (division_type, div)
        div_percent = 0.0
        # accumulate percentages for this div
        for (div_codes, percentages) in div_cols:
            mask = (div_codes == div)
            div_percent = div_percent + (percentages * mask)
        out_div_cols[new_col_name] = div_percent

    return out_div_cols

def replace_cols_with_divisional_percentages(cols, fmts, division_type):
    div_cols = make_division_cols(cols, division_type)
    for col_name in div_cols:
        assert col_name not in cols
        cols[col_name] = div_cols[col_name]
        fmts[col_name] = ('float', 'number')
    max_codes = 5
    for i in xrange(1, max_codes + 1):
        for s in ['Percentage', 'Code']:
            col_name = '%s.%s.%d' % (division_type, s, i)
            del cols[col_name]
            del fmts[col_name]
    return cols

def write_cols_to_csv_file(cols, csv_file, row_id_name):
    cols_as_lists = {}
    for col_name in sorted(cols):
        print 'processing col %s' % col_name
        col = cols[col_name]
        col_list = [x if not m else None for (x, m) in zip(col, col.mask)]
        cols_as_lists[col_name] = col_list

    # define row order for output
    col_order = list(sorted(cols))
    col_order = [row_id_name] + [x for x in col_order if x != row_id_name]
    n_rows = len(cols.values()[0])

    def make_row(i):
        return [cols_as_lists[c][i] for c in col_order]

    writer = csv.writer(
        csv_file,
        delimiter = ',',
        quotechar = '"',
        quoting = csv.QUOTE_MINIMAL,
    )

    print 'writing csv'
    # write header
    writer.writerow(col_order)
    # write rows
    for i in xrange(n_rows):
        if (i % 100) == 0:
            print 'writing row %d' % i
        writer.writerow(make_row(i))

def main():
    # read cols (no conversion is done here, cols are stored as lists of
    # strings)
    cols = load_csv(open(sys.argv[1], 'r'))
    # sanity check to ensure all cols have same length
    assert len(set([len(col) for col in cols.itervalues()])) == 1

    # define how cols are to be parsed, then parse 'em
    parsers = {
        'integer' : parse_array_of_ints,
        'float' : parse_array_of_floats,
        'date' : parse_array_of_dates,
        'string' : parse_array_of_strings,
        'sparse_logical' : parse_array_of_sparse_logicals,
    }
    fmts = make_col_formats()
    for col_name in sorted(cols):
        fmt = fmts[col_name]
        dtype, vartype = fmt
        print 'parsing col %s as dtype %s' % (col_name, dtype)
        cols[col_name] = parsers[dtype](cols[col_name])

    # replace rfcd column encoding with one based upon divisions
    # XXX TODO FIXME : this does result in a loss of information.
    # this isnt necessarily a bad thing but it might be worth
    # checking out later if trying to improve accuracy
    # of predictive models

    replace_cols_with_divisional_percentages(cols, fmts, 'RFCD')
    replace_cols_with_divisional_percentages(cols, fmts, 'SEO')

    # delete any columns of type id
    for col_name in fmts:
        dtype, vartype = fmts[col_name]
        if vartype == 'id':
            print 'removing column %s of vartype id' % col_name
            del cols[col_name]

    # rename cols to include prefix which we'll use to tell R which format
    # should be used

    dtype_symbol = {
        'integer' : 'I',
        'float' : 'F',
        'date' : 'I',
        'string' : 'S',
        'sparse_logical' : 'S',
    }

    vartype_symbol = {
        'number' : 'NUM',
        'factor' : 'FAC',
        'row_id' : 'KEY',
    }

    renamed_cols = {}
    for col_name in fmts:
        if col_name not in cols:
            continue
        dtype, vartype = fmts[col_name]
        new_name = '%s.%s.%s' % (dtype_symbol[dtype], vartype_symbol[vartype], col_name)
        renamed_cols[new_name] = cols[col_name]

    write_cols_to_csv_file(
        renamed_cols,
        open('butchered_data.csv', 'w+'),
        row_id_name = 'I.KEY.Grant.Application.ID'
    )

if __name__ == '__main__':
    main()
