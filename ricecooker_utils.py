import os
import shutil
import tempfile

from ricecooker.classes import nodes, files, licenses
from ricecooker.utils.zip import create_predictable_zip
from ricecooker.utils.browser import preview_in_browser


def make_topic_tree(license, imscp_dict):
    """Return a TopicTree node from a dict of some subset of an IMSCP manifest.

    Ready to be uploaded via Ricecooker to Studio or used in Kolibri.
    """
    if imscp_dict.get('children'):
        topic_node = nodes.TopicNode(
            source_id=imscp_dict['identifier'],
            title=imscp_dict['title']
        )
        for child in imscp_dict['children']:
            topic_node.add_child(make_topic_tree(license, child))
        return topic_node
    else:
        if imscp_dict['type'] == 'webcontent':
            return create_html5_app_node(license, imscp_dict)
        else:
            raise 'Content type %s not supported yet.' % imscp_dict['type']


def create_html5_app_node(license, content_dict):
    with tempfile.TemporaryDirectory() as destination:
        index_copy_path = os.path.join(destination, 'index.html')
        shutil.copyfile(content_dict['index_file'], index_copy_path)

        for file_path in content_dict['files']:
            shutil.copy(file_path, destination)

        #preview_in_browser(destination)

        zip_path = create_predictable_zip(destination)
        return nodes.HTML5AppNode(
            source_id=content_dict['identifier'],
            title=content_dict.get('title'),
            license=license,
            files=[files.HTMLZipFile(zip_path)],
        )
