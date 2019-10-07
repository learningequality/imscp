import itertools
import logging
import os
import re
import shutil
import tempfile
import zipfile

from lxml import etree
import xmltodict


def extract_from_zip(zip_file_path, license, extract_path=None):
    """Extract metadata and topic tree info from an IMSCP zip.

    Return a dict {'metadata': {...}, 'organizations': [list of topic dicts]}

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
    """Extract metadata and topic tree info from an IMSCP directory.

    Return a dict {'metadata': {...}, 'organizations': [list of topic dicts]}

    Like extract_from_zip but assumes zip file has been extracted already.

    Args:
        ims_dir - Directory of extracted IMS Content Package.
        license - License to apply to content nodes.
    """
    logging.info('Parsing imsmanifest.xml in %s' % ims_dir)
    manifest_path = os.path.join(ims_dir, 'imsmanifest.xml')
    manifest_root = etree.parse(manifest_path).getroot()
    nsmap = manifest_root.nsmap

    logging.info('Extracting tree structure ...\n')

    metadata_elem = manifest_root.find('metadata', nsmap)
    metadata = {}
    if metadata_elem is not None:
        metadata = collect_metadata(metadata_elem)

    resources_elem = manifest_root.find('resources', nsmap)
    resources_dict = dict((r.get('identifier'), r) for r in resources_elem)

    organizations = []
    for org_elem in manifest_root.findall('organizations/organization', nsmap):
        item_tree = walk_items(org_elem)
        collect_resources(license, item_tree, resources_dict, ims_dir)
        organizations.append(item_tree)

    return {
        'metadata': metadata,
        'organizations': organizations,
    }


def walk_items(root):
    root_dict = dict(root.items())

    title_elem = root.find('title', root.nsmap)
    if title_elem is not None:
        root_dict['title'] = title_elem.text

    metadata_elem = root.find('metadata', root.nsmap)
    if metadata_elem is not None:
        root_dict['metadata'] = collect_metadata(metadata_elem)

    children = []
    for item in root.findall('item', root.nsmap):
        children.append(walk_items(item))

    if children:
        root_dict['children'] = children

    return root_dict


def collect_metadata(metadata_elem):
    strip_ns_prefix(metadata_elem)
    strip_langstring(metadata_elem)
    metadata_dict = {}

    for tag in ('general', 'rights', 'educational', 'lifecycle'):
        elem = metadata_elem.find('lom/%s' % tag)
        if elem:
            metadata_dict.update(xmltodict.parse(etree.tostring(elem)))

    return metadata_dict


def strip_ns_prefix(tree):
    """Strip namespace prefixes from an LXML tree.

    From https://stackoverflow.com/a/30233635
    """
    for element in tree.xpath("descendant-or-self::*[namespace-uri()!='']"):
        element.tag = etree.QName(element).localname


def strip_langstring(tree):
    """Replace all langstring elements with their text value."""
    for ls in tree.xpath(".//langstring"):
        ls.tail = ls.text + ls.tail if ls.tail else ls.text
    etree.strip_elements(tree, 'langstring', with_tail=False)


def collect_resources(license, item, resources_dict, ims_dir):
    if item.get('children'):
        for child in item['children']:
            collect_resources(license, child, resources_dict, ims_dir)
    elif item.get('identifierref'):
        resource_elem = resources_dict[item['identifierref']]

        # Add all resource attrs to item dict
        for key, value in resource_elem.items():
            key_stripped = re.sub('^{.*}', '', key) # Strip any namespace prefix
            item[key_stripped] = value

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
