from distutils.dir_util import copy_tree
import hashlib
import logging
import os
import pathlib
import shutil
import tempfile
import uuid

from bs4 import BeautifulSoup

from le_utils.constants import format_presets

from ricecooker.classes import nodes, files, licenses
from ricecooker.utils.zip import create_predictable_zip
from ricecooker.utils.browser import preview_in_browser


ENTRYPOINT_TEMPLATE = """
<!DOCTYPE html>
<html>
   <head>
      <title>HTML Meta Tag</title>
      <meta http-equiv = "refresh" content = "0; url = {}" />
   </head>
   <body>
   </body>
</html>
"""


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
            source_id=str(uuid.uuid4()),
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


def make_topic_tree_with_entrypoints(license, imscp_zip, imscp_dict, ims_dir,
        temp_dir=None, parent_id=None, node_options=None):
    """Return a TopicTree node from a dict of some subset of an IMSCP manifest.

    The actual IMSCP zip is marked as a dependency, and the zip loaded by Kolibri
    only contains an index.html file that redirects to the entrypoint defined in
    the manifest. This minimizes the additional content generated for Kolibri,
    and also allows us to support content where multiple content nodes have entrypoints
    defined by parameters, e.g. index.html#chapter2, index.html#chapter3, etc.

    Ready to be uploaded via Ricecooker to Studio or used in Kolibri.

    Args:
        license - License to apply to content nodes.
        imscp_dict - Dict of IMSCP from extract_from_zip or extract_from_dir.
        ims_dir (string) - Path of directory of IMSCP
        scraper_class (webmixer.HTMLPageScraper class, optional):
            Webmixer scraper class to use for pruning an HTML page.
        temp_dir (string, optional) - Full path of temporary directory to
            output HTML zip files to.
        parent_id (string, optional) - Parent ID string to concatenate to source ID.
        node_options (dict, optional) - Options to pass to content renderer in Kolibri.
    """
    if not temp_dir:
        temp_dir = tempfile.tempdir

    source_id = imscp_dict['identifier']
    assert source_id, "{} has no identifier, parent id = {}".format(os.path.basename(imscp_zip), parent_id)
    if parent_id:
        source_id = '{}-{}'.format(parent_id, source_id)

    if imscp_dict.get('children'):
        topic_node = nodes.TopicNode(
            source_id=source_id,
            title=imscp_dict['title']
        )
        counter = 1
        for child in imscp_dict['children']:
            # We will get duplicate IDs if we don't have any ID set.
            if not child['identifier']:
                child['identifier'] = 'item{}'.format(counter)
            topic_node.add_child(make_topic_tree_with_entrypoints(
                    license, imscp_zip, child, ims_dir,
                    temp_dir=temp_dir, parent_id=source_id, node_options=node_options))
            counter += 1
        return topic_node
    else:
        if imscp_dict['type'] == 'webcontent':
            entrypoint_dir = os.path.join(temp_dir, 'entrypoint')
            if os.path.exists(entrypoint_dir):
                shutil.rmtree(entrypoint_dir)
            os.makedirs(entrypoint_dir)
            index = os.path.join(entrypoint_dir, "index.html")
            entrypoint_url = '/zipcontent/{}/{}'.format(os.path.basename(imscp_zip), imscp_dict['href'])
            f = open(index, "w", encoding="utf-8")
            f.write(ENTRYPOINT_TEMPLATE.format(entrypoint_url))
            f.close()

            zip_path = create_predictable_zip(entrypoint_dir)
            html5_node = nodes.HTML5AppNode(
                source_id=source_id,
                title=imscp_dict.get('title'),
                license=license,
                files=[files.HTMLZipFile(zip_path),
                       files.HTMLZipFile(imscp_zip, preset=format_presets.HTML5_DEPENDENCY_ZIP)],
            )
            if node_options is not None:
                extra_data = {'options': node_options}

                html5_node.extra_fields.update(extra_data)

            return html5_node
        else:
            logging.warning(
                    'Content type %s not supported yet.' % imscp_dict['type'])


def create_html5_app_node(license, content_dict, ims_dir, scraper_class=None,
        temp_dir=None, needs_scorm_support=False):
    if scraper_class:
        index_path = os.path.join(ims_dir, content_dict['index_file'])

        if '?' in index_path:
            index_path = index_path.split('?')[0]
        if '#' in index_path:
            index_path = index_path.split('#')[0]
        if content_dict['scormtype'] == 'sco' and needs_scorm_support:
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

            if content_dict.get('scormtype') == 'sco' and needs_scorm_support:
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
