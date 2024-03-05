# -----------------------------------------------------------------------------
# Copyright (c) 2024--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import os

from qiita_client import QiitaPlugin, QiitaCommand

from .qp_dbbact import wordcloud_from_ASVs

__all__ = ['dbBact']

# Initialize the plugin
plugin = QiitaPlugin(
    'dbBact',  # name
    '2024.03',  # version
    'Achieving pan-microbiome biological insights',  # description
    publications=[('10.1093/nar/gkad527', '37326027')])  # publication

req_params = {'deblur reference hit table': ('artifact', ['BIOM'])}
opt_params = {
    'dbBact server URL': ['choice["http://dbbact.org"]', 'http://dbbact.org'],
    'Minimum ASV sample occurence in feature-table': ['float', '0.3333'],
    'Wordcloud width': ['integer', '400'],
    'Wordcloud height': ['integer', '200'],
    'Wordcloud background color': ['choice["white"]', 'white'],
    'Wordcloud relative scaling': ['float': '0.5'],
}

outputs = {'dbBact wordcloud': 'Wordcloud'}
dflt_param_set = {
    'Defaults': {
        'dbBact server URL': '"http://dbbact.org',
        'Minimum ASV sample occurence in feature-table': float(1/3),
        'Wordcloud width': 400,
        'Wordcloud height': 200,
        'Wordcloud background color': "white",
        'Wordcloud relative scaling': float(1/2),
    }
}
dbbact_wordcloud_cmd = QiitaCommand(
    'dbBact 2024.03',  # The command name
    'wordlouds from ASVs',  # The command description
    wordcloud_from_ASVs,  # function : callable
    req_params, opt_params, outputs, dflt_param_set)

plugin.register_command(dbbact_wordcloud_cmd)
