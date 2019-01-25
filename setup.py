from setuptools import find_packages, setup

import versioneer

setup(
    author='Transifex Devs',
    author_email='info@transifex.com',
    description=(
        'Software to verify that PRs and commits follow expected Quality Standards'
    ),
    name='totem',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    install_requires=[
        'Click',
        'PyGitHub==1.40a4',
        'pyaml==17.12.1',
        'gitpython==2.1.11',
    ],
    py_modules=['cli'],
    entry_points={'console_scripts': ['totem=cli:main']},
)
