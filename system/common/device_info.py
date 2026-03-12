import platform
import socket
import uuid
import psutil
import os

def get_basic_info():
    """
    Returns basic OS and system details
    """
    return {
        "OS": platform.system(),
        "OS Version": platform.version(),
        "OS Release": platform.release(),
        "Architecture": platform.machine(),
        "Processor": platform.processor()
    }


def get_cpu_info():
    """
    Returns CPU-related information
    """
    return {
        "Physical Cores": psutil.cpu_count(logical=False),
        "Total Cores": psutil.cpu_count(logical=True),
        "CPU Usage (%)": psutil.cpu_percent(interval=1)
    }


def get_memory_info():
    """
    Returns RAM information
    """
    mem = psutil.virtual_memory()
    return {
        "Total RAM (GB)": round(mem.total / (1024 ** 3), 2),
        "Available RAM (GB)": round(mem.available / (1024 ** 3), 2),
        "Used RAM (GB)": round(mem.used / (1024 ** 3), 2),
        "RAM Usage (%)": mem.percent
    }


def get_disk_info():
    """
    Returns disk usage information
    """
    disks = {}
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks[part.device] = {
                "Total (GB)": round(usage.total / (1024 ** 3), 2),
                "Used (GB)": round(usage.used / (1024 ** 3), 2),
                "Free (GB)": round(usage.free / (1024 ** 3), 2),
                "Usage (%)": usage.percent
            }
        except PermissionError:
            pass
    return disks


def get_network_info():
    """
    Returns network-related information
    """
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    return {
        "Hostname": hostname,
        "IP Address": ip_address,
        "MAC Address": ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff)
                                 for i in range(0, 48, 8)])
    }


def get_battery_info():
    """
    Returns battery details (Laptop only)
    """
    battery = psutil.sensors_battery()
    if not battery:
        return "No battery detected"

    return {
        "Battery Percent": battery.percent,
        "Power Plugged": battery.power_plugged
    }


def get_full_device_info():
    """
    Returns ALL system information in one dictionary
    """
    return {
        "Basic Info": get_basic_info(),
        "CPU Info": get_cpu_info(),
        "Memory Info": get_memory_info(),
        "Disk Info": get_disk_info(),
        "Network Info": get_network_info(),
        "Battery Info": get_battery_info(),
        "Current User": os.getlogin()
    }
