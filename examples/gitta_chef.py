#!/usr/bin/env python

"""
Sample Sushi Chef that uses the IMSCP library to create and upload a channel
from the IMSCP zip file downloaded from
http://www.elml.org/gitta_ims.zip

Assumes the above is downloaded as gitta_ims.zip in the examples/ directory.
"""

import logging
import tempfile

from ricecooker.chefs import SushiChef
from ricecooker.classes import licenses
from webmixer.scrapers.pages.base import DefaultScraper

from imscp import extract_from_zip
from ricecooker_utils import make_topic_tree


class SampleGittaChef(SushiChef):
    """
    The chef class that takes care of uploading channel to the content curation server.

    We'll call its `main()` method from the command line script.
    """
    channel_info = {
        'CHANNEL_SOURCE_DOMAIN': "sample-imscp.elml.org",
        'CHANNEL_SOURCE_ID': "sample-imscp-gitta",
        'CHANNEL_TITLE': "Sample IMSCP upload for GITTA from elml.org",
        'CHANNEL_DESCRIPTION': "Sample Sushi Chef that uses the IMSCP library to upload a channel for GITTA from elml.org",
        'CHANNEL_LANGUAGE': "en",
    }

    def construct_channel(self, **kwargs):
        """
        Create ChannelNode and build topic tree.
        """
        # create channel
        channel = self.get_channel()

        # TODO: This is the wrong license
        license = licenses.CC_BY_SALicense(copyright_holder="GITTA elml.org")
        logging.basicConfig(level=logging.INFO)

        with tempfile.TemporaryDirectory() as extract_path:
            imscp_dict = extract_from_zip(
                    'examples/gitta_ims.zip', license, extract_path)
            for topic_dict in imscp_dict['organizations']:
                topic_tree = make_topic_tree(license, topic_dict,
                        extract_path, scraper_class=DefaultScraper,
                        temp_dir=kwargs.get('temp_dir'))
                print('Adding topic tree to channel:', topic_tree)
                channel.add_child(topic_tree)

        print('--- metadata ---')
        import json
        print(json.dumps(imscp_dict['metadata'], indent=4))

        return channel


if __name__ == '__main__':
    """
    This code will run when the sushi chef is called from the command line.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        chef = SampleGittaChef(temp_dir=temp_dir)
        chef.main()
