# -----------------------------------------------------------------------------
# Copyright (c) 2024--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from unittest import TestCase, main
from os import environ, remove
from os.path import join, exists, isdir
from shutil import copyfile, rmtree
from tempfile import mkdtemp
from json import dumps
import urllib.parse

from qiita_client.testing import PluginTestCase

from qp_dbbact import plugin
from qp_dbbact.dbbact import (wordcloud_from_ASVs, _get_color)

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class WordcloudFromASVsTests(PluginTestCase):
    def setUp(self):
        plugin("https://localhost:8383", 'register', 'ignored')
        self._clean_up_files = []

        self.params = {
            'dbBact server URL': urllib.parse.quote_plus('http://dbbact.org'),
            'dbBact api URL': urllib.parse.quote_plus('http://api.dbbact.org'),
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

    def test_noDeblurBIOM(self):
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
        copyfile('support_files/tiny_16srefhit/remapped_reference-hit.biom',
                 final_biom_hit)
        final_seqs_hit = join(artifact_tmp_dir, 'reference-hit.seqs.fa')
        copyfile('support_files/tiny_16srefhit/remapped_reference-hit.seqs.fa',
                 final_seqs_hit)
        fp_phylogeny = join(artifact_tmp_dir, 'insertion_tree.relabelled.tre')
        copyfile(('support_files/tiny_16srefhit/'
                  'remapped_insertion_tree.relabelled.tre'), fp_phylogeny)
        data = {
            'filepaths': dumps([(final_biom_hit, 'biom'),
                                (final_seqs_hit, 'preprocessed_fasta'),
                                (fp_phylogeny, 'plain_text')]),
            'type': "BIOM",
            'name': "NOT A deblur reference hit table",
            'prep': pid}
        aid = self.qclient.post('/apitest/artifact/', data=data)['artifact']
        self.params['deblur BIOM table'] = aid

        # register processing job
        data = {'user': 'demo@microbio.me',
                'command': dumps([plugin.name,
                                  plugin.version,
                                  'Wordcloud from ASV sequences']),
                'status': 'running',
                'parameters': dumps(self.params)}
        jid = self.qclient.post('/apitest/processing_job/', data=data)['job']

        # execute processing job
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)
        success, ainfo, msg = wordcloud_from_ASVs(
            self.qclient, jid, self.params, out_dir)

        self.assertEqual(
            ('Currently, dbBact queries within Qiita are only possible'
             ' for artifacts that have been produced via "deblur".'), msg)
        self.assertFalse(success)

    def test_lackingBIOMfile(self):
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
        copyfile('support_files/tiny_16srefhit/remapped_reference-hit.biom',
                 final_biom_hit)
        final_seqs_hit = join(artifact_tmp_dir, 'reference-hit.seqs.fa')
        copyfile('support_files/tiny_16srefhit/remapped_reference-hit.seqs.fa',
                 final_seqs_hit)
        fp_phylogeny = join(artifact_tmp_dir, 'insertion_tree.relabelled.tre')
        copyfile(('support_files/tiny_16srefhit/'
                  'remapped_insertion_tree.relabelled.tre'), fp_phylogeny)
        data = {
            'filepaths': dumps([(final_seqs_hit, 'preprocessed_fasta'),
                                (fp_phylogeny, 'plain_text')]),
            'type': "BIOM",
            'name': "deblur reference hit table",
            'prep': pid}
        aid = self.qclient.post('/apitest/artifact/', data=data)['artifact']
        self.params['deblur BIOM table'] = aid

        # register processing job
        data = {'user': 'demo@microbio.me',
                'command': dumps([plugin.name,
                                  plugin.version,
                                  'Wordcloud from ASV sequences']),
                'status': 'running',
                'parameters': dumps(self.params)}
        jid = self.qclient.post('/apitest/processing_job/', data=data)['job']

        # execute processing job
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)
        success, ainfo, msg = wordcloud_from_ASVs(
            self.qclient, jid, self.params, out_dir)

        self.assertEqual("The input artifact is lacking the biom file.", msg)
        self.assertFalse(success)

    def test_nonDNAasv_sequence(self):
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
        copyfile('support_files/nonDNAseq.biom',
                 final_biom_hit)
        final_seqs_hit = join(artifact_tmp_dir, 'reference-hit.seqs.fa')
        copyfile('support_files/tiny_16srefhit/remapped_reference-hit.seqs.fa',
                 final_seqs_hit)
        fp_phylogeny = join(artifact_tmp_dir, 'insertion_tree.relabelled.tre')
        copyfile(('support_files/tiny_16srefhit/'
                  'remapped_insertion_tree.relabelled.tre'), fp_phylogeny)
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
                'command': dumps([plugin.name,
                                  plugin.version,
                                  'Wordcloud from ASV sequences']),
                'status': 'running',
                'parameters': dumps(self.params)}
        jid = self.qclient.post('/apitest/processing_job/', data=data)['job']

        # execute processing job
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)
        success, ainfo, msg = wordcloud_from_ASVs(
            self.qclient, jid, self.params, out_dir)

        self.assertEqual(('One or more ASV sequences contains at least one '
                          'non-DNA character.'), msg)
        self.assertFalse(success)

    def test_serverErrorStatus(self):
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
        copyfile('support_files/tiny_16srefhit/remapped_reference-hit.biom',
                 final_biom_hit)
        final_seqs_hit = join(artifact_tmp_dir, 'reference-hit.seqs.fa')
        copyfile('support_files/tiny_16srefhit/remapped_reference-hit.seqs.fa',
                 final_seqs_hit)
        fp_phylogeny = join(artifact_tmp_dir, 'insertion_tree.relabelled.tre')
        copyfile(('support_files/tiny_16srefhit/'
                  'remapped_insertion_tree.relabelled.tre'), fp_phylogeny)
        data = {
            'filepaths': dumps([(final_biom_hit, 'biom'),
                                (final_seqs_hit, 'preprocessed_fasta'),
                                (fp_phylogeny, 'plain_text')]),
            'type': "BIOM",
            'name': "deblur reference hit table",
            'prep': pid}
        aid = self.qclient.post('/apitest/artifact/', data=data)['artifact']
        self.params['deblur BIOM table'] = aid

        # this should lead to an empty ASV list
        self.params['Minimum ASV sample occurence in feature-table'] = 99

        # register processing job
        data = {'user': 'demo@microbio.me',
                'command': dumps([plugin.name,
                                  plugin.version,
                                  'Wordcloud from ASV sequences']),
                'status': 'running',
                'parameters': dumps(self.params)}
        jid = self.qclient.post('/apitest/processing_job/', data=data)['job']

        # execute processing job
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)
        success, ainfo, msg = wordcloud_from_ASVs(
            self.qclient, jid, self.params, out_dir)

        self.assertTrue('None of the 0 sequences were found in dbBact' in msg)

        # revert to normal
        self.params['Minimum ASV sample occurence in feature-table'] = 1/3
        self.params['deblur BIOM table'] = aid
        # set to a wrong but existing URL
        correct_value = self.params['dbBact server URL']
        self.params['dbBact server URL'] = 'https://www.google.com'
        data = {'user': 'demo@microbio.me',
                'command': dumps([plugin.name,
                                  plugin.version,
                                  'Wordcloud from ASV sequences']),
                'status': 'running',
                'parameters': dumps(self.params)}
        jid = self.qclient.post('/apitest/processing_job/', data=data)['job']
        success, ainfo, msg = wordcloud_from_ASVs(
            self.qclient, jid, self.params, out_dir)
        self.assertFalse(success)
        # revert URL
        self.params['dbBact server URL'] = correct_value

        self.params['dbBact api URL'] = 'https://www.google.com'
        self.params['deblur BIOM table'] = aid
        data = {'user': 'demo@microbio.me',
                'command': dumps([plugin.name,
                                  plugin.version,
                                  'Wordcloud from ASV sequences']),
                'status': 'running',
                'parameters': dumps(self.params)}
        jid = self.qclient.post('/apitest/processing_job/', data=data)['job']
        success, ainfo, msg = wordcloud_from_ASVs(
            self.qclient, jid, self.params, out_dir)
        self.assertFalse(success)

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
        copyfile('support_files/tiny_16srefhit/remapped_reference-hit.biom',
                 final_biom_hit)
        final_seqs_hit = join(artifact_tmp_dir, 'reference-hit.seqs.fa')
        copyfile('support_files/tiny_16srefhit/remapped_reference-hit.seqs.fa',
                 final_seqs_hit)
        fp_phylogeny = join(artifact_tmp_dir, 'insertion_tree.relabelled.tre')
        copyfile(('support_files/tiny_16srefhit/'
                  'remapped_insertion_tree.relabelled.tre'), fp_phylogeny)
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
                'command': dumps([plugin.name,
                                  plugin.version,
                                  'Wordcloud from ASV sequences']),
                'status': 'running',
                'parameters': dumps(self.params)}
        jid = self.qclient.post('/apitest/processing_job/', data=data)['job']

        # execute processing job
        out_dir = mkdtemp()
        self._clean_up_files.append(out_dir)
        success, ainfo, msg = wordcloud_from_ASVs(
            self.qclient, jid, self.params, out_dir)

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


class GetColorTests(TestCase):
    def test_get_color(self):
        obs = _get_color(
            'hallo', 11, None, None, None, None, {'hallo': 0.00079},
            recall={}, precision={}, term_count={})
        self.assertEqual('#7b73b5', obs)

        obs = _get_color(
            '-hallo', 11, None, None, None, None, {'-hallo': 0.00079},
            recall={}, precision={}, term_count={})
        self.assertEqual('#ec620f', obs)

        obs = _get_color(
            'hallo', 11, None, None, None, None, {'hallo': 0.00079},
            recall={}, precision={}, term_count={'hallo': 3})
        self.assertEqual('#a4a1cc', obs)


if __name__ == '__main__':
    main()
