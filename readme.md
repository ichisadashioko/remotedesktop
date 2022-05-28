# remotedesktop

## Problems with existing remote desktop solutions

- TeamViewer, AnyDesk will sometimes not release my keyboard and mouse.

For example, sometimes I press Win+Tab and use the mouse to leave or enter the remote desktop window, my Windows key or some other key is stuck in pressed state. I can't release it even if I press it again. Reboot was the only solution I could find to get back my keyboard and mouse.

- I would love to have some features of VMWare about grabbing and releasing the keyboard and mouse.

If the remote desktop window is focused and if my mouse moves outside the remote desktop window, I would like to have my keyboard released.

And I would love to have the option to enter view only mode which my mouse would not interact with the remote computer because it is running some automation software which controls the mouse and keyboard. I only want to monitor them.

- I have multiple computers but I only have 2 monitors which I connected to my main machine. There are other ports on the monitors which I connected the other computers to get the GPU working "properly". I have physical mouse and keyboard connected to them but I don't want to switch video input in my monitors which will cause the main machine windows to messed up when it was going through the disconnect and reconnect of the monitors (in multiple monitors setup).

- RDP is very convenient but it locked the computer and probably messed up the GPU display and windows placement of the remote computer and audio. I just want the video stream of the remote computer screen to be displayed on my main machine.

## Implementation notes

- Socket server-client model seems to have great bandwidth potential and flexible. All of my computers are connected to gigabit switch. We can spawn multiple TCP or UDP connections for multiple types of data (multiple video streams, control commands, etc.)
- However, I haven't able to find any obvious way to implement any video stream protocols. From MP4 video compression, I know that it has increamental update to the key frame instead of the whole image which increase performance. Some projects use `ffmpeg-cli` to start a video stream.

### TCP socket server - C# Winforms client

- I implemented a naive frame-by-frame socket protocol which is not very efficient.
- When I used `gzip` to compress the raw image data, I managed to ultilize 100% CPU usage of my `i9-10900` with terrible performance. I think it is probably because the manually setting each pixel color is very slow and CPU intensive.
- I switch to `PNG` and `JPG` image format and use `Image.FromStream` to convert them to displayable image which has more reasonable CPU usage. However, the rendering of `OnPaint` method causes flickering.

### Web server image stream

- I remember about some projects stream Raspberry Pi camera over HTTP. I lookup some implementation. It seems that it is only a simple HTTP request with response contains multiple JPG images data (full scale frame) back to back.
- However, Chrome browser renders the seemingly navie with more overhead than I expected with excellent performance.
- I swap JPG with PNG and it works perfectly fine.
- If I found a way to efficiently render the UI with native application, I would like to implement it as the web has many limitations.
- I will stick with this web server implementation for now.
