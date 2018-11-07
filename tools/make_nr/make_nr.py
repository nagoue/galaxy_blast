#!/usr/bin/env python3
"""Check for combining duplicate sequence in FASTA files.

This script takes one or more FASTA filenames as input, and
will return a non-zero error if any duplicate identifiers
are found. Writes output to stdout.

Keeps all the sequences in memory, beware!
"""
from __future__ import print_function

import gzip
import os
import sys

from optparse import OptionParser


if "-v" in sys.argv or "--version" in sys.argv:
    print("v0.0.0")
    sys.exit(0)


# Parse Command Line
usage = """Use as follows:

$ python make_nr.py [options] A.fasta [B.fasta ...]

For example,

$ python make_nr.py -o dedup.fasta -s ";" input1.fasta input2.fasta

There is additional guidance in the help text in the make_nr.xml file,
which is shown to the user via the Galaxy interface to this tool.
"""

parser = OptionParser(usage=usage)
parser.add_option("-s", "--sep", dest="sep",
                  default=";",
                  help="Separator character for combining identifiers of duplicated records e.g. '|' or ';' (required)")
parser.add_option("-o", "--output", dest="output",
                  default="/dev/stdout", metavar="FILE",
                  help="Output filename (defaults to stdout)")
options, args = parser.parse_args()

if not args:
    sys.exit("Expects at least one input FASTA filename")


def make_nr(input_fasta, output_fasta, sep=";"):
    """Make the sequences in FASTA files non-redundant.

    Argument input_fasta is a list of filenames.
    """
    by_seq = dict()
    try:
        from Bio.SeqIO.FastaIO import SimpleFastaParser
    except KeyError:
        sys.exit("Missing Biopython")
    for f in input_fasta:
        with open(f) as handle:
            for title, seq in SimpleFastaParser(handle):
                idn = title.split(None, 1)[0]  # first word only
                seq = seq.upper()
                try:
                    by_seq[seq].append(idn)
                except KeyError:
                    by_seq[seq] = [idn]
    unique = 0
    representatives = dict()
    duplicates = set()
    for cluster in by_seq.values():
        if len(cluster) > 1:
            representatives[cluster[0]] = cluster
            duplicates.update(cluster[1:])
        else:
            unique += 1
    del by_seq
    if duplicates:
        # TODO - refactor as a generator with single SeqIO.write(...) call
        with open(output_fasta, "w") as handle:
            for f in input_fasta:
                with open(f) as in_handle:
                    for title, seq in SimpleFastaParser(in_handle):
                        idn = title.split(None, 1)[0]  # first word only
                        if idn in representatives:
                            cluster = representatives[idn]
                            idn = sep.join(cluster)
                            title = "%s representing %i records" % (idn, len(cluster))
                        elif idn in duplicates:
                            continue
                        # TODO - line wrapping
                        handle.write(">%s\n%s\n" % (title, seq))
        print("%i unique entries; removed %i duplicates leaving %i representative records"
              % (unique, len(duplicates), len(representatives)))
    else:
        os.symlink(os.path.abspath(input_fasta), output_fasta)
        print("No perfect duplicates in file, %i unique entries" % unique)


make_nr(args, options.output, options.sep)
