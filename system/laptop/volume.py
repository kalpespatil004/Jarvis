try:
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
except ImportError:
    AudioUtilities = None
    IAudioEndpointVolume = None


# ---------------------------
# GET AUDIO DEVICE
# ---------------------------

def get_speaker():
    if not AudioUtilities:
        return None
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None
    )
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    return volume


# ---------------------------
# VOLUME UP
# ---------------------------

def volume_up(step=0.05):
    volume = get_speaker()
    if not volume:
        return "❌ pycaw not installed"
    current = volume.GetMasterVolumeLevelScalar()
    new = min(1.0, current + step)
    volume.SetMasterVolumeLevelScalar(new, None)
    return f"🔊 Volume increased to {int(new*100)}%"


# ---------------------------
# VOLUME DOWN
# ---------------------------

def volume_down(step=0.05):
    volume = get_speaker()
    if not volume:
        return "❌ pycaw not installed"
    current = volume.GetMasterVolumeLevelScalar()
    new = max(0.0, current - step)
    volume.SetMasterVolumeLevelScalar(new, None)
    return f"🔉 Volume decreased to {int(new*100)}%"


# ---------------------------
# SET VOLUME
# ---------------------------

def set_volume(value):
    """
    Set volume to specific level (0-100)
    """
    volume = get_speaker()
    if not volume:
        return "❌ pycaw not installed"
    value = max(0, min(100, int(value)))
    volume.SetMasterVolumeLevelScalar(value/100, None)
    return f"🔊 Volume set to {value}%"


# ---------------------------
# GET CURRENT VOLUME
# ---------------------------

def get_volume():
    """
    Return current volume percentage
    """
    volume = get_speaker()
    if not volume:
        return "❌ pycaw not installed"
    current = int(volume.GetMasterVolumeLevelScalar()*100)
    return f"🔊 Current volume is {current}%"
