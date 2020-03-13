import os
import sys
from setuptools import setup, find_packages

root_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(root_dir, 'src')
sys.path.append(src_dir)

import imscp

requirements = [
    "lxml==4.4.1",
    "ricecooker>=0.6.33",
    "xmltodict==0.12.0",
    "webmixer>=0.0.1",
    "beautifulsoup4>=4.8.0"
]

setup(
    name='imscp-le',
    version=imscp.__version__,
    description="Utilities for handling IMSCP and SCORM files within LE's product ecosystem.",
    long_description_content_type="text/markdown",
    author="Learning Equality",
    author_email='dev@learningequality.org',
    url='https://github.com/learningequality/imscp',
    packages=find_packages('src'),
    package_dir={'':'src'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords=['imscp', 'ricecooker', 'scorm'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
