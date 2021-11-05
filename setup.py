from distutils.core import setup
import os

def version_reader(path):
    for line in open(path,"rt").read(1024).split("\n"):
        if line.startswith("VERSION"):
            return line.split("=")[1].strip().replace('"',"")

version = version_reader(os.path.join("tsmark","__init__.py"))
setup(
    name="tsmark",
    packages=["tsmark"],
    version=version,
    description="Video timestamp marking.",
    author="Ville Rantanen",
    author_email="ville.q.rantanen@gmail.com",
    keywords=["video"],
    entry_points={
        "console_scripts": [
            "tsmark=tsmark:main",
        ],
    },
    install_requires = [
        'opencv-python==4.5.3.56'
    ]
)
