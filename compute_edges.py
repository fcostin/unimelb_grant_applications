import numpy
import pickle

def main():
    pickle_file = open('gen/cols.pickle', 'rb')
    cols = pickle.load(pickle_file)
    picle_file.close()
    ages = cols['Start.date']
    min_age = 0
    max_age = 10
    max_people = 15
    n_rows = len(ages)

    for min_shared_applicants in (1, 2, 3):
        new_features = []
        for i in xrange(n_rows):
            assert len(new_features) == i
            print 'computing new feature for row %d' % i
            # 1. filter by age
            my_age = ages[i]
            if my_age is numpy.ma.masked:
                new_features.append([])
                print '\tmy age missing'
                continue
            years_prior = (my_age - ages) / 365.0
            age_mask = numpy.logical_and(
                min_age < years_prior,
                years_prior <= max_age,
            )
            mask = age_mask.filled(False)
            if numpy.any(mask) == 0:
                new_features.append([])
                print '\tno older applicants exist'
                continue
            else:
                print'\tolder applicants: %d' % numpy.add.reduce(mask)

            # 2. filter by shared applicants
            shared_applicant_count = numpy.zeros(numpy.shape(mask), dtype = numpy.int)
            n_applicants_listed = True
            for j in xrange(1, max_people + 1):
                applicant = cols['Person.ID.%d' % j][i]
                if applicant is not numpy.ma.masked:
                    n_applicants_listed += 1
                    for k in xrange(1, max_people + 1):
                        another_applicant = cols['Person.ID.%d' % k]
                        shared_applicant_count = numpy.add(
                            shared_applicant_count,
                            another_applicant.filled(-1) == applicant
                        )
            if not n_applicants_listed:
                shared_applicant_count = numpy.zeros(numpy.shape(mask), dtype = numpy.int)
            applicant_mask = shared_applicant_count > min_shared_applicants

            mask = numpy.logical_and(mask, applicant_mask)
            sparse_mask = list(mask.nonzero()[0])
            print '\tsparse_mask: %s' % str(sparse_mask)
            new_features.append(sparse_mask)

        dump_file_name = 'gen/edges-grants-with-min-%d-shared-applicants.pickle' % min_shared_applicants
        pickle.dump(new_features, open(dump_file_name, 'wb'))

if __name__ == '__main__':
    main()
