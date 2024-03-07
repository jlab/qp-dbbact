# -----------------------------------------------------------------------------
# Copyright (c) 2024--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import requests
import matplotlib as mpl
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import urllib.parse
from os.path import join
import datetime
import pandas as pd

from biom import Table, load_table

from qiita_client import ArtifactInfo
from qiita_client.util import system_call

import qp_dbbact



# copied from https://github.com/amnona/dbbact-calour/blob/f463fb52a56231ef68a0fb1cb200dceadec5c97b/dbbact_calour/dbbact.py#L2472
#   smj 2024-03-06: replaced deprecated mpl.cm.get_cmap with matplotlib.colormaps[name]
def _get_color(word, font_size, position, orientation, font_path, random_state, fscore, recall, precision, term_count):
    '''Get the color for a wordcloud term based on the term_count and higher/lower

    If term starts with "-", it is lower in and colored red. otherwise colored blue
    If we have term_count, we use it to color from close to white(low count) to full color (>=10 experiments)

    Parameters
    ----------
    fscores: dict of {term(str): fscore(float)}
        between 0 and 1
    recall: dict of {term(str): recall score(float)}, optional
    precision: dict of {term(str): precision score(float)}, optional
    term_count: dict of {term(str): number of experiments with term(float)}, optional
        used to determine the color intensity


    Returns
    -------
    str: the color in hex "0#RRGGBB"
    '''
    if word in term_count:
        count = min(term_count[word], 10)
    else:
        count = 10

    if word[0] == '-':
        cmap = mpl.colormaps['Oranges']
        rgba = cmap(float(0.4 + count / 40), bytes=True)
    else:
        cmap = mpl.colormaps['Purples']
        rgba = cmap(float(0.4 + count / 40), bytes=True)

    red = format(rgba[0], '02x')
    green = format(rgba[1], '02x')
    blue = format(rgba[2], '02x')
    return '#%s%s%s' % (red, green, blue)


def wordcloud_from_ASVs(qclient, job_id, parameters, out_dir):
    """Query for enriched terms in dbBact for a set of ASV sequences.

    Parameters
    ----------
    qclient : qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    parameters : dict
        The parameter values to run F-score query against dbBact
    out_dir : str
        The path to the job's output directory

    Returns
    -------
    boolean, list, str
        The results of the job

    Notes
    -----
    The code first checks if the provided biom artifact was produced by deblur
    to ensure that the features are actual DNA sequences. To double check, we
    next test if a biom filepath is given. If so, the index is tested to contain
    only A C G T letters, i.e. are ASV sequences. Depending on the
    'Minimum ASV sample occurence in feature-table' parameter, a subset of
    features is used to query F-scores against the dbBact server. The result
    will be saved as a *.tsv file and rendered into a *.png and *.svg image.
    We also obtain some stats from the server about database size and query
    date and save that as stats.tsv for reference.
    """
    NUM_STEPS = 4

    # Step 1 check if the provided BIOM table is
    #   a) a result of deblur (can't to term enrichment for e.g. OTU IDs)
    #   b) the reference-hit and not the all table (as we don't need both)
    #   c) the target gene is 16S, 18S or ITS but nothing else
    qclient.update_job_step(job_id, "Step 1 of %i: Collecting information" % NUM_STEPS)
    artifact_id = parameters['deblur BIOM table']

    # removing input from parameters so it's not part of the final command
    del parameters['deblur BIOM table']

    # Get the artifact filepath information
    artifact_info = qclient.get("/qiita_db/artifacts/%s/" % artifact_id)

    # check artifact properties
    # only accept BIOM artifact that were produced via deblur (but not by DADA2 - which is not in Qiita yet, or pick_closed_OTUs)
    if artifact_info['name'] not in ['deblur final table', 'deblur reference hit table']:
        error_msg = 'Currently, dbBact queries within Qiita are only possible for artifacts that have been produced via "deblur".'
        return False, None, error_msg

    fps = {k: [vv['filepath'] for vv in v]
           for k, v in artifact_info['files'].items()}
    # ensure that artifact has a feature table as biom file
    if 'biom' not in fps:
        error_msg = 'The input artifact is lacking the biom file.'
        return False, None, error_msg

    feature_table = load_table(fps['biom'][0])
    features = list(feature_table.ids(axis='observation'))
    # check that all features are DNA sequences
    if len(set(''.join(features)) - {'A', 'C', 'G', 'T'}) > 0:
        error_msg = 'One or more ASV sequences contains at least one non-DNA character.'
        return False, None, error_msg

    # only consider ASVs/features that at least occur in XXX of the samples (default: 1/3)
    sel_features = [feature
                    for feature, occ in (feature_table.to_dataframe() > 0).sum(axis=1).items()
                    if occ >= feature_table.shape[1] * parameters['Minimum ASV sample occurence in feature-table']]
    qclient.update_job_step(job_id, "Step 2 of %i: query %s with %i features (total was %i)" % (NUM_STEPS, parameters['dbBact server URL'], len(sel_features), len(features)))

    dbbact = requests.get('%s/sequences_fscores' % urllib.parse.unquote_plus(parameters['dbBact server URL']), json={'sequences': sel_features})
    if dbbact.status_code != 200:
        return False, None, dbbact.content.decode('ascii')
    fscores = dbbact.json()

    qclient.update_job_step(job_id, "Step 3 of %i: generate wordcloud" % (NUM_STEPS))
    wc = WordCloud(width=parameters['Wordcloud width'], height=parameters['Wordcloud height'],
                   background_color=parameters['Wordcloud background color'], relative_scaling=parameters['Wordcloud relative scaling'],
                   stopwords=set(),
                   color_func=lambda *x, **y: _get_color(*x, **y, fscore=fscores, recall={}, precision={}, term_count={}))
    cloud = wc.generate_from_frequencies(fscores)

    qclient.update_job_step(job_id, "Step 4 of %i: render image" % (NUM_STEPS))
    fp_png = join(out_dir, 'wordcloud.png')
    DPI = 100
    fig = plt.figure(figsize=(parameters['Wordcloud width']/DPI, parameters['Wordcloud height']/DPI), dpi=DPI)
    plt.imshow(cloud)
    plt.axis("off")
    fig.tight_layout()
    fig.savefig(fp_png)
    fp_svg = join(out_dir, 'wordcloud.svg')
    with open(fp_svg, 'w') as SVG:
        SVG.write(cloud.to_svg(embed_font=True))

    # also save actual f-scores as table
    fp_fscores = join(out_dir, "fscores.tsv")
    pd.Series(fscores, name='F-score').to_csv(fp_fscores, sep="\t", index_label='term')

    # obtain some stats from dbBact about database volume
    dbbact_stats = requests.get('http://api.dbbact.org/stats/stats')
    if dbbact_stats.status_code != 200:
        return False, None, dbbact.content.decode('ascii')
    dbbact_stats = dbbact_stats.json()['stats']
    dbbact_stats['query_timestamp'] = str(datetime.datetime.now())
    fp_stats = join(out_dir, "stats.tsv")
    pd.Series(dbbact_stats).to_csv(fp_stats, sep="\t", header=None)

    ainfo = [ArtifactInfo('dbBact wordcloud', 'BIOM',
                          [(fp_png, 'biom'),
                           (fp_svg, 'biom'),
                           (fp_fscores, 'plain_text'),
                           (fp_stats, 'plain_text')])]

    return True, ainfo, ""
