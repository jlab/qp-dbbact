# -----------------------------------------------------------------------------
# Copyright (c) 2024--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import urllib.parse

from qiita_client import QiitaPlugin, QiitaCommand

from .dbbact import wordcloud_from_ASVs

__all__ = ['dbbact']

# Initialize the plugin
plugin = QiitaPlugin(
    'dbBact',  # name
    '2024.03',  # version
    'Achieving pan-microbiome biological insights',  # description
    publications=[('10.1093/nar/gkad527', '37326027')])  # publication


req_params = {'deblur BIOM table': ('artifact', ['BIOM'])}
URL = urllib.parse.quote_plus('http://dbbact.org')

opt_params = {
    'dbBact server URL': ['choice:["%s"]' % URL, URL],
    'Minimum ASV sample occurence in feature-table': ['float', '0.333'],
    'Wordcloud width': ['integer', '400'],
    'Wordcloud height': ['integer', '200'],
    'Wordcloud background color': ['choice:["white"]', 'white'],
    'Wordcloud relative scaling': ['float', '0.5']
}

outputs = {'dbBact wordcloud': 'BIOM'}
dflt_param_set = {
    'Defaults': {
        'dbBact server URL': URL,
        'Minimum ASV sample occurence in feature-table': 0.333,
        'Wordcloud width': 400,
        'Wordcloud height': 200,
        'Wordcloud background color': "white",
        'Wordcloud relative scaling': float(1/2),
    }
}
dbbact_wordcloud_cmd = QiitaCommand(
    'Wordcloud from ASV sequences',  # The command name
    # The command description
    'Query for enriched terms in dbBact for a set of ASV sequences',
    wordcloud_from_ASVs,  # function : callable
    req_params, opt_params, outputs, dflt_param_set)

plugin.register_command(dbbact_wordcloud_cmd)
