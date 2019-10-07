from distutils.dir_util import copy_tree
import hashlib
import logging
import os
import pathlib
import shutil
import tempfile

from bs4 import BeautifulSoup

from ricecooker.classes import nodes, files, licenses
from ricecooker.utils.zip import create_predictable_zip
from ricecooker.utils.browser import preview_in_browser


def make_topic_tree(license, imscp_dict, ims_dir, scraper_class=None,
        temp_dir=None):
    """Return a TopicTree node from a dict of some subset of an IMSCP manifest.

    Ready to be uploaded via Ricecooker to Studio or used in Kolibri.

    Args:
        license - License to apply to content nodes.
        imscp_dict - Dict of IMSCP from extract_from_zip or extract_from_dir.
        ims_dir (string) - Path of directory of IMSCP
        scraper_class (webmixer.HTMLPageScraper class, optional):
            Webmixer scraper class to use for pruning an HTML page.
        temp_dir (string, optional) - Full path of temporary directory to
            output HTML zip files to.
    """
    if imscp_dict.get('children'):
        topic_node = nodes.TopicNode(
            source_id=imscp_dict['identifier'],
            title=imscp_dict['title']
        )
        for child in imscp_dict['children']:
            topic_node.add_child(make_topic_tree(
                    license, child, ims_dir, scraper_class=scraper_class,
                    temp_dir=temp_dir))
        return topic_node
    else:
        if imscp_dict['type'] == 'webcontent':
            return create_html5_app_node(license, imscp_dict, ims_dir,
                    scraper_class=scraper_class, temp_dir=temp_dir)
        else:
            logging.warning(
                    'Content type %s not supported yet.' % imscp_dict['type'])


def create_html5_app_node(license, content_dict, ims_dir, scraper_class=None,
        temp_dir=None):
    if scraper_class:
        index_path = os.path.join(ims_dir, content_dict['index_file'])

        if content_dict['scormtype'] == 'sco':
            add_scorm_support(index_path, ims_dir)

        index_uri = pathlib.Path(os.path.abspath(index_path)).as_uri()
        zip_name = '%s.zip' % hashlib.md5(index_uri.encode('utf-8')).hexdigest()
        temp_dir = temp_dir if temp_dir else tempfile.gettempdir()
        zip_path = os.path.join(temp_dir, zip_name)
        scraper = scraper_class(index_uri)
        scraper.download_file(zip_path)
        logging.info('Webmixer scraper outputted HTML app to %s' % zip_path)

    else:
        with tempfile.TemporaryDirectory() as destination:
            index_src_path = os.path.join(ims_dir, content_dict['index_file'])
            index_dest_path = os.path.join(destination, 'index.html')
            shutil.copyfile(index_src_path, index_dest_path)

            for file_path in content_dict['files']:
                shutil.copy(os.path.join(ims_dir, file_path), destination)

            if content_dict.get('scormtype') == 'sco':
                add_scorm_support(index_dest_path, destination)

            #preview_in_browser(destination)
            zip_path = create_predictable_zip(destination)

    return nodes.HTML5AppNode(
        source_id=content_dict['identifier'],
        title=content_dict.get('title'),
        license=license,
        files=[files.HTMLZipFile(zip_path)],
    )


def add_scorm_support(index_file_path, dest_dir):
    with open(index_file_path, 'r+') as index_file:
        index_contents = index_file.read()

        is_hot_potatoes = False
        doc = BeautifulSoup(index_contents, "html.parser")
        author_tag = doc.find('meta', attrs={'name': 'author'})
        if author_tag:
            is_hot_potatoes = 'Hot Potatoes' in author_tag.get('content', '')

        # Copy scorm JS files to a scorm/ dir in destination dir
        scorm_dir = pathlib.Path(os.path.join(dest_dir, 'le-scorm'))
        scorm_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy('src/scorm_handlers.js', scorm_dir)
        shutil.copy('src/scormAPI.js', scorm_dir)

        # Add links to those script tags into the <head> of the index.html
        scorm_api = doc.new_tag('script', src='le-scorm/scormAPI.js')
        scorm_handlers = doc.new_tag('script', src='le-scorm/scorm_handlers.js')
        if is_hot_potatoes:
            doc.head.append(scorm_api)
            doc.head.append(scorm_handlers)
        else:
            doc.head.insert(0, scorm_api)
            doc.head.insert(1, scorm_handlers)

        # Return modified index_contents
        index_file.seek(0)
        index_file.write(str(doc))
        index_file.truncate()
