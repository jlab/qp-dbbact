#!/usr/bin/env python

# -----------------------------------------------------------------------------
# Copyright (c) 2024, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from setuptools import setup

__version__ = "2024.03"

classes = """
    Development Status :: 3 - Alpha
    License :: OSI Approved :: BSD License
    Topic :: Scientific/Engineering :: Bio-Informatics
    Topic :: Software Development :: Libraries :: Application Frameworks
    Topic :: Software Development :: Libraries :: Python Modules
    Programming Language :: Python
    Programming Language :: Python :: 3.11
    Programming Language :: Python :: Implementation :: CPython
    Operating System :: POSIX :: Linux
    Operating System :: MacOS :: MacOS X
"""

with open('README.rst') as f:
    long_description = f.read()

classifiers = [s.strip() for s in classes.split('\n') if s]
setup(name='qp-dbbact',
      version=__version__,
      long_description=long_description,
      license="BSD",
      description='Qiita Plugin: dbBact',
      author="Qiita development team",
      author_email="qiita.help@gmail.com",
      url='https://github.com/qiita-spots/qp-dbbact',
      test_suite='nose2.collector.collector',
      packages=['qp_dbbact'],
      package_data={'qp_dbbact': [
          # '../support_files/sepp/*.json',
          # '../support_files/sepp/*.py',
          # '../support_files/sepp/reference_alignment_tiny.fasta',
          # '../support_files/sepp/reference_phylogeny_tiny.nwk'
      ]},
      scripts=['scripts/configure_dbbact', 'scripts/start_dbbact'],
      extras_require={'test': ["nose2", "pep8"]},
      install_requires=['click', 'scikit-bio', 'pandas', 'future',
                        'biom-format', 'wordcloud',
                        'qiita-files @ https://github.com/'
                        'qiita-spots/qiita-files/archive/master.zip',
                        'qiita_client @ https://github.com/qiita-spots/'
                        'qiita_client/archive/master.zip'],
      classifiers=classifiers,
      )
