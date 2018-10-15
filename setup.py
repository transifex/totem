from setuptools import find_packages, setup

setup(author='Transifex Devs',
      author_email='info@transifex.com',
      description='Software to verify GitHub PRs are compliant with the TEM',
      name='temcheck',
      version='0.1',
      packages=find_packages(),
      install_requires=[
          'Click',
          'PyGitHub==1.40a4'
      ],
      py_modules=['cli'],
      entry_points='''
         [console_scripts]
         temcheck=cli:main
      '''
)
