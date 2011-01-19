"""
proof-of-concept hack to merge duplicate entries of people and try to find
inconsistencies. at the moment it doesnt look like we find any major
inconsistencies, apart from the odd country which seems to be wrong, while
the other attributes (eg faculty, department, phd, age) all match.

seems good enough

generates a people.csv file when run
"""

import numpy
import pickle

def make_edges(cols):
    max_people = 15
    edges = set()
    for i in xrange(1, max_people + 1):
        col = cols['Person.ID.%d' % i]
        indices = numpy.arange(len(col))
        indices = indices[numpy.logical_not(col.mask)]
        for (person_id, grant_index) in zip(col.compressed(), indices):
            edges.add((person_id, grant_index))
    return edges

def main():
    file_name = '../cols.pickle'
    people_file = open(file_name, 'rb+')
    these_cols = pickle.load(people_file)
    people_file.close()

    edges = make_edges(these_cols)
    people = set()
    for (p, g) in edges:
        people.add(p)

    grants_win = set()
    grants_fail = set()
    col = these_cols['Grant.Status']
    indices = numpy.arange(len(col))
    indices = indices[numpy.logical_not(col.mask)]
    for (grant_index, win) in zip(indices, col.compressed()):
        if win:
            grants_win.add(grant_index)
        else:
            grants_fail.add(grant_index)

    graph_file = open('people.gv', 'w+')
    header = [
        'digraph G {\n',
        '\tgraph [center bgcolor="#808080"]\n',
        '\tedge [dir=none]\n',
        '\tnode [width=0.1 height=0.1 label="" style="filled"]\n',
    ]
    graph_file.write(''.join(header))
    graph_file.write('\t{ node [shape=circle color = "#000000"]\n')

    for a in sorted(list(people)):
        graph_file.write('\t\tP_%d\n' % a)
    graph_file.write('\t}\n')

    graph_file.write('\t{ node [shape=diamond color = "#00ff00"]\n')
    for grant_id in sorted(list(grants_win)):
        graph_file.write('\t\tG_%d\n' % grant_id)
    graph_file.write('\t}\n')

    graph_file.write('\t{ node [shape=diamond color = "#ff0000"]\n')
    for grant_id in sorted(list(grants_fail)):
        graph_file.write('\t\tG_%d\n' % grant_id)
    graph_file.write('\t}\n')

    for (a, b) in edges:
        graph_file.write('\tP_%d -> G_%d\n' % (a, b))
    graph_file.write('}\n')
    graph_file.close()

    # hack : get a feel for the spread of dates
    print sorted([x for x in these_cols.keys() if 'date' in x.lower()])
    dates = these_cols['Start.date']
    import pylab
    dates = dates.compressed()
    dates -= dates.min()
    # pylab.hist(dates, bins = 100)

    # another hack
    dates = these_cols['Start.date']
    indices = numpy.arange(len(dates))
    indices = indices[numpy.logical_not(dates.mask)]
    dates = dates[indices]

    jobs_of_person = {}
    for (p, j) in edges:
        if p not in jobs_of_person:
            jobs_of_person[p] = []
        jobs_of_person[p].append(j)
    foo_p = []
    foo_date_delta = []
    foo_succ_old = []
    foo_succ_new = []
    for p in jobs_of_person:
        for j_old in jobs_of_person[p]:
            for j_new in jobs_of_person[p]:
                date_delta = dates[j_new] - dates[j_old]
                if date_delta <= 0:
                    continue
                foo_p.append(p)
                foo_date_delta.append(date_delta)
                foo_succ_old.append(j_old in grants_win)
                foo_succ_new.append(j_new in grants_win)
    foo_p = numpy.asarray(foo_p)
    foo_date_delta = numpy.asarray(foo_date_delta)
    foo_succ_old = numpy.asarray(foo_succ_old)
    foo_succ_new = numpy.asarray(foo_succ_new)
    # pylab.figure()
    # todo : factorise on succ old and succ new
    for a, mask_a in enumerate((foo_succ_old, numpy.logical_not(foo_succ_old))):
        for b, mask_b in enumerate((foo_succ_new, numpy.logical_not(foo_succ_new))):
            # pylab.subplot(2, 2, (1 + a + (2 * b)))
            pylab.figure()
            mask = numpy.logical_and(mask_a, mask_b)
            p_indices = numpy.arange(len(foo_p[mask]))
            p_order = numpy.argsort(foo_p[mask])
            p_relabled = p_indices[p_order] # this is probably wrong
            pylab.hexbin(foo_date_delta[mask], p_relabled, gridsize = 40)
            pylab.title('a %d b %d entries: %d' % (a, b, len(foo_p[mask])))
    pylab.show()

if __name__ == '__main__':
    main()
