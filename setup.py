from setuptools import setup, find_packages

setup(
    name="proxy-ja4-project",
    version="1.0.0",
    description="Automated JA4 signature collection from TLS-inspecting proxies for proxy detection",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "cryptography>=41.0.0",
        "requests>=2.28.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/proxy-ja4-project",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: Security",
        "Topic :: System :: Networking :: Monitoring",
    ],
    keywords="proxy detection ja4 tls fingerprinting network security",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/proxy-ja4-project/issues",
        "Source": "https://github.com/yourusername/proxy-ja4-project",
        "Documentation": "https://github.com/yourusername/proxy-ja4-project#readme",
    },
    entry_points={
        "console_scripts": [
            "proxy-ja4=scripts.proxy_manager:main",
        ],
    },
)

