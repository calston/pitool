from setuptools import setup, find_packages


setup(
    name="pitool",
    version='0.0.1',
    license='MIT',
    url="http://nowhere",
    description="pitool",
    author='Colin Alston',
    author_email='colin@imcol.in',
    packages=find_packages() + [
        "twisted.plugins",
    ],
    package_data={
        'twisted.plugins': ['twisted/plugins/pitool_plugin.py']
    },
    include_package_data=True,
    install_requires=[
        'Twisted',
        'PyYaml',
        'RPi.GPIO',
        'Autobahn',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
)
