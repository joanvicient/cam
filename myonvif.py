from onvif import ONVIFCamera
import requests
from requests.auth import HTTPDigestAuth
from PIL import Image
from io import BytesIO
from onvif import ONVIFCamera
from urllib.parse import urlparse
import os

WSDL_PATH = os.path.join(os.path.dirname(__file__), 'python-onvif-zeep/wsdl')

def discover_onvif_cameras():
    try:
        from wsdiscovery import WSDiscovery
        wsd = WSDiscovery()
        wsd.start()
        services = wsd.searchServices()
        wsd.stop()
        
        cameras = []
        for service in services:
            url = service.getXAddrs()[0]
            if 'onvif' in url:
                parsed_url = urlparse(url)
                cam = {}
                cam['ip'] = parsed_url.hostname
                cam['port'] = parsed_url.port if parsed_url.port else 80
                cameras.append(cam)

        if cameras:
            print("Discovered ONVIF Cameras:")
            for cam in cameras:
                print('- ' + str(cam))
        else:
            print("No ONVIF cameras found.")
        return cameras
    except Exception as e:
        print("Error discovering cameras:", e)
        return []

def identify_camera(cam_dict, wsdl_path='/etc/onvif/wsdl'):                
    cam_dict['username'] = 'admin'
    cam_dict['password'] = 'Joan35Joan'
    try:
        onvif_camera = ONVIFCamera(cam_dict['ip'], cam_dict['port'], cam_dict['username'], cam_dict['password'], wsdl_path)
        media_service = onvif_camera.create_media_service()

        # Create a device management service
        device_mgmt = onvif_camera.create_devicemgmt_service()

        # Get basic device information
        device_info = device_mgmt.GetDeviceInformation()
        cam_dict['manufacturer'] = device_info.Manufacturer
        cam_dict['model'] = device_info.Model
        cam_dict['firmware_version'] = device_info.FirmwareVersion
        cam_dict['serial_number'] = device_info.SerialNumber
        cam_dict['hardware_id'] = device_info.HardwareId
        if device_info.Manufacturer == 'AQE':
            cam_dict['name'] = "tortuges"
        elif device_info.Manufacturer == 'LC':
            cam_dict['name'] = "terrassa"
        else:
            cam_dict['name'] = "unknown"
        
        # Get profiles
        profiles = media_service.GetProfiles()
        profile_token = profiles[0].token  # Use the first profile
        
        # Get the snapshot URI
        request = media_service.create_type('GetSnapshotUri')
        request.ProfileToken = profile_token
        cam_dict['uri'] = media_service.GetSnapshotUri(request).Uri

    except Exception as e:
        print("Error connecting to camera:", e)
        return None

    return cam_dict

def get_snapshot(cam):
    print("Retrieving snapshot from", cam['name'])
    response = requests.get(cam['uri'], auth=HTTPDigestAuth(cam['username'], cam['password']), stream=True)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        image.show()  # Display image
        #image.save("snapshot.jpg")  # Save image
        #print("Snapshot saved as 'snapshot.jpg'")
    else:
        print("Failed to retrieve snapshot. Status code:", response.status_code)

if __name__ == "__main__":
    # Discover cameras
    cameras = discover_onvif_cameras()

    for camera in cameras:
        print("Connecting to", camera["ip"])

        camera = identify_camera(camera, wsdl_path=WSDL_PATH)
        if camera:
            get_snapshot(camera)
