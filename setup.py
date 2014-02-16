from setuptools import setup, find_packages

setup(name='juju-docean',
      version="0.0.11",
      classifiers=[
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Operating System :: OS Independent'],
      author='Kapil Thangavelu',
      author_email='kapil.foss@gmail.com',
      description="Digital Ocean integration with juju",
      long_description=open("README.rst").read(),
      url='http://github/kapilt/juju-docean',
      license='BSD',
      packages=find_packages(),
      install_requires=["PyYAML", "dop", "requests"],
      entry_points={
          "console_scripts": [
              'juju-docean = juju_docean.cli:main']},
      )
