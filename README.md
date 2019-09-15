# IMSCP

Library to convert an IMS Content Package (IMSCP) into Kolibri topic tree nodes.

A number of content sources, including CEDEC, Ceibal, Biblioredes, and LMS tools like Moodle, provide or export content in the format of an IMS Content Package (IMSCP). An IMSCP is a self-contained zip file, with all pages and associated resources inside the zip, along with a special file called imsmanifest.xml that contains a hierarchical structure of the content in a tree-like format.

This library extracts info from an IMSCP zip file and converts it into a ricecooker `TopicTree` node.

## Usage

#### `imscp.extract_from_zip`

Return a list of dicts of topic trees extracted from an IMSCP zip.

Args:

- `zip_file_path` - Path to IMSCP zip file.
- `license` - License to apply to content nodes.
- `extract_path` (optional) - Path of directory to extract zip file to. If not given, a temporary one will be created (but not cleaned up).

Sample usage:

```
import tempfile
from ricecooker.classes import licenses

license = licenses.CC_BY_SALicense(copyright_holder="CeDeC")
with tempfile.TemporaryDirectory() as extract_path:
    imscp_dict = extract_from_zip('eventos.zip', license, extract_path)
    for topic_dict in imscp_dict:
        print(topic_tree)
```


#### `imscp.extract_from_dir`

Return list of dicts of topic trees extracted from an IMSCP directory.

Like `extract_from_zip` but assumes zip file has been extracted already.

Args:

- `ims_dir` - Directory of extracted IMS Content Package.
- `license` - License to apply to content nodes.

Sample usage:

```
from ricecooker.classes import licenses

license = licenses.CC_BY_SALicense(copyright_holder="CeDeC")
imscp_dict = extract_from_dir('eventos', license)
for topic_dict in imscp_dict:
    print(topic_dict)
```


#### `ricecooker_utils.make_topic_tree`

Return a TopicTree node from a dict of some subset of an IMSCP manifest.

Ready to be uploaded via Ricecooker to Studio or used in Kolibri.

Args:

- `license` - License to apply to content nodes.
- `imscp_dict` - Dict of IMSCP from extract_from_zip or extract_from_dir.

Sample usage:

```
channel = self.get_channel()
imscp_dict = extract_from_dir('eventos', license)
for topic_dict in imscp_dict:
    topic_tree = make_topic_tree(license, topic_dict)
    channel.add_child(topic_tree)
```


## Example chefs

See example chefs using this library to upload to Studio in `examples/`.

Run from the base project directory like the following:

```
PYTHONPATH=. examples/educalab_chef.py -v --reset --token=yourtokenhere
```
