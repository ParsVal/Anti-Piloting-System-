"""
Device Fingerprinting - MachineGuid Extraction
"""
import platform
import subprocess
import uuid

def get_machine_guid():
    """
    Get unique machine identifier
    
    Returns:
        str: Machine GUID
    """
    system = platform.system()
    
    if system == 'Windows':
        return get_windows_machine_guid()
    elif system == 'Linux':
        return get_linux_machine_id()
    elif system == 'Darwin':  # macOS
        return get_mac_hardware_uuid()
    else:
        # Fallback to UUID based on MAC address
        return str(uuid.getnode())

def get_windows_machine_guid():
    """
    Get Windows MachineGuid from registry
    
    Returns:
        str: MachineGuid
    """
    try:
        import winreg
        
        # Open registry key
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r'SOFTWARE\Microsoft\Cryptography',
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY
        )
        
        # Read MachineGuid value
        machine_guid, _ = winreg.QueryValueEx(key, 'MachineGuid')
        winreg.CloseKey(key)
        
        return machine_guid
    
    except Exception as e:
        print(f"Error getting Windows MachineGuid: {e}")
        return str(uuid.getnode())

def get_linux_machine_id():
    """
    Get Linux machine-id
    
    Returns:
        str: Machine ID
    """
    try:
        # Try reading /etc/machine-id
        with open('/etc/machine-id', 'r') as f:
            machine_id = f.read().strip()
            return machine_id
    except FileNotFoundError:
        try:
            # Fallback to /var/lib/dbus/machine-id
            with open('/var/lib/dbus/machine-id', 'r') as f:
                machine_id = f.read().strip()
                return machine_id
        except Exception as e:
            print(f"Error getting Linux machine-id: {e}")
            return str(uuid.getnode())

def get_mac_hardware_uuid():
    """
    Get macOS hardware UUID
    
    Returns:
        str: Hardware UUID
    """
    try:
        result = subprocess.run(
            ['system_profiler', 'SPHardwareDataType'],
            capture_output=True,
            text=True
        )
        
        for line in result.stdout.split('\n'):
            if 'Hardware UUID' in line:
                return line.split(':')[1].strip()
        
        return str(uuid.getnode())
    
    except Exception as e:
        print(f"Error getting macOS UUID: {e}")
        return str(uuid.getnode())

def get_device_info():
    """
    Get comprehensive device information
    
    Returns:
        dict: Device information
    """
    return {
        'machine_guid': get_machine_guid(),
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'hostname': platform.node()
    }

def verify_device(current_guid, registered_guid):
    """
    Verify if current device matches registered device
    
    Args:
        current_guid: Current machine GUID
        registered_guid: Registered machine GUID
        
    Returns:
        bool: True if match, False otherwise
    """
    return current_guid == registered_guid

if __name__ == '__main__':
    # Test device fingerprinting
    print("Device Fingerprinting Test")
    print("=" * 50)
    
    info = get_device_info()
    
    for key, value in info.items():
        print(f"{key}: {value}")
    
    print("\nMachine GUID:", get_machine_guid())
