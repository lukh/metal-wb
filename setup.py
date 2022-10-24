from setuptools import setup
import os
# from freecad.metalwb.version import __version__
# name: this is the name of the distribution.
# Packages using the same name here cannot be installed together

version_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 
                            "freecad", "metalwb", "version.py")
with open(version_path) as fp:
    exec(fp.read())

setup(name='freecad.metalwb',
      version=str(__version__),
      packages=['freecad',
                'freecad.metalwb'],
      maintainer="Veloma",
      maintainer_email="quentin.plisson@protonmail.com",
      url="https://framagit.org/Veloma/freecad-mecano-soudure/-/tree/main/MetalWB",
      description="template for a freecad extensions, installable with pip",
      install_requires=[], # should be satisfied by FreeCAD's system dependencies already
      include_package_data=True)
