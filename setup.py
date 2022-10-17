import setuptools
setuptools.setup(name='osif',
version='1.0',
description='OSINT Framework Console',
url='https://github.com/fr4nc1stein/osint-framework',
author='laet4x',
install_requires=['opencv-python', 'setuptools>=42','sploitkit>=0.5.5', 'terminaltables','vt-py', 'python-dotenv'
    ,'sublist3r'
    ,'dnspython'
    ,'win_unicode_console'
    ,'censys'
    ,'malwarebazaar'
    ,'python-Wappalyzer'
    ,'shodan'
    ,'requests_oauthlib'
    ,'jellyfish'],
author_email='laet4x@pehcon.org',
include_package_data=True,
package_data={'osif': ['osif/banners/*','.*.example', 'osif/db/*.txt', '*' ]},
packages=setuptools.find_packages(),
zip_safe=False)