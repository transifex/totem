from setuptools import find_packages, setup

setup(author='Transifex Devs',
      author_email='info@transifex.com',
      description='Software to verify that GitHub PRs are compliant with the TEM '
                  '(http://tem.transifex.com)',
      name='temcheck',
      version='0.1',
      packages=find_packages(),
      install_requires=[
          'Click',
          'PyGitHub==1.40a4',
          'pyaml==17.12.1',
      ],
      py_modules=['cli'],
      entry_points='''
         [console_scripts]
         temcheck=cli:main
      ''')
