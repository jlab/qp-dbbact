# -----------------------------------------------------------------------------
# Copyright (c) 2024--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import pandas as pd
from os.path import join
from os import makedirs
from qiita_client import ArtifactInfo
from shutil import copyfile
from json import loads


def validate(qclient, job_id, parameters, out_dir):
    """Validate and fix a new BIOM artifact

    Parameters
    ----------
    qclient : qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    parameters : dict
        The parameter values to validate and create the artifact
    out_dir : str
        The path to the job's output directory

    Returns
    -------
    bool, list of qiita_client.ArtifactInfo , str
        Whether the job is successful
        The artifact information, if successful
        The error message, if not successful
    """
    prep_id = parameters['template']
    files = loads(parameters['files'])
    a_type = parameters['artifact_type']

    qclient.update_job_step(job_id, "Step 1: Collecting prep information")
    prep_info = qclient.get("/qiita_db/prep_template/%s/data/" % prep_id)
    prep_info = prep_info['data']

    if a_type != "WordCloud":
        return (
            False, None,
            "Unknown artifact type %s. Supported types: WordCloud" % a_type)

    # convert filepaths from {'type': [str]} to [(str, type)]
    filepaths = [(fp, t) for t, fps in files.items() for fp in fps]

    return True, [ArtifactInfo(None, 'WordCloud', filepaths)], ""


def _generate_html_code(fp_stats, fp_fscores, url_dbbact):
    tbl_stats = pd.read_csv(fp_stats, sep="\t", index_col=0, header=None)[1]
    dbstats = ['<tr><th>URL</th><td><a href="%s">%s</a></td></tr>' % (
        url_dbbact, url_dbbact)]
    querystats = []
    for idx, val in tbl_stats.items():
        row = '<tr><th>%s</th><td>%s</td></tr>' % (idx, val)
        if idx.startswith('quer'):
            querystats.append(row)
        else:
            dbstats.append(row)

    tbl_fscores = pd.read_csv(fp_fscores, sep="\t", index_col=0)['F-score']
    fscores = []
    for idx, val in tbl_fscores.sort_values(ascending=False).items():
        style = ''
        if (idx[0] == '-'):
            style = ' style="color: orange;"'
        fscores.append('<tr%s><th>%s</th><td>%s</td></tr>' % (style, idx, val))

    def _indent(rows, indent=5):
        header = '\n' + ('    ' * indent)
        footer = '\n' + ('    ' * (indent-1))
        return header + ('\n%s' % ('    ' * indent)).join(rows) + footer

    html = """<!DOCTYPE html>
<html>
    <head>
        <link rel="stylesheet" href="%s" type="text/css">
        <link rel="stylesheet" href="%s" type="text/css">
    </head>
    <body>
        <div style="text-align: center;">
            <img src = "wordcloud.svg" alt="%s"/>
        </div>
        <div style="">
            <h1>Query Statistics</h1>
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Statistic</th><th>Value</th>
                    </tr>
                </thead>
                <tbody>%s</tbody>
            </table>

            <h1>Database Statistics</h1>
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Statistic</th><th>Value</th>
                    </tr>
                </thead>
                <tbody>%s</tbody>
            </table>
        </div>
        <div style="">
            <h1>F-Scores</h1>
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Term</th><th>F-Score</th>
                    </tr>
                </thead>
                <tbody>%s</tbody>
            </table>
        </div>
    </body>
</html>""" % ('support_files/css/bootstrap.min.css',
              'support_files/css/normalize.css',
              'dbBact wordcloud of F-scores for ASVs',
              _indent(querystats), _indent(dbstats), _indent(fscores))

    return html


def generate_html_summary(qclient, job_id, parameters, out_dir):
    """Generates the HTML summary of a BIOM artifact

    Parameters
    ----------
    qclient : qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    parameters : dict
        The parameter values to validate and create the artifact
    out_dir : str
        The path to the job's output directory

    Returns
    -------
    bool, None, str
        Whether the job is successful
        Ignored
        The error message, if not successful
    """

    # Step 1: gather file information from qiita using REST api
    artifact_id = parameters['input_data']
    qclient_url = "/qiita_db/artifacts/%s/" % artifact_id
    artifact_info = qclient.get(qclient_url)

    # 1a. getting the file paths
    filepaths = {k: [vv['filepath'] for vv in v]
                 for k, v in artifact_info['files'].items()}
    # 1.b get the artifact type_info
    artifact_type = artifact_info['type']

    if artifact_type != 'WordCloud':
        raise ValueError("This artifact is not a word cloud")
    for file in ['image_vector', 'tabular_text', 'log']:
        if file not in filepaths.keys():
            raise ValueError("Cannot find file '%s'" % file)
    html = _generate_html_code(filepaths['log'][0],
                               filepaths['tabular_text'][0], 'kurt')

    of_fp = join(out_dir, "artifact_%d.html" % artifact_id)
    with open(of_fp, 'w') as of:
        of.write(html)

    # copy support files
    fp_dir = join(out_dir, 'support_files/css/')
    makedirs(fp_dir, exist_ok=True)
    copyfile('support_files/css/bootstrap.min.css',
             join(fp_dir, 'bootstrap.min.css'))
    copyfile('support_files/css/normalize.css',
             join(fp_dir, 'normalize.css'))

    # Step 3: add the new file to the artifact using REST api
    success = True
    error_msg = ''
    try:
        qclient.patch(qclient_url, 'add', '/html_summary/',
                      value=dumps({'html': of_fp, 'dir:': fp_dir}))
    except Exception as e:
        success = False
        error_msg = str(e)

    return success, None, error_msg
