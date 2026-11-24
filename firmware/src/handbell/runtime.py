"""The device main loop: read, decide, tick. No blocking work on the hot path.

Audio plays from DMA in the background. The loop reads the IMU (skipping
samples the sensor has not refreshed), feeds button edges, ticks the
instrument and runs garbage collection only when nothing is in progress.
"""

import gc

from handbell.core import events

RAW_BATCH_US = 250000
GC_INTERVAL_US = 1000000


def run(ports, inst, cfg, app="digital-handbell", device_id="hb-unknown", max_loops=None, wake=None, power_on=False):
    """Run the instrument. Returns only in tests or after a simulated sleep;
    on a device a deep sleep exits the program and the board restarts on wake."""
    clock = ports.clock
    motion = ports.motion
    button = ports.button
    link = ports.link
    audio = ports.audio
    sleeper = getattr(ports, "sleeper", None)
    debug = cfg.debug
    raw = bool(debug.get("raw"))
    status_us = int(debug.get("status_s", 0) * 1000000)

    now = clock.now_us()
    link.send(
        events.hello(device_id, cfg.name, app, ports.info.get("sensors", {}), ("ring", "damp"), True)
    )
    inst.start(now, wake=wake, power_on=power_on)
    window_start = now
    next_status = now + status_us
    next_raw = now + RAW_BATCH_US
    last_gc = now
    prev = now
    max_gap = 0
    samples = 0
    loops = 0
    raw_rows = []
    while max_loops is None or loops < max_loops:
        now = clock.now_us()
        gap = now - prev
        prev = now
        if gap > max_gap:
            max_gap = gap
        sample = motion.read()
        if sample is not None:
            samples += 1
            inst.on_motion(now, sample)
            if raw:
                raw_rows.append((now,) + tuple(sample))
        for pressed in button.poll():
            inst.on_button(pressed, now)
        inst.tick(now)
        loops += 1

        if raw and now >= next_raw:
            link.send(events.raw_batch(raw_rows))
            raw_rows = []
            next_raw = now + RAW_BATCH_US
        if status_us and now >= next_status:
            elapsed = max(1, now - window_start)
            st = inst.status(now)
            st["rateHz"] = round(samples * 1000000.0 / elapsed, 1)
            st["loopHz"] = round(loops * 1000000.0 / elapsed, 1) if max_loops is None else loops
            st["maxGapMs"] = round(max_gap / 1000.0, 1)
            if hasattr(gc, "mem_free"):
                st["memFree"] = gc.mem_free()
            if hasattr(audio, "state_name"):
                st["audio"] = audio.state_name
            link.send(events.status(st))
            window_start = now
            next_status = now + status_us
            samples = 0
            max_gap = 0
            if max_loops is None:
                loops = 0
        if now - last_gc > GC_INTERVAL_US and inst.quiet(now):
            gc.collect()
            last_gc = now
        if sleeper is not None and inst.sleep_due(now):
            inst.prepare_sleep(now)
            ports.sleep(cfg.sleep)
            return loops
    return loops
