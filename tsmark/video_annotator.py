import sys
import os
import cv2
import time
import argparse


def draw_time(frame, nr, fps, paused):
    left = 10
    bottom = 30

    formatted = "{} {}".format(
        format_time(nr, fps),
        "||" if paused else "",
    )
    shadow_text(frame, formatted, (left, bottom), 1.1, 2, (255, 255, 255))


def shadow_text(frame, text, pos, size, thicc, color):
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(
        frame,
        text,
        pos,
        font,
        size,
        (0, 0, 0),
        2 * thicc,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        text,
        pos,
        font,
        size,
        color,
        thicc,
        cv2.LINE_AA,
    )


def draw_bar(frame, nr, frames, fps, stamps):

    position = nr / frames
    bar_start = int(frame.shape[1] * 0.05)
    bar_end = int(frame.shape[1] * 0.95)
    bar_position = int(bar_start + position * (bar_end - bar_start))
    top = int(frame.shape[0] * 0.90)
    bottom = int(frame.shape[0] * 0.95)

    cv2.rectangle(frame, (bar_start, top), (bar_end, bottom), (255, 255, 255), 2)

    for ts in stamps:
        ts_pos = int(bar_start + ts / frames * (bar_end - bar_start))
        cv2.line(frame, (ts_pos, top), (ts_pos, bottom), (32, 32, 32), 3)
        cv2.line(frame, (ts_pos, top), (ts_pos, bottom), (84, 255, 63), 1)
    # cv2.line(frame, (bar_position, top), (bar_position, bottom), (32,32,32), 3)
    cv2.line(frame, (bar_position, top), (bar_position, bottom), (63, 84, 255), 1)

    shadow_text(frame, "1", (bar_start - 7, bottom + 20), 0.7, 2, (255, 255, 255))
    end_frame = format_time(frames - 1, fps)
    (text_width, text_height) = cv2.getTextSize(
        end_frame, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
    )[0]
    shadow_text(
        frame, end_frame, (bar_end - text_width, bottom + 20), 0.7, 2, (255, 255, 255)
    )


def draw_label(frame, nr, stamps):

    if not nr in stamps:
        return

    text = "{} #{}".format(nr + 1, stamps.index(nr) + 1)
    bottom = 60
    left = 10
    shadow_text(frame, text, (left, bottom), 1, 2, (63, 84, 255))


def calculate_step(step, last_move, video_length):

    now = time.time()
    last_move = [x for x in last_move if x[1] > now - 3]
    if len(last_move) == 0:
        return 1, []
    lefts = sum([1 for x in last_move if x[0] == "l"])
    rights = sum([1 for x in last_move if x[0] == "r"])
    if lefts > 0 and rights > 0:
        return 1, []
    count = max(lefts, rights)
    if count < 5:
        step = 1
    else:
        # x2 poly  from 5:5 -> 15:180
        step = 45 - 16.5 * count + 1.7 * count * count
        step = min(step, 0.1 * video_length)
    return int(step), last_move


def format_time(nframe, fps):

    seconds = int(nframe / fps)
    frame = nframe % fps
    parts = int(100 * (frame / fps))
    return time.strftime("%H:%M:%S", time.gmtime(seconds)) + ".%02d" % (parts)


def parse_time(timestr, fps):
    """return frames"""

    colon_count = len(timestr.split(":")) - 1
    if colon_count == 0:
        secs = float(timestr)
        return int(secs * fps)
    if colon_count == 1:
        mins, secstr = timestr.split(":", 1)
        sec = float(secstr)
        return int(fps * (int(mins) * 60 + sec))
    if colon_count == 2:
        hours, mins, secstr = timestr.split(":", 2)
        sec = float(secstr)
        return int(fps * (int(hours) * 3600 + int(mins) * 60 + sec))
    raise ValueError("Cannot parse time definition {}".format(timestr))


def print_timestamps(stamps, fps, filename):
    stamps.sort()
    print("# Timestamps:")
    for i, ts in enumerate(stamps):
        print("# {}: {} / {}".format(i + 1, format_time(ts, fps), ts + 1))
    if len(stamps) > 0:
        print(
            "ffmpeg -i '{}' -ss {} -to {} -c copy trimmed.mp4".format(
                filename,
                format_time(stamps[0], fps),
                format_time(stamps[-1], fps),
            )
        )


def get_options():

    parser = argparse.ArgumentParser(description="Video timestamping tool")
    parser.add_argument(
        "--ts",
        action="store",
        dest="timestamps",
        default=None,
        required=False,
        help="Comma separated list of predefined timestamps, in frame numbers, or HH:MM:SS.FF",
    )
    parser.add_argument(action="store", dest="video")
    return parser.parse_args()


def calculate_res(max_res, video_reader):

    video_res = [
        int(video_reader.get(cv2.CAP_PROP_FRAME_WIDTH)),
        int(video_reader.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    ]
    video_aspect = video_res[0] / video_res[1]
    if video_res[0] > max_res[0]:
        video_res[0] = int(max_res[0])
        video_res[1] = int(video_res[0] / video_aspect)

    if video_res[1] > max_res[1]:
        video_res[1] = int(max_res[1])
        video_res[0] = int(video_res[1] * video_aspect)
    return tuple(video_res)


def print_help():
    print(
        """Keyboard help:
          
Arrows left and right, Home, End 
          jump in video. Tap frequently to increase time step
, and .   move one frame at a time
z and c   move to previous or next mark
x         mark frame
space     pause
i         toggle HUD
q         quit
"""
    )


def main():
    try:
        opts = get_options()
        if not os.path.exists(opts.video):
            raise FileNotFoundError("Video file missing!")

        max_res = (1280, 720)
        video_reader = cv2.VideoCapture(opts.video)
        frames = int(video_reader.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video_reader.get(cv2.CAP_PROP_FPS)
        spf = 1.0 / fps
        video_res = calculate_res(max_res, video_reader)
        if opts.timestamps:
            stamps = sorted(
                [parse_time(ts.strip(), fps) for ts in opts.timestamps.split(",")]
            )
            stamps = [x for x in stamps if 0 <= x < frames]
            nr = stamps[0]
        else:
            stamps = []
            nr = 0

        paused = False
        read_next = False
        show_info = True
        frame_visu = []
        step = 1
        last_move = []
        video_length = frames * fps
        auto_step = True
        video_reader.set(cv2.CAP_PROP_POS_FRAMES, nr)

        print_help()

        while video_reader.isOpened():
            show_time = time.time()
            if (not paused) or read_next:
                ret, frame = video_reader.read()
            if ret == True:
                if paused:
                    draw_wait = 200
                else:
                    draw_wait = 1
                if (not paused) or read_next:
                    read_next = False
                frame_visu = cv2.resize(frame.copy(), video_res)
                nr_time = nr / fps
                if show_info:
                    draw_time(frame_visu, nr, fps, paused)
                    draw_bar(frame_visu, nr, frames, fps, stamps)
                    draw_label(frame_visu, nr, stamps)

                cv2.imshow("tsmark", frame_visu)
                k = cv2.waitKey(draw_wait)
                if k & 0xFF == ord("q") or k & 0xFF == 27:
                    break
                if k & 0xFF == 32:  # space
                    paused = not paused

                if k & 0xFF == 80:  # home key
                    nr = 0

                if k & 0xFF == 87:  # end key
                    nr = frames - 1
                    paused = True

                if k & 0xFF == 83:  # right arrow
                    last_move.append(("r", time.time()))
                    if auto_step:
                        step, last_move = calculate_step(step, last_move, video_length)
                    nr = int((nr_time + step) * fps) - 1
                    read_next = True
                if k & 0xFF == ord("."):
                    paused = True
                    read_next = True
                if k & 0xFF == 81:  # left arrow
                    last_move.append(("l", time.time()))
                    if auto_step:
                        step, last_move = calculate_step(step, last_move, video_length)
                    nr = int((nr_time - step) * fps) - 1
                    read_next = True
                if k & 0xFF == ord(","):
                    paused = True
                    nr -= 2
                    read_next = True

                if k & 0xFF == ord("z"):  # move to previous ts
                    for ts in reversed(sorted(stamps)):
                        if ts < nr - 1:
                            nr = ts - 1
                            read_next = True
                            break
                if k & 0xFF == ord("c"):  # move to previous ts
                    for ts in sorted(stamps):
                        if ts > nr:
                            nr = ts - 1
                            read_next = True
                            break

                if k & 0xFF == ord("x"):  # toggle ts
                    if nr in stamps:
                        stamps.remove(nr)
                    else:
                        stamps.append(nr)
                    stamps.sort()
                if k & 0xFF == ord("i"):
                    show_info = not show_info
                if k & 0xFF == ord("h"):
                    print_help()

                if (not paused) or read_next:
                    nr += 1
                if nr < 0:
                    nr = 0
                if nr >= frames:
                    nr = frames - 1
                    paused = True
                if read_next:
                    video_reader.set(cv2.CAP_PROP_POS_FRAMES, nr)

                time_to_wait = spf - time.time() + show_time
                if time_to_wait > 0:
                    time.sleep(time_to_wait)

            else:
                nr = frames - 2
                video_reader.set(cv2.CAP_PROP_POS_FRAMES, nr)
                paused = True
                read_next = True

        video_reader.release()
        print_timestamps(stamps, fps, opts.video)
    except Exception:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
