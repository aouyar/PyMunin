import errno
import os
import pkgutil
import shutil
import glob
from setuptools import setup, find_packages
from  setuptools.command.install import install as _install
import pymunin #@UnusedImport
import pymunin.plugins


PYMUNIN_SCRIPT_FILENAME_PREFIX = u'pymunin'
PYMUNIN_PLUGIN_DIR = u'./share/munin/plugins'


def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''

if hasattr(pkgutil, "iter_modules"): # Python > 2.5
    modules = [modname for importer, modname, ispkg in 
               pkgutil.iter_modules(pymunin.plugins.__path__)]
else:
    modules = []
    for path in glob.glob(os.path.join(pymunin.plugins.__path__[0], 
                                       u'[A-Za-z]*.py')):
        file = os.path.basename(path)
        modules.append(file[:-3])

console_scripts = []
plugin_names = []
for modname in modules:
    params = {
        'script_name': u'%s-%s' % (PYMUNIN_SCRIPT_FILENAME_PREFIX, modname),
        'script_path': u'%s.%s' % (pymunin.plugins.__name__,  modname),
        'entry': 'main',
    }
    plugin_names.append(modname)
    console_scripts.append(u'%(script_name)s = %(script_path)s:%(entry)s' % params)


class install(_install): 
    "Extend base install class to provide a post-install step."

    def run(self): 
        _install.run(self)
        # Installing the plugins requires write permission to plugins directory
        # (Default: /usr/share/munin/plugins) which is default owned by root
        munin_plugin_dir = os.path.join(self.install_data, PYMUNIN_PLUGIN_DIR)
        print "Munin Plugin Directory: %s" % munin_plugin_dir
        if os.path.exists(munin_plugin_dir):
            try:
                for name in plugin_names:
                    source = os.path.join(
                        self.install_scripts,
                        u'%s-%s' % (PYMUNIN_SCRIPT_FILENAME_PREFIX, name)
                    )
                    destination = os.path.join(munin_plugin_dir, name)
                    print "Installing %s to %s." % (name, munin_plugin_dir)
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
                    f = open(script, 'w')
                    try:
                        f.write('#!/bin/sh\n')
                        for name in plugin_names:
                            source = os.path.join(
                                self.install_scripts,
                                u'%s-%s' % (PYMUNIN_SCRIPT_FILENAME_PREFIX, name)
                            )
                            destination = os.path.join(munin_plugin_dir, name)
                            f.write('cp %s %s\n' % (source, destination))
                    finally:
                        f.close()
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
