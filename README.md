# IMSCP

Library to convert an IMS Content Package (IMSCP) into Kolibri topic tree nodes.

A number of content sources, including CEDEC, Ceibal, Biblioredes, and LMS tools like Moodle, provide or export content in the format of an IMS Content Package (IMSCP). An IMSCP is a self-contained zip file, with all pages and associated resources inside the zip, along with a special file called imsmanifest.xml that contains a hierarchical structure of the content in a tree-like format.

This library extracts info from an IMSCP zip file and converts it into a ricecooker `TopicTree` node.

## Usage

#### `imscp.extract_from_zip`

Extract metadata and topic tree info from an IMSCP zip.

Return a dict `{'metadata': {...}, 'organizations': [list of topic dicts]}`

Args:

- `zip_file_path` - Path to IMSCP zip file.
- `license` - License to apply to content nodes.
- `extract_path` (optional) - Path of directory to extract zip file to. If not given, a temporary one will be created (but not cleaned up).

Sample usage:

```
import pprint
import tempfile
from ricecooker.classes import licenses

license = licenses.CC_BY_SALicense(copyright_holder="CeDeC")
with tempfile.TemporaryDirectory() as extract_path:
    imscp_dict = extract_from_zip('eventos.zip', license, extract_path)
    pprint.pprint(imscp_dict['metadata'])
    for topic_dict in imscp_dict['organizations']:
        pprint.pprint(topic_dict)
```


#### `imscp.extract_from_dir`

Extract metadata and topic tree info from an IMSCP directory.

Return a dict `{'metadata': {...}, 'organizations': [list of topic dicts]}`

Like `extract_from_zip` but assumes zip file has been extracted already.

Args:

- `ims_dir` - Directory of extracted IMS Content Package.
- `license` - License to apply to content nodes.

Sample usage:

```
from ricecooker.classes import licenses

license = licenses.CC_BY_SALicense(copyright_holder="CeDeC")
imscp_dict = extract_from_dir('eventos', license)
print('metadata', imscp_dict['metadata'])
for topic_dict in imscp_dict['organizations']:
    print(topic_dict)
```


#### `ricecooker_utils.make_topic_tree`

Return a TopicTree node from a dict of some subset of an IMSCP manifest.

Ready to be uploaded via Ricecooker to Studio or used in Kolibri.

By default, this will take the entire IMS directory and use that for each app uploaded. (Some imsmanifest.xml don't completely specify all required dependencies.) However, you can specify a Webmixer class to use, to use Webmixer to determine which files are needed and just package those with the app.

Args:

- `license` - License to apply to content nodes.
- `imscp_dict` - Dict of IMSCP from `extract_from_zip` or `extract_from_dir`.
- `ims_dir (string)` - Path of directory of IMSCP
- `scraper_class (webmixer.HTMLPageScraper class, optional)` - Webmixer scraper class to use for pruning an HTML page.
- `temp_dir (string, optional)` - Full path of temporary directory to output HTML zip files to.

Sample usage with Webmixer:

```
from webmixer.scrapers.pages.base import DefaultScraper

channel = self.get_channel()
imscp_dict = extract_from_dir('eventos', license)
for topic_dict in imscp_dict['organizations']:
    topic_tree = make_topic_tree(license, topic_dict, 'eventos',
        scraper_class=DefaultScraper)
    channel.add_child(topic_tree)
```


## Example chefs

See example chefs using this library to upload to Studio in `examples/`.

Run from the base project directory like the following:

```
PYTHONPATH=. examples/educalab_chef.py -v --reset --token=yourtokenhere
```
