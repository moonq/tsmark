# TSMARK

Simple video timestamp marking tool. Prints out a command line example
how to trim video with first and last timestamp.

example:  `tsmark video.mp4 --ts 10,00:01:23.4`

- Opens video named `video.mp4`
- Sets predefined timestamps at 10 seconds, and 1 minute 23.4 seconds.

## Keyboard shortcuts:

```
Arrows left and right, Home, End
          jump in video. Tap frequently to increase time step
, and .   move one frame at a time
z and c   move to previous or next mark
x         mark frame
space     pause
i         toggle HUD
q         quit
```


## Install

`pipx install git+https://github.com/moonq/tsmark.git`
