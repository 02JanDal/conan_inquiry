from setuptools import setup, find_packages

import conan_inquiry

setup(
    name='Conan-Inquiry',
    version=conan_inquiry.__version__,
    url='https://github.com/02JanDal/conan_inquiry',
    license='MIT',
    author='Jan Dalheimer',
    author_email='jan@dalheimer.de',
    description='An alternative to the official package search for conan packages',
    long_description=open('README.md', 'r').read(),
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools'
    ],
    package_data={
        'data': ['licenses/*', 'packages/*', 'web/*']
    },
    entry_points={
        'console_scripts': [
            'conan_inquiry = conan_inquiry.runner:main'
        ]
    },
    install_requires=open('requirements.txt', 'r').readlines()
)