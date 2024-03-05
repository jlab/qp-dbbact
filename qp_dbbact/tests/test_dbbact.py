# -----------------------------------------------------------------------------
# Copyright (c) 2024--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main

from qiita_client.testing import PluginTestCase

from qp_dbbact.dbbact import (wordcloud_from_ASVs)


class dbbactTests(PluginTestCase):
    # def setUp(self):
    #     plugin("https://localhost:8383", 'register', 'ignored')
    #     self._clean_up_files = []
    #
    #     # saving current value of PATH
    #     self.oldpath = environ['PATH']
    #
    # def tearDown(self):
    #     # restore eventually changed PATH env var
    #     environ['PATH'] = self.oldpath
    #     for fp in self._clean_up_files:
    #         if exists(fp):
    #             if isdir(fp):
    #                 rmtree(fp)
    #             else:
    #                 remove(fp)

if __name__ == '__main__':
    main()
