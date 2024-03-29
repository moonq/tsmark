import argparse

from tsmark.video_annotator import Marker

VERSION = "0.4.7"


def get_options():

    parser = argparse.ArgumentParser(description="Video timestamping tool")
    parser.add_argument(
        "--ts",
        action="store",
        dest="timestamps",
        default=None,
        required=False,
        help="Comma separated list of predefined timestamps, in seconds, or HH:MM:SS.ss, or input CSV file. You can use the -o output file as input via --ts $( cut -d, -f1 ts.csv | xargs printf '%%s,' )",
    )
    parser.add_argument(
        "-o",
        action="store",
        dest="output",
        default=None,
        required=False,
        help="Save timestamps to a CSV file",
    )
    parser.add_argument(
        "--fps",
        action="store",
        dest="fps",
        default=None,
        required=False,
        type=float,
        help="Force FPS to play video",
    )
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument(action="store", dest="video")
    return parser.parse_args()


def main():
    opts = get_options()
    Marker(opts)
