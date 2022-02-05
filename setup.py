from setuptools import setup, find_packages

setup(
    name="allocation",
    version="1.0",
    description="Python Package for Allocation Service.",
    author="Yassine Ayadi",
    author_email="ayadi.yas@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
