#!/usr/bin/env python

from lxml import etree
import os
import re
import shutil
import tempfile
import zipfile

from ricecooker.classes import nodes, files, licenses
from ricecooker.utils.zip import create_predictable_zip
from ricecooker.utils.browser import preview_in_browser


def extract_from_zip(zip_file_path, license):
    with tempfile.TemporaryDirectory() as extract_path:
        print('Extracting zip file %s to %s' % (zip_file_path, extract_path))
        zip_file = zipfile.ZipFile(zip_file_path)
        zip_file.extractall(extract_path)
        return extract_from_dir(extract_path, license)


def extract_from_dir(ims_dir, license):
    """Return a list of content nodes from an IMSCP directory."""
    print('Parsing imsmanifest.xml in %s' % ims_dir)
    manifest_path = os.path.join(ims_dir, 'imsmanifest.xml')
    manifest_root = etree.parse(manifest_path).getroot()
    nsmap = manifest_root.nsmap

    print('Extracting tree structure ...')
    print()

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
            if resource_elem.get('type') == 'webcontent':
                item['node'] = package_into_html5_app_node(
                        license, item, resource_elem, resources_dict, ims_dir)


def package_into_html5_app_node(license, item, resource_elem, resources_dict, ims_dir):
    nsmap = resource_elem.nsmap
    with tempfile.TemporaryDirectory() as destination:
        # Copy index file into our temporary directory and call it index.html
        index_path = os.path.join(ims_dir, resource_elem.get('href'))
        index_copy_path = os.path.join(destination, 'index.html')
        shutil.copyfile(index_path, index_copy_path)

        def copy_files(resource_elem):
            for file_elem in resource_elem.findall('file', nsmap):
                file_path = os.path.join(ims_dir, file_elem.get('href'))
                shutil.copy(file_path, destination)

            for dependency_elem in resource_elem.findall('dependency', nsmap):
                dep_res_elem = resources_dict[dependency_elem.get('identifierref')]
                copy_files(dep_res_elem)

        # Copy files and recursively copy files in dependency elements into temp
        # dir
        copy_files(resource_elem)

        #preview_in_browser(destination)

        zip_path = create_predictable_zip(destination)
        return nodes.HTML5AppNode(
            source_id=item['identifier'],
            title=item.get('title'),
            license=license,
            files=[files.HTMLZipFile(zip_path)],
        )


if __name__ == '__main__':
    license = licenses.SpecialPermissionsLicense(
        description="XXX",
        copyright_holder="XXXX"
    )
    extracted_dict = extract_from_zip('eventos.zip', license)
    import pprint
    pprint.pprint(extracted_dict)

