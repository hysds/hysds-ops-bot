from setuptools import setup, find_packages
import hysds_ops_bot

setup(
    name='hysds_ops_bot',
    version=hysds_ops_bot.__version__,
    long_description=hysds_ops_bot.__description__,
    url=hysds_ops_bot.__url__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'requests>=2.7.0',
    ]
)
