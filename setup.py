import os
import pkgutil
from setuptools import setup, find_packages
import pymunin
import pymunin.plugins


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''


console_scripts = []
for importer, modname, ispkg in pkgutil.iter_modules(pymunin.plugins.__path__):
    params = {
        'script_name': modname,
        'script_path': u'%s.%s' % (pymunin.plugins.__name__,  modname),
        'entry': 'main',
    }
    console_scripts.append(u'%(script_name)s = %(script_path)s:%(entry)s' % params)


setup( 
    name='PyMunin',
    version=pymunin.__version__,
    author=pymunin.__author__,
    author_email=pymunin.__email__,
    packages=find_packages(),
    include_package_data=True,
    url='http://aouyar.github.com/PyMunin',
    license=pymunin.__license__,
    description=u'Python Module for developing Munin Multigraph Monitoring Plugins.',
    classifiers=[
        'Topic :: System :: Monitoring',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
    ],
    long_description=read_file('README.markdown'),
    entry_points={'console_scripts': console_scripts},
)
