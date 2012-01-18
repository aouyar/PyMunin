import os
import pkgutil
import shutil
from setuptools import setup, find_packages
from  setuptools.command.install  import  install  as  _install
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


SCRIPT_PREFIX = u'pymunin'
console_scripts = []
script_names = []
for importer, modname, ispkg in pkgutil.iter_modules(pymunin.plugins.__path__):
    params = {
        'script_name': u'%s-%s' % (SCRIPT_PREFIX, modname),
        'script_path': u'%s.%s' % (pymunin.plugins.__name__,  modname),
        'entry': 'main',
    }
    script_names.append(modname)
    console_scripts.append(u'%(script_name)s = %(script_path)s:%(entry)s' % params)


class install(_install): 
    "Extend base install class to provide a post-install step."

    def run(self): 
        _install.run(self)
        for name in script_names:
            # FIXME: This requires write permission to /usr/share/munin/plugins
            # which is default owned by root
            source = os.path.join(self.install_scripts, u'%s-%s' % (SCRIPT_PREFIX, name))
            destination = os.path.join('/usr/share/munin/plugins', name)
            shutil.copy(source, destination)


setup(
    cmdclass={'install': install},
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
