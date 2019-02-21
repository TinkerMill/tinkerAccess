import logging
from setuptools import setup, find_packages
from setuptools.command.install import install as _install

from tinker_access_client.PackageInfo import PackageInfo
from tinker_access_client.ServiceInstaller import ServiceInstaller


# noinspection PyClassHasNoInit,PyPep8Naming,PyBroadException
class install(_install):
    def run(self):
        _install.run(self)

        logger = logging.getLogger(__name__)
        try:
            msg = '\nInstalling the {0} service...'.format(PackageInfo.pip_package_name)
            self.execute(ServiceInstaller(self.install_lib).install, [], msg)

        except Exception as e:
            logger.error('The % service may not have installed correctly.\n', PackageInfo.pip_package_name)
            logger.error('Remediation maybe required.\n')
            raise e


config = {
    'name': PackageInfo.pip_package_name,
    'description': PackageInfo.pip_package_name,
    'author': 'Erick McQueen',
    'url': 'http://github.com/tinkerMill/tinkerAccess',
    'download_url': 'https://github.com/tinkerAccess/archive/v{0}.tar.gz'.format(PackageInfo.version),
    'author_email': 'ronn.mcqueen@tinkermill.org',
    'version': PackageInfo.version,
    'zip_safe': False,
    'install_requires': [
        'transitions==0.4.3',
        'daemonize==2.4.7',
        'requests>=2.20.0',
        'pyserial==3.2.1',
	'smbus2==0.1.4' ,
        'retry==0.9.2'
    ],

    'packages': find_packages(exclude=('tests*',)),
    'test_suite': 'nose.collector',
    'tests_require': [
        'backports.tempfile==1.0rc1',
        'transitions==0.4.3',
        'daemonize==2.4.7',
        'requests>=2.20.0',
        'pyserial==3.2.1',
        'mock==2.0.0',
        'nose==1.3.7'
    ],
    'entry_points': {
        'console_scripts': [
            '{0}={1}.Service:run'.format(PackageInfo.pip_package_name, PackageInfo.python_package_name)
        ]
    },
    'cmdclass': {
        'install': install
    }
}

setup(**config)
