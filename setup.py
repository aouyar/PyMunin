from __future__ import with_statement
import errno
import os
import pkgutil
import shutil
from setuptools import setup, find_packages
from  setuptools.command.install  import  install  as  _install
import pymunin #@UnusedImport
import pymunin.plugins


SCRIPT_PREFIX = u'pymunin'


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''


console_scripts = []
plugin_names = []

for importer, modname, ispkg in pkgutil.iter_modules(pymunin.plugins.__path__):
    params = {
        'script_name': u'%s-%s' % (SCRIPT_PREFIX, modname),
        'script_path': u'%s.%s' % (pymunin.plugins.__name__,  modname),
        'entry': 'main',
    }
    plugin_names.append(modname)
    console_scripts.append(u'%(script_name)s = %(script_path)s:%(entry)s' % params)


class install(_install): 
    "Extend base install class to provide a post-install step."

    def run(self): 
        _install.run(self)
        # Installing the plugins requires write permission to 
        # /usr/share/munin/plugins which is default owned by root
        munin_plugin_dir = u'/usr/share/munin/plugins'
        if os.path.exists(munin_plugin_dir):
            try:
                for name in plugin_names:
                    source = os.path.join(
                        self.install_scripts,
                        u'%s-%s' % (SCRIPT_PREFIX, name)
                    )
                    destination = os.path.join(munin_plugin_dir, name)
                    shutil.copy(source, destination)
            except IOError, e:
                if e.errno in  (errno.EACCES, errno.ENOENT):
                    # Access denied or file/directory not found.
                    print "*" * 78
                    if e.errno == errno.EACCES:
                        print ("You do not have permission to install the plugins to %s." 
                               % munin_plugin_dir)
                    if e.errno == errno.ENOENT:
                        print ("Failed installing the plugins to %s. "
                               "File or directory not found." % munin_plugin_dir)
                    script = os.path.join(self.install_scripts, 'pymunin-install')
                    with open(script, 'w') as f:
                        f.write('#!/bin/sh\n')
                        for name in plugin_names:
                            source = os.path.join(
                                self.install_scripts,
                                u'%s-%s' % (SCRIPT_PREFIX, name)
                            )
                            destination = os.path.join(munin_plugin_dir, name)
                            f.write('cp %s %s\n' % (source, destination))
                    os.chmod(script, 0755)
                    print ("You will need to copy manually using the script: %s\n"
                           "Example: sudo %s"
                           % (script, script))
                    print "*" * 78
                else:
                    # Raise original exception
                    raise


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
