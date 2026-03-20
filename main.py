# main.py
import threading
from body.speak import audio_loop, warm_up
from brain.brain import brain_loop
from memory.firebase_sync import pull_memory
from memory.local_cache import write_cache
from memory.firebase_sync import pull_memory
from memory.local_cache import write_cache, read_cache


def init_memory():
    cloud_data = pull_memory()
    local_data = read_cache()

    if not cloud_data:
        return

    local_time = local_data.get("user_profile", {}).get("updated_at")
    cloud_time = cloud_data.get("user_profile", {}).get("updated_at")

    if not local_time or (cloud_time and cloud_time > local_time):
        print("[SYNC] Using cloud data")
        write_cache(cloud_data)
    else:
        print("[SYNC] Keeping local data")



if __name__ == "__main__":
    init_memory()

    warm_up()

    threading.Thread(target=brain_loop, daemon=True).start()
    audio_loop()

    brain_loop() 