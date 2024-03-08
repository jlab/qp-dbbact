# -----------------------------------------------------------------------------
# Copyright (c) 2024--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from .wordcloud import validate, generate_html_summary
from qiita_client import QiitaTypePlugin, QiitaArtifactType

# INSERT INTO qiita.filepath_type (filepath_type) VALUES ('image_bitmap'), ('image_vector'), ('tabular_text');

# Define the supported artifact types
artifact_types = [
    QiitaArtifactType(
        'WordCloud',  # name
        'A dbBact word cloud',  # description
        False,  # can_be_submitted_to_ebi
        False,  # can_be_submitted_to_vamps
        False,  # is_user_uploadable
        [('image_bitmap', True),  # wordcloud as PNG
         ('image_vector', False),  # wordcloud as SVG
         ('tabular_text', True),  # F-scores
         ('log', True)])]  # stats

# Initialize the plugin
plugin = QiitaTypePlugin('WordCloud type', '2024.03',
                         'A dbBact word cloud',
                         validate, generate_html_summary,
                         artifact_types)
