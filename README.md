# TSMARK

Simple video timestamp marking tool. Prints out a command line example
how to trim video with first and last timestamp.

example:  `tsmark video.mp4 --ts 10,00:01:23.4`

- Opens video named `video.mp4`
- Sets predefined timestamps at 10 seconds, and 1 minute 23.4 seconds.

## Keyboard shortcuts:

```
(Note: after mouse click, arrows stop working due to unknown bug: use j,l,i,k)
Arrows, PgUp, PgDn, Home, End or click mouse in position bar
j l i k [ ]
          jump in video position
0-9       move to 0%,10%,20% .. position
, and .   move one frame at a time
z and c   move to previous or next mark
x or double click in the video
          mark frame
space or click video
          pause
f         toggle 0.5x 1x or 2x FPS
v         toggle HUD
h         toggle help
q or esc  quit
```


## Install

`pipx install git+https://github.com/moonq/tsmark.git`
