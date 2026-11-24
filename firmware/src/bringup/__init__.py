"""First-article bring-up scripts. Run in order from the REPL, one per import.

Only after the E09 electrical gates allow powered use (current-limited
supply first). Each script prints what it checks and leaves the amplifier
muted and unpowered when it ends, even on error or Ctrl-C.

    import bringup.info        # board, CircuitPython, flash/filesystem space
    import bringup.blink       # GPIO13 status LED
    import bringup.i2c_imu     # 0x6A, WHO_AM_I, CTRL9_XL fix (#13), samples
    import bringup.button      # J2 button edges and recognized gestures
    import bringup.audio_tone  # power/mute/I2S sequencing with a quiet tone
    import bringup.audio_files # synth, WAV and MP3 voices; start timing
    import bringup.loop_rate   # IMU sample rate and loop timing
    import bringup.wake        # IMU wake-on-motion interrupt on GPIO22 (deep sleep wake path)
    import bringup.battery     # battery/USB/charge sensing (boards that have it)
    import bringup.record_trace  # stream HGP raw rows for scripts/capture_trace.py

Re-run a script with ``import supervisor; supervisor.reload()`` or by
pressing Ctrl-D, then importing it again.
"""
