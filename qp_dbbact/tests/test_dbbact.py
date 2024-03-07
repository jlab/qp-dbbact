# -----------------------------------------------------------------------------
# Copyright (c) 2024--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import main
from os import environ
from os.path import join
from shutil import copyfile
from tempfile import mkstemp, mkdtemp
from json import dumps, load
import urllib.parse

from qiita_client.testing import PluginTestCase

from qp_dbbact import plugin
from qp_dbbact.dbbact import (wordcloud_from_ASVs)

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class WordcloudFromASVsTests(PluginTestCase):
    def setUp(self):
        # from qiita_client import QiitaClient
        # qclient = QiitaClient("https://localhost:21174", '19ndkO3oMKsoChjVVWluF7QkxHRfYhTKSFbAVt8IhK7gZgDaO4', 'J7FfQ7CQdOxuKhQAf1eoGgBAE81Ns8Gu3EKaWFm3IO2JKhAmmCWZuabe0O5Mp28s1', server_cert='/home/qiita/Git/qiita-spots/qiita/qiita_core/support_files/ci_rootca.crt')
        plugin("https://localhost:8383", 'register', 'ignored')
        self._clean_up_files = []

        self.params = {
            'dbBact server URL': urllib.parse.quote_plus('http://dbbact.org'),
            'Minimum ASV sample occurence in feature-table': 0.333,
            'Wordcloud width': 400,
            'Wordcloud height': 200,
            'Wordcloud background color': "white",
            'Wordcloud relative scaling': float(1/2),
        }

        # saving current value of PATH
        self.oldpath = environ['PATH']


    def tearDown(self):
        # restore eventually changed PATH env var
        environ['PATH'] = self.oldpath
        for fp in self._clean_up_files:
            if exists(fp):
                if isdir(fp):
                    rmtree(fp)
                else:
                    remove(fp)

    # def test_deblur_origin(self):
    #     # inserting new prep template
    #     prep_info_dict = {
    #         'SKB1.640202': {
    #             'description_prep': 'SKB1', 'platform': 'Illumina'},
    #         'SKB7.640196': {
    #             'description_prep': 'SKB7', 'platform': 'Illumina'},
    #         'SKB8.640193': {
    #             'description_prep': 'SKB8', 'platform': 'Illumina'}
    #     }
    #     data = {'prep_info': dumps(prep_info_dict),
    #             # magic #1 = testing study
    #             'study': 1,
    #             'data_type': '16S'}
    #     pid = self.qclient.post('/apitest/prep_template/', data=data)['prep']
    #
    #     # inserting artifacts
    #     artifact_tmp_dir = mkdtemp()
    #     self._clean_up_files.append(artifact_tmp_dir)
    #     final_biom_hit = join(artifact_tmp_dir, 'reference-hit.biom')
    #     copyfile('support_files/tiny_16srefhit/remapped_reference-hit.biom', final_biom_hit)
    #     final_seqs_hit = join(artifact_tmp_dir, 'reference-hit.seqs.fa')
    #     copyfile('support_files/tiny_16srefhit/remapped_reference-hit.seqs.fa', final_seqs_hit)
    #     fp_phylogeny = join(artifact_tmp_dir, 'insertion_tree.relabelled.tre')
    #     copyfile('support_files/tiny_16srefhit/remapped_insertion_tree.relabelled.tre', fp_phylogeny)
    #     data = {
    #         'filepaths': dumps([(final_biom_hit, 'biom'),
    #                             (final_seqs_hit, 'preprocessed_fasta'),
    #                             (fp_phylogeny, 'plain_text')]),
    #         'type': "BIOM",
    #         'name': "deblur reference hit table",
    #         'prep': pid}
    #     aid = self.qclient.post('/apitest/artifact/', data=data)['artifact']
    #     self.params['deblur BIOM table'] = aid
    #
    #     # register processing job
    #     data = {'user': 'demo@microbio.me',
    #             'command': dumps([plugin.name, plugin.version, 'Wordcloud from ASV sequences 6']),
    #             'status': 'running',
    #             'parameters': dumps(self.params)}
    #     jid = self.qclient.post('/apitest/processing_job/', data=data)['job']
    #
    #     # execute processing job
    #     out_dir = mkdtemp()
    #     self._clean_up_files.append(out_dir)
    #     success, ainfo, msg = wordcloud_from_ASVs(self.qclient, jid, self.params, out_dir)

    def test_success(self):
        # inserting new prep template
        prep_info_dict = {
            'SKB1.640202': {
                'description_prep': 'SKB1', 'platform': 'Illumina'},
            'SKB7.640196': {
                'description_prep': 'SKB7', 'platform': 'Illumina'},
            'SKB8.640193': {
                'description_prep': 'SKB8', 'platform': 'Illumina'}
        }
        data = {'prep_info': dumps(prep_info_dict),
                # magic #1 = testing study
                'study': 1,
                'data_type': '16S'}
        pid = self.qclient.post('/apitest/prep_template/', data=data)['prep']

        # inserting artifacts
        artifact_tmp_dir = mkdtemp()
        self._clean_up_files.append(artifact_tmp_dir)
        final_biom_hit = join(artifact_tmp_dir, 'reference-hit.biom')
        copyfile('support_files/tiny_16srefhit/remapped_reference-hit.biom', final_biom_hit)
        final_seqs_hit = join(artifact_tmp_dir, 'reference-hit.seqs.fa')
        copyfile('support_files/tiny_16srefhit/remapped_reference-hit.seqs.fa', final_seqs_hit)
        fp_phylogeny = join(artifact_tmp_dir, 'insertion_tree.relabelled.tre')
        copyfile('support_files/tiny_16srefhit/remapped_insertion_tree.relabelled.tre', fp_phylogeny)
        data = {
            'filepaths': dumps([(final_biom_hit, 'biom'),
                                (final_seqs_hit, 'preprocessed_fasta'),
                                (fp_phylogeny, 'plain_text')]),
            'type': "BIOM",
            'name': "deblur reference hit table",
            'prep': pid}
        aid = self.qclient.post('/apitest/artifact/', data=data)['artifact']
        self.params['deblur BIOM table'] = aid

        # register processing job
        data = {'user': 'demo@microbio.me',
                'command': dumps([plugin.name, plugin.version, 'Wordcloud from ASV sequences 6']),
                'status': 'running',
                'parameters': dumps(self.params)}
        jid = self.qclient.post('/apitest/processing_job/', data=data)['job']

        # execute processing job
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)
        success, ainfo, msg = wordcloud_from_ASVs(self.qclient, jid, self.params, out_dir)

        self.assertEqual("", msg)
        self.assertTrue(success)

        self.assertEqual(1, len(ainfo))
        self.assertEqual("BIOM", ainfo[0].artifact_type)
        self.assertEqual("dbBact wordcloud", ainfo[0].output_name)

        self.assertEqual(
            [(join(out_dir, 'wordcloud.png'), 'biom'),
             (join(out_dir, 'wordcloud.svg'), 'biom'),
             (join(out_dir, 'fscores.tsv'), 'plain_text'),
             (join(out_dir, 'stats.tsv'), 'plain_text')], ainfo[0].files)


if __name__ == '__main__':
    main()
