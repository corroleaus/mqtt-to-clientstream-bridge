import os
import re

from setuptools import find_packages, setup

install_requires = ['tornado',
                    'paho-mqtt',
                    'pyyaml',
                    'daiquiri']


setup(name='mqtt-to-clientstream',
      version='0.1',
      description='mqtt-to-clientstream-bridge',
      platforms=['POSIX'],
      packages=find_packages(),
      include_package_data=True,
      install_requires=install_requires,
      zip_safe=False,
      entry_points={
        'console_scripts': [
            'mqtt-bridge = mqtt_to_clientstream.app:main',
        ]
    })