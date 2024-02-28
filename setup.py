from setuptools import setup, find_packages

setup(
    name='transfermarktapi',
    version='0.1',  # Update this as necessary
    packages=find_packages(),
    install_requires=[
        # list all the packages that your package depends on
        # for example: 'requests', 'beautifulsoup4',
    ],
    author='Your Name',
    author_email='your.email@example.com',
    description='An unofficial API for Transfermarkt.',
    url='https://github.com/my-game-plan/transfermarkt-api',  # Project's URL
)