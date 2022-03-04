import sys
import os
import cv2
import time


class Marker:
    def __init__(self, opts):
        self.opts = opts
        if not os.path.exists(self.opts.video):
            raise FileNotFoundError("Video file missing!")

        self.paused = False
        self.read_next = False
        self.show_info = True
        self.show_help = False
        self.auto_step = True
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.frame_visu = []
        self.max_res = (1280, 720)
        self.min_res = (512, None)

        try:
            self.open()
            self.calculate_res()
            self.parse_timestamps()
            self.loop()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            raise e

    def open(self):

        self.video_reader = cv2.VideoCapture(self.opts.video)
        self.frames = int(self.video_reader.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.video_reader.get(cv2.CAP_PROP_FPS)
        self.spf = 1 / self.fps
        self.video_length = self.frames * self.fps

    def calculate_res(self):

        self.video_res = [
            int(self.video_reader.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.video_reader.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        ]
        video_aspect = self.video_res[0] / self.video_res[1]
        if self.video_res[0] > self.max_res[0]:
            self.video_res[0] = int(self.max_res[0])
            self.video_res[1] = int(self.video_res[0] / video_aspect)

        if self.video_res[1] > self.max_res[1]:
            self.video_res[1] = int(self.max_res[1])
            self.video_res[0] = int(self.video_res[1] * video_aspect)

        if self.video_res[0] < self.min_res[0]:
            self.video_res[0] = int(self.min_res[0])
            self.video_res[1] = int(self.video_res[0] / video_aspect)

        self.video_res = tuple(self.video_res)
        self.bar_start = int(self.video_res[0] * 0.05)
        self.bar_end = int(self.video_res[0] * 0.95)
        self.bar_top = int(self.video_res[1] * 0.90)
        self.bar_bottom = int(self.video_res[1] * 0.95)

    def calculate_step(self):

        now = time.time()
        self.last_move = [x for x in self.last_move if x[1] > now - 3]
        if len(self.last_move) == 0:
            self.step = 1
            self.last_move = []
            return
        lefts = sum([1 for x in self.last_move if x[0] == "l"])
        rights = sum([1 for x in self.last_move if x[0] == "r"])
        if lefts > 0 and rights > 0:
            self.step = 1
            self.last_move = []
            return
        count = max(lefts, rights)
        if count < 5:
            self.step = 1
        else:
            # x2 poly  from 5:5 -> 15:180
            self.step = 45 - 16.5 * count + 1.7 * count * count
            self.step = min(self.step, 0.1 * self.video_length)
        self.step = int(self.step)

    def draw_bar(self, frame):

        position = self.nr / self.frames
        bar_position = int(self.bar_start + position * (self.bar_end - self.bar_start))

        cv2.rectangle(
            frame,
            (self.bar_start, self.bar_top),
            (self.bar_end, self.bar_bottom),
            (255, 255, 255),
            2,
        )

        for ts in self.stamps:
            ts_pos = int(
                self.bar_start + ts / self.frames * (self.bar_end - self.bar_start)
            )
            cv2.line(
                frame,
                (ts_pos, self.bar_top),
                (ts_pos, self.bar_bottom),
                (32, 32, 32),
                3,
            )
            cv2.line(
                frame,
                (ts_pos, self.bar_top),
                (ts_pos, self.bar_bottom),
                (84, 255, 63),
                1,
            )
        # cv2.line(frame, (bar_position, top), (bar_position, bottom), (32,32,32), 3)
        cv2.line(
            frame,
            (bar_position, self.bar_top),
            (bar_position, self.bar_bottom),
            (63, 84, 255),
            1,
        )

        self.shadow_text(
            frame,
            "1",
            (self.bar_start - 7, self.bar_bottom + 20),
            0.7,
            2,
            (255, 255, 255),
        )
        end_frame = self.format_time(self.frames - 1)
        (text_width, text_height) = cv2.getTextSize(
            end_frame, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
        )[0]
        self.shadow_text(
            frame,
            end_frame,
            (self.bar_end - text_width, self.bar_bottom + 20),
            0.7,
            2,
            (255, 255, 255),
        )

    def draw_help(self, frame):

        bottom = 80
        left = 100
        for row in self.get_help().split("\n"):
            self.shadow_text(frame, row, (left, bottom), 0.6, 1, (255, 255, 255))
            bottom += 18

    def draw_label(self, frame):

        if not self.nr in self.stamps:
            return

        text = "{} #{}".format(self.nr + 1, self.stamps.index(self.nr) + 1)
        bottom = 60
        left = 10
        self.shadow_text(frame, text, (left, bottom), 1, 2, (63, 84, 255))

    def draw_time(self, frame):
        left = 10
        bottom = 30

        formatted = "{} {}".format(
            self.format_time(self.nr),
            "||" if self.paused else "",
        )
        self.shadow_text(frame, formatted, (left, bottom), 1.1, 2, (255, 255, 255))

    def format_time(self, nframe):

        seconds = int(nframe / self.fps)
        frame = nframe % self.fps
        parts = int(100 * (frame / self.fps))
        return time.strftime("%H:%M:%S", time.gmtime(seconds)) + ".%02d" % (parts)

    def get_help(self):
        return """Keyboard help:
    (Note: after mouse click, arrows stop working due to unknown bug: use j,l,i,k)
    Arrows, PgUp, PgDn, Home, End or click mouse in position bar
    j,l,i,k,[,]
              jump in video position
    , and .   move one frame at a time
    z and c   move to previous or next mark
    x or double click in the video
              mark frame
    space or click video
              pause
    v         toggle HUD
    q or esc  quit
    """

    def mouse_click(self, event, x, y, flags, param):

        in_bar = all(
            (
                x < self.bar_end,
                x > self.bar_start,
                y < self.bar_bottom,
                y > self.bar_top,
            )
        )
        if event == cv2.EVENT_LBUTTONDOWN:
            if in_bar:
                click_relative = (x - self.bar_start) / (self.bar_end - self.bar_start)
                self.nr = int(click_relative * self.frames)
                self.read_next = True
            else:
                self.paused = not self.paused

        if event == cv2.EVENT_LBUTTONDBLCLK:
            if not in_bar:
                self.toggle_stamp()
            # doubleclick (toggle?)
            # ~ print("double", x, y)

    def parse_time(self, timestr):
        """return frames"""

        colon_count = len(timestr.split(":")) - 1
        if colon_count == 0:
            secs = float(timestr)
            return int(secs * self.fps)
        if colon_count == 1:
            mins, secstr = timestr.split(":", 1)
            sec = float(secstr)
            return int(self.fps * (int(mins) * 60 + sec))
        if colon_count == 2:
            hours, mins, secstr = timestr.split(":", 2)
            sec = float(secstr)
            return int(self.fps * (int(hours) * 3600 + int(mins) * 60 + sec))
        raise ValueError("Cannot parse time definition {}".format(timestr))

    def parse_timestamps(self):
        if self.opts.timestamps:
            self.stamps = sorted(
                [
                    self.parse_time(ts.strip())
                    for ts in self.opts.timestamps.split(",")
                    if ts.strip() != ""
                ]
            )
            self.stamps = [x for x in self.stamps if 0 <= x < self.frames]
            self.nr = self.stamps[0]
        else:
            self.stamps = []
            self.nr = 0

    def print_help(self):
        print(self.get_help())

    def print_timestamps(self):
        self.stamps.sort()
        print("# Timestamps:")
        for i, ts in enumerate(self.stamps):
            print("# {}: {} / {}".format(i + 1, self.format_time(ts), ts + 1))
        if len(self.stamps) > 0:
            print(
                'ffmpeg -i "{}" -ss {} -to {} -c copy "{}.trimmed.mp4"'.format(
                    self.opts.video.replace('"','\\"'),
                    self.format_time(self.stamps[0]),
                    self.format_time(self.stamps[-1]),
                    self.opts.video.replace('"','\\"'),
                )
            )

    def save_timestamps(self):

        if self.opts.output == None:
            return
        with open(self.opts.output, "wt") as fp:
            for i, ts in enumerate(self.stamps):
                fp.write("{},{},{}\n".format(self.format_time(ts), i + 1, ts + 1))

    def shadow_text(self, frame, text, pos, size, thicc, color):

        cv2.putText(
            frame,
            text,
            pos,
            self.font,
            size,
            (0, 0, 0),
            2 * thicc,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            text,
            pos,
            self.font,
            size,
            color,
            thicc,
            cv2.LINE_AA,
        )

    def toggle_stamp(self):
        if self.nr in self.stamps:
            self.stamps.remove(self.nr)
        else:
            self.stamps.append(self.nr)
        self.stamps.sort()

    def loop(self):

        self.step = 1
        self.bigstep = 30
        self.hugestep = 300
        self.auto_step = False
        self.last_move = []
        self.video_reader.set(cv2.CAP_PROP_POS_FRAMES, self.nr)

        self.print_help()
        cv2.namedWindow("tsmark")
        cv2.setMouseCallback("tsmark", self.mouse_click)
        while self.video_reader.isOpened():
            show_time = time.time()
            if (not self.paused) or self.read_next:
                ret, frame = self.video_reader.read()
            if ret == True:
                if self.paused:
                    draw_wait = 200
                else:
                    draw_wait = 1
                if (not self.paused) or self.read_next:
                    self.read_next = False
                frame_visu = cv2.resize(frame.copy(), self.video_res)
                nr_time = self.nr / self.fps
                if self.show_info:
                    self.draw_time(frame_visu)
                    self.draw_bar(frame_visu)
                    self.draw_label(frame_visu)
                if self.show_help:
                    self.draw_help(frame_visu)

                if cv2.getWindowProperty("tsmark", cv2.WND_PROP_VISIBLE) < 1:
                    break
                cv2.imshow("tsmark", frame_visu)
                k = cv2.waitKey(draw_wait)
                if k & 0xFF == ord("q") or k & 0xFF == 27:
                    break
                if k & 0xFF == 32:  # space
                    self.paused = not self.paused

                # Movement =================
                if k & 0xFF == 80:  # home key
                    self.nr = -1
                    self.read_next = True

                if k & 0xFF == 87:  # end key
                    self.nr = self.frames - 1
                    self.paused = True
                    self.read_next = True

                if k & 0xFF == 85 or k & 0xFF == ord("]"):  # pg up
                    self.nr = int((nr_time + self.hugestep) * self.fps) - 1
                    self.read_next = True
                if k & 0xFF == 86 or k & 0xFF == ord("["):  # pg down
                    self.nr = int((nr_time - self.hugestep) * self.fps) - 1
                    self.read_next = True


                if k & 0xFF == 82 or k & 0xFF == ord("i"):  # up arrow
                    self.nr = int((nr_time + self.bigstep) * self.fps) - 1
                    self.read_next = True
                if k & 0xFF == 84 or k & 0xFF == ord("k"):  # down arrow
                    self.nr = int((nr_time - self.bigstep) * self.fps) - 1
                    self.read_next = True


                if k & 0xFF == 83 or k & 0xFF == ord("l"):  # right arrow
                    self.last_move.append(("r", time.time()))
                    if self.auto_step:
                        self.calculate_step()
                    self.nr = int((nr_time + self.step) * self.fps) - 1
                    self.read_next = True

                if k & 0xFF == 81 or k & 0xFF == ord("j"):  # left arrow
                    self.last_move.append(("l", time.time()))
                    if self.auto_step:
                        self.calculate_step()
                    self.nr = int((nr_time - self.step) * self.fps) - 1
                    self.read_next = True


                # Move by frame
                if k & 0xFF == ord("."):
                    self.paused = True
                    self.read_next = True
                if k & 0xFF == ord(","):
                    self.paused = True
                    self.nr -= 2
                    self.read_next = True

                if k & 0xFF == ord("z"):  # move to previous ts
                    for ts in reversed(sorted(self.stamps)):
                        if ts < self.nr - 1:
                            self.nr = ts - 1
                            self.read_next = True
                            break
                if k & 0xFF == ord("c"):  # move to previous ts
                    for ts in sorted(self.stamps):
                        if ts > self.nr:
                            self.nr = ts - 1
                            self.read_next = True
                            break

                # Toggling =================

                if k & 0xFF == ord("x"):  # toggle ts
                    self.toggle_stamp()

                if k & 0xFF == ord("v"):
                    self.show_info = not self.show_info
                if k & 0xFF == ord("h"):
                    self.print_help()
                    self.show_help = not self.show_help


                if (not self.paused) or self.read_next:
                    self.nr += 1
                if self.nr < 0:
                    self.nr = 0
                if self.nr >= self.frames:
                    self.nr = self.frames - 1
                    self.paused = True
                if self.read_next:
                    self.video_reader.set(cv2.CAP_PROP_POS_FRAMES, self.nr)

                time_to_wait = self.spf - time.time() + show_time
                if time_to_wait > 0:
                    time.sleep(time_to_wait)

            else:
                self.nr = self.frames - 2
                self.video_reader.set(cv2.CAP_PROP_POS_FRAMES, self.nr)
                self.paused = True
                self.read_next = True

        self.video_reader.release()
        self.print_timestamps()
        self.save_timestamps()
