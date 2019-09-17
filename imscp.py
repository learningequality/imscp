import itertools
import logging
from lxml import etree
import os
import re
import shutil
import tempfile
import zipfile


def extract_from_zip(zip_file_path, license, extract_path=None):
    """Return a list of dicts of topic trees extracted from an IMSCP zip.

    Args:
        zip_file_path - Path to IMSCP zip file.
        license - License to apply to content nodes.
        extract_path (optional) - Path of directory to extract zip file to. If
            not given, a temporary one will be created (but not cleaned up).
    """
    if not extract_path:
        extract_path = tempfile.mkdtemp()

    logging.info('Extracting zip file %s to %s' % (zip_file_path, extract_path))
    zip_file = zipfile.ZipFile(zip_file_path)
    zip_file.extractall(extract_path)
    return extract_from_dir(extract_path, license)


def extract_from_dir(ims_dir, license):
    """Return list of dicts of topic trees extracted from an IMSCP directory.

    Like extract_from_zip but assumes zip file has been extracted already.

    Args:
        ims_dir - Directory of extracted IMS Content Package.
        license - License to apply to content nodes.
    """
    logging.info('Parsing imsmanifest.xml in %s' % ims_dir)
    manifest_path = os.path.join(ims_dir, 'imsmanifest.xml')
    manifest_root = etree.parse(manifest_path).getroot()
    nsmap = manifest_root.nsmap

    logging.info('Extracting tree structure ...')
    logging.info('')

    # NOTE: Can there be multiple organizations?
    organization = manifest_root.find('organizations/organization', nsmap)
    organization_items = walk_items(organization)

    resources_elem = manifest_root.find('resources', nsmap)
    resources_dict = dict((r.get('identifier'), r) for r in resources_elem)

    collect_resources(license, organization_items, resources_dict, ims_dir)

    return organization_items


def walk_items(root):
    items_list = []

    for item in root.findall('item', root.nsmap):
        item_dict = dict(item.items())

        title_elem = item.find('title', item.nsmap)
        if title_elem is not None:
            item_dict['title'] = title_elem.text

        item_dict['children'] = walk_items(item)
        items_list.append(item_dict)

    return items_list


def collect_resources(license, items_list, resources_dict, ims_dir):
    for item in items_list:
        resource_elem = resources_dict[item['identifierref']]
        if item['children']:
            collect_resources(license, item['children'], resources_dict, ims_dir)
        else:
            item['type'] = resource_elem.get('type')
            if resource_elem.get('type') == 'webcontent':
                item['index_file'] = resource_elem.get('href')
                item['files'] = derive_content_files_dict(
                        resource_elem, resources_dict, ims_dir)


def derive_content_files_dict(resource_elem, resources_dict, ims_dir):
    nsmap = resource_elem.nsmap
    file_elements = resource_elem.findall('file', nsmap)
    file_paths = [fe.get('href') for fe in file_elements]
    dep_elements = resource_elem.findall('dependency', nsmap)
    dep_res_elements = (resources_dict[de.get('identifierref')] for de in dep_elements)
    dep_paths_list = (derive_content_files_dict(dre, resources_dict, ims_dir)
            for dre in dep_res_elements)
    dep_paths = list(itertools.chain(*dep_paths_list))  # Flatten
    return file_paths + dep_paths
