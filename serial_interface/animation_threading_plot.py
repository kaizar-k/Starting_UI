"""
The following example code is for a live plot of a 4-channel
resistance measurement. It demonstrates many (but not all) of the key features
of the SerialManager.


for this program I am using this file as a test file for noting the resitance of the sensor points
"""

import time
import threading

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from .serial_manager import SerialManager

CONFIG_STRING = "NC:8, SP:10"


def main():
    # Device Setup:
    master = SerialManager()
    full_device_list = master.find_usb_devices()

    if not full_device_list:
        raise RuntimeError("No USB serial devices were detected. Connect the device and try again.")

    box = full_device_list[0]
    box.change_config_string(CONFIG_STRING)

    print(box.__str__())

    master.connect_to_device(0)
    box.set_up_channels()

    box.start_device()

    # Thread Conditions:
    # The event lets the plot close handler stop the background serial worker.
    stop_event = threading.Event()

    # Worker thread to receive data.
    def receive_data():
        while not stop_event.is_set():
            output = box.receive_serial()
            if output is not None:
                print("stream:", output)
            time.sleep(0.001)

    # Instantiating and starting the worker thread.
    data_worker = threading.Thread(target=receive_data, daemon=True)
    data_worker.start()

    # Make sure the serial worker and device stop exactly once when the plot is closed.
    # A single close callback is enough; repeated close events should be ignored.
    def safe_shutdown():
        if stop_event.is_set():
            return

        stop_event.set()

        for animation in (anim_all, anim_ch5):
            try:
                animation.event_source.stop()
            except Exception:
                pass

        if box.running:
            try:
                box.stop_device()
            except Exception as exc:
                print(f"Shutdown warning: {exc}")

        if data_worker.is_alive():
            data_worker.join(timeout=1.0)

    channel_count = box.num_channels

    # Figure Set-up: one window for all configured channels, one dedicated to ch5.
    fig_all, ax_all = plt.subplots()
    fig_all.set_size_inches(8, 5)
    ax_all.set_xlim(0, 100000)
    ax_all.set_ylim(0, 120000)
    ax_all.set_title(f"All {channel_count} Channels")
    ax_all.grid(True)

    all_lines = []
    for i in range(1, channel_count + 1):
        line, = ax_all.plot([], [], label=f'CH{i}')
        all_lines.append(line)

    ax_all.legend(loc="upper right")

    fig_ch5, ax_ch5 = plt.subplots()
    fig_ch5.set_size_inches(6, 4)
    ax_ch5.set_xlim(0, 100000)
    ax_ch5.set_ylim(1500, 3500)
    ax_ch5.set_title("Channel 5")
    ax_ch5.grid(True)

    line_ch5, = ax_ch5.plot([], [], label='CH5', color='tab:orange')
    ax_ch5.legend(loc="upper right")

    # Function that updates the full channel plot.
    def update_all(_):
        channels = box.channel_collection
        time_data = list(channels[0].return_raw_data())

        for i in range(1, channel_count + 1):
            channel_data = list(channels[i].return_raw_data())
            all_lines[i - 1].set_data(time_data, channel_data)

        return all_lines

    # Function that updates the dedicated channel 5 plot.
    def update_ch5(_):
        channels = box.channel_collection
        time_data = list(channels[0].return_raw_data())

        if channel_count >= 5:
            ch5_data = list(channels[5].return_raw_data())
            line_ch5.set_data(time_data, ch5_data)

        return [line_ch5]

    # Animation Function:
    anim_all = FuncAnimation(
        fig_all,
        update_all,
        frames=None,
        interval=50,
        blit=False,
        cache_frame_data=False,
        repeat=False
    )

    anim_ch5 = FuncAnimation(
        fig_ch5,
        update_ch5,
        frames=None,
        interval=50,
        blit=False,
        cache_frame_data=False,
        repeat=False
    )

    # Closing Function:
    def closing(_):
        safe_shutdown()

    # This line utilises a built-in method to detect closure of the
    # matplotlib window, and activates the closing function accordingly.
    fig_all.canvas.mpl_connect('close_event', closing)
    fig_ch5.canvas.mpl_connect('close_event', closing)

    try:
        plt.show()
    finally:
        safe_shutdown()


if __name__ == "__main__":
    main()



