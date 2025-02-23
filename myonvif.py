from onvif import ONVIFCamera
import requests
from requests.auth import HTTPDigestAuth
from PIL import Image
from io import BytesIO
from onvif import ONVIFCamera
from urllib.parse import urlparse
import os

WSDL_PATH = os.path.join(os.path.dirname(__file__), 'python-onvif-zeep/wsdl')
# WSDL_PATH = '/etc/onvif/wsdl'


class myOnvifClass:

    def __init__(self, wsdl_path=WSDL_PATH):
        try:
            from wsdiscovery import WSDiscovery
            wsd = WSDiscovery()
            wsd.start()
            services = wsd.searchServices()
            wsd.stop()

            self.cameras = {}
            for service in services:
                url = service.getXAddrs()[0]
                if 'onvif' in url:
                    parsed_url = urlparse(url)
                    ip = parsed_url.hostname
                    port = parsed_url.port if parsed_url.port else 80
                    camera = self.identify_camera(ip, port, wsdl_path)
                    if camera:
                        self.cameras[camera['name']] = camera

            if self.cameras:
                print("Discovered ONVIF Cameras:")
                for camera in self.cameras:
                    print('- ' + camera)
            else:
                print("No ONVIF cameras found.")

        except Exception as e:
            print("Error discovering cameras:", e)

    def identify_camera(self, ip, port, wsdl_path):
        camera = {}
        camera['ip'] = ip
        camera['port'] = port
        camera['username'] = 'admin'
        camera['password'] = 'Joan35Joan'
        try:
            onvif_camera = ONVIFCamera(
                camera['ip'], camera['port'], camera['username'], camera['password'], wsdl_path)
            media_service = onvif_camera.create_media_service()

            # Create a device management service
            device_mgmt = onvif_camera.create_devicemgmt_service()

            # Get basic device information
            device_info = device_mgmt.GetDeviceInformation()
            camera['manufacturer'] = device_info.Manufacturer
            camera['model'] = device_info.Model
            camera['firmware_version'] = device_info.FirmwareVersion
            camera['serial_number'] = device_info.SerialNumber
            camera['hardware_id'] = device_info.HardwareId
            if device_info.Manufacturer == 'AQE':
                camera['name'] = "tortugues"
            elif device_info.Manufacturer == 'LC':
                camera['name'] = "terrassa"
            else:
                camera['name'] = "unknown"

            # Get profiles
            profiles = media_service.GetProfiles()
            profile_token = profiles[0].token  # Use the first profile

            # Get the snapshot URI
            request = media_service.create_type('GetSnapshotUri')
            request.ProfileToken = profile_token
            camera['uri'] = media_service.GetSnapshotUri(request).Uri

            # Save changes
            return camera

        except Exception as e:
            print("Error connecting to camera:", e)
            return []

    def get_snapshot(self, name):
        camera = self.cameras[name]
        print("Retrieving snapshot from", name)
        response = requests.get(camera['uri'], auth=HTTPDigestAuth(
            camera['username'], camera['password']), stream=True)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            return image
        else:
            print("Failed to retrieve snapshot. Status code:",
                  response.status_code)
            return None

    def show_snapshot(self, camera_name):
        image = self.get_snapshot(camera_name)
        if image:
            image.show()

    def save_snapshot(self, camera_name, image_name):
        image = self.get_snapshot(camera_name)
        if image:
            image.save(image_name)
            print("Snapshot saved as 'snapshot.jpg'")

    def get_camera_list(self):
        return self.cameras.keys()


if __name__ == "__main__":
    # Discover cameras
    cameras = myOnvifClass()

    for camera in cameras.get_camera_list():
        # cameras.show_snapshot(camera)
        cameras.save_snapshot(camera, camera+".jpg")
