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

contract_band_midpoint_value = {
    'A' : 25000,
    'B' : 75000,
    'C' : 150000,
    'D' : 250000,
    'E' : 350000,
    'F' : 450000,
    'G' : 750000,
    'H' : 1500000,
    'I' : 2500000,
    'J' : 3500000,
    'K' : 4500000,
    'L' : 5500000,
    'M' : 6500000,
    'N' : 7500000,
    'O' : 8500000,
    'P' : 9500000,
    'Q' : 55000000,
}

def main():
    # load cols
    pickle_file = open('../cols.pickle', 'rb')
    cols = pickle.load(pickle_file)

    ages = cols['Start.date']
    min_age = 0
    max_age = 1

    shared_applicant_mode = 'any' # 'any' or 'all'

    grant_success_mode = False

    selected_variable = 'Contract.Value.Band...see.note.A'

    def map_function(band):
        # convert contract value band to something reasonable
        return contract_band_midpoint_value[band]

    reduce_function = numpy.add.reduce

    n_rows = len(ages)
    new_features = []
    for i in xrange(n_rows):
        assert len(new_features) == i
        print 'computing new feature for row %d' % i
        # 1. filter by age
        my_age = ages[i]
        if my_age is numpy.ma.masked:
            new_features.append(numpy.ma.masked)
            print '\tmy age missing'
            continue
        years_prior = (my_age - ages) / 365.0
        age_mask = numpy.logical_and(
            min_age < years_prior,
            years_prior <= max_age,
        )
        mask = age_mask.filled(False)
        if numpy.any(mask) == 0:
            new_features.append(numpy.ma.masked)
            print '\tno older applicants exist'
            continue
        else:
            print'\tolder applicants: %d' % numpy.add.reduce(mask)

        # 2. filter by shared applicants
        if shared_applicant_mode == 'all':
            raise NotImplementedError('todo')
        else:
            max_people = 15
            applicant_mask = numpy.zeros(numpy.shape(mask), dtype = numpy.bool)
            for j in xrange(1, max_people + 1):
                applicant = cols['Person.ID.%d' % j][i]
                if applicant is not numpy.ma.masked:
                    for k in xrange(1, max_people + 1):
                        another_applicant = cols['Person.ID.%d' % k]
                        # print '\t\t* %d' % numpy.add.reduce(another_applicant.filled(-1) == applicant)
                        applicant_mask = numpy.logical_or(
                            applicant_mask,
                            another_applicant.filled(-1) == applicant
                        )
        mask = numpy.logical_and(mask, applicant_mask)

        if not numpy.any(mask):
            print '\tfound no applications with shared applicants'
            new_features.append(numpy.ma.masked)
            continue
        else:
            print'\tapplications with shared applicants: %d' % numpy.add.reduce(mask)

        # 3. filter by grant success
        success_mask = cols['Grant.Status']
        if not grant_success_mode:
            success_mask = numpy.logical_not(success_mask)
        mask = numpy.logical_and(mask, success_mask)

        # 4. optionally, filter by some other indicator or categorical thing
        # nb not implemented ...

        # 5. select variable to extract
        mask = mask.filled(False)
        if not numpy.any(mask):
            new_features.append(numpy.ma.masked)
            continue
        else:
            print'\tapplicants with matching grant status: %d' % numpy.add.reduce(mask)

        print('\tsome entries passed filters:')
        print('\t\t%s' % str(numpy.nonzero(mask)))
        values = cols[selected_variable][mask]
        values = [map_function(x) for x in values if x is not numpy.ma.masked]
        if not values:
            new_features.append(numpy.ma.masked)
        else:
            reduced_value = reduce_function(values)
            print('\tadded new value for feature: %s' % str(reduced_value))
            new_features.append(reduced_value)

    new_features = numpy.ma.masked_array(new_features)

    pickle.dump(new_features, open('another_new_feature.pickle', 'wb+'))

if __name__ == '__main__':
    main()
