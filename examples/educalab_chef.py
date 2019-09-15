#!/usr/bin/env python

"""
Sample Sushi Chef that uses the IMSCP library to create and upload a channel
from the IMSCP zip file downloaded from upper-right dropdown on
http://procomun.educalab.es/es/ode/view/1465806119010

Direct link to IMSCP file:
https://agrega.educacion.es///export/es_2016062312_9100647/IMS_CP/Evento's_Solutions,_servicios_integrales_(ESSI)-IMS_CP.zip

Assumes the above is downloaded as "eventos.zip" in examples/ directory.
"""

import logging
import tempfile

from ricecooker.chefs import SushiChef
from ricecooker.classes import licenses

from imscp import extract_from_zip
from ricecooker_utils import make_topic_tree


class SampleEducalabChef(SushiChef):
    """
    The chef class that takes care of uploading channel to the content curation server.

    We'll call its `main()` method from the command line script.
    """
    channel_info = {
        'CHANNEL_SOURCE_DOMAIN': "sample-imscp.procomun.educalab.es",
        'CHANNEL_SOURCE_ID': "sample-imscp-procomun-educalab",
        'CHANNEL_TITLE': "Sample IMSCP upload from procomun.educalab.es",
        'CHANNEL_DESCRIPTION': "Sample Sushi Chef that uses the IMSCP library to upload a channel from procomun.educalab.es",
        'CHANNEL_LANGUAGE': "es",
    }

    def construct_channel(self, **kwargs):
        """
        Create ChannelNode and build topic tree.
        """
        # create channel
        channel = self.get_channel()

        license = licenses.CC_BY_SALicense(copyright_holder="CeDeC")
        logging.basicConfig(level=logging.DEBUG)

        with tempfile.TemporaryDirectory() as extract_path:
            imscp_dict = extract_from_zip('examples/eventos.zip', license, extract_path)
            for topic_dict in imscp_dict:
                topic_tree = make_topic_tree(license, topic_dict)
                print('Adding topic tree to channel:', topic_tree)
                channel.add_child(topic_tree)


        return channel


if __name__ == '__main__':
    """
    This code will run when the sushi chef is called from the command line.
    """
    chef = SampleEducalabChef()
    chef.main()
