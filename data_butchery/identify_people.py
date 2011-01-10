"""
proof-of-concept hack to merge duplicate entries of people and try to find
inconsistencies. at the moment it doesnt look like we find any major
inconsistencies, apart from the odd country which seems to be wrong, while
the other attributes (eg faculty, department, phd, age) all match.

seems good enough

generates a people.csv file when run
"""

import sys
import numpy
import pickle
import csv

def write_cols_to_csv_file(cols, csv_file, row_id_name):
    cols_as_lists = {}
    for col_name in sorted(cols):
        print 'processing col %s' % col_name
        col = cols[col_name]
        if col.mask.shape != col.shape:
            col.mask = numpy.zeros(col.shape, dtype = numpy.bool)
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

def write_rows_to_csv_file(rows, col_names, csv_file):

    writer = csv.writer(
        csv_file,
        delimiter = ',',
        quotechar = '"',
        quoting = csv.QUOTE_MINIMAL,
    )

    print 'writing csv'
    # write header
    writer.writerow(col_names)
    # write rows
    for key in sorted(rows):
        writer.writerow([key] + rows[key])


def merge_people_cols(cols):
    max_people = 15
    people_cols = {}
    col_names = (
        'Person.ID.%d',
        'Role.%d',
        'Year.of.Birth.%d',
        'Country.of.Birth.%d',
        'Home.Language.%d',
        'Dept.No..%d',
        'Faculty.No..%d',
        'With.PHD.%d',
        'No..of.Years.in.Uni.at.Time.of.Grant.%d',
        'Number.of.Successful.Grant.%d',
        'Number.of.Unsuccessful.Grant.%d',
        'A..%d',
        'A.%d',
        'B.%d',
        'C.%d',
    )
    for i in xrange(1, max_people + 1):
        for name in col_names:
            if (name % 0) not in people_cols:
                people_cols[name % 0] = []
            people_cols[name % 0].append(cols[name % i])
    for name in people_cols:
        people_cols[name] = numpy.ma.concatenate(people_cols[name])
    return people_cols


def merge_people_rows(cols):
    key_name = 'Person.ID.0'
    other_names = [name for name in cols.keys() if name != key_name]
    n_rows = len(cols[key_name])

    def gen_items():
        for i in xrange(n_rows):
            key = cols[key_name][i]
            row = [cols[name][i] for name in other_names]
            row = [x if x is not numpy.ma.masked else None for x in row]
            yield (key, row)

    def combine_values(a, b):
        c = []
        n_agree = 0
        n_disagree = 0
        for (ai, bi) in zip(a, b):
            if (ai != None) and (bi != None):
                if ai == bi:
                    n_agree += 1
                else:
                    n_disagree += 1
            if ai is None:
                c.append(bi)
            else:
                c.append(ai)
        return c, n_agree, n_disagree

    merged_rows = {}
    for key, value in gen_items():
        if key in merged_rows:
            old_value = merged_rows[key]
            new_value, n_agree, n_disagree = combine_values(old_value, value)
            if n_disagree > 0:
                print '- inconsistency in data:'
                print '\tkey : %s' % str(key)
                print '\told value : %s' % str(old_value)
                print '\tvalue : %s' % str(value)
                if n_agree > n_disagree:
                    print '\tn_agree > n_disagree, merging anyway'
                    merged_rows[key] = new_value
                else:
                    raise ValueError('serious data inconsistency')
            else:
                merged_rows[key] = new_value
        else:
            merged_rows[key] = value

    return merged_rows, [key_name] + other_names

def main():
    if len(sys.argv) < 2:
        print 'usage: people_a.pickle [people_b.pickle [ ...]]'
        print ''
        print '\tgenerates a people.csv file when run'
        sys.exit(1)

    cols = {}
    for file_name in sys.argv[1:]:
        people_file = open(file_name, 'rb+')
        these_cols = pickle.load(people_file)
        people_file.close()
        these_cols = merge_people_cols(these_cols)
        for name in these_cols:
            if name not in cols:
                cols[name] = these_cols[name]
            else:
                cols[name] = numpy.ma.concatenate((cols[name], these_cols[name]))

    row_mask = numpy.logical_not(cols['Person.ID.0'].mask)
    for name in cols:
        cols[name] = cols[name][row_mask]
    order = numpy.ma.argsort(cols['Person.ID.0'])
    for name in cols:
        cols[name] = cols[name][order]

# remove cols that aren't likely to be constant for an individual
    bad_col_names = (
        'Role.%d',
        'No..of.Years.in.Uni.at.Time.of.Grant.%d',
        'Number.of.Successful.Grant.%d',
        'Number.of.Unsuccessful.Grant.%d',
        'A..%d',
        'A.%d',
        'B.%d',
        'C.%d',
    )
    for name in bad_col_names:
        del cols[name % 0]

    # attempt to merge rows with the same person id
    merged_rows, col_names = merge_people_rows(cols)


    csv_file = open('people.csv', 'w+')
    write_rows_to_csv_file(merged_rows, col_names, csv_file)

if __name__ == '__main__':
    main()
