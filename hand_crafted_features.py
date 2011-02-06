import numpy
import os

from create_features import unpickle
from butcher_data import write_cols_to_r_binary_files

def make_contract_band_midpoints(cols):
    name = 'Contract.Value.Band...see.note.A'
    codes = numpy.array(cols[name])
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
    values = numpy.ma.zeros(numpy.shape(cols[name]), dtype = numpy.float)
    for i, code in enumerate(codes):
        values[i] = contract_band_midpoint_value.get(code, numpy.ma.masked)
    fmt = ('float', 'numeric')
    new_name = 'Contract.Value.Midpoint'
    return {new_name : values}, {new_name : fmt}

def main():
    cols = unpickle('gen/cols.pickle')
    new_cols, new_fmts = make_contract_band_midpoints(cols)
    write_cols_to_r_binary_files(
        new_cols,
        new_fmts,
        dump_dir = 'gen/rdata_train_handcrafted_features/',
    )

if __name__ == '__main__':
    main()
