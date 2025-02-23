from onvif import ONVIFCamera
import requests
from requests.auth import HTTPDigestAuth
from PIL import Image
from io import BytesIO
from onvif import ONVIFCamera
from urllib.parse import urlparse
import os
import logging

WSDL_PATH = os.path.join(os.path.dirname(__file__), 'python-onvif-zeep/wsdl')
# WSDL_PATH = '/etc/onvif/wsdl'

# Configure logging
logger = logging.getLogger(__name__)


class myOnvifClass:

    def __init__(self, wsdl_path=WSDL_PATH):
        """
        Discover ONVIF cameras using WS-Discovery.
        :param wsdl_path: Path to the WSDL files for ONVIF discovery.
        """
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
                logger.debug("Discovered ONVIF Cameras:")
                for camera in self.cameras:
                    logger.debug('- ' + camera)
            else:
                logger.error("No ONVIF cameras found.")

        except Exception as e:
            logger.error("Error discovering cameras:", e)

    def identify_camera(self, ip, port, wsdl_path):
        """
        Identify a camera based on its IP address and port.
        :param ip: IP address of the camera.
        :param port: Port number of the camera.
        :param wsdl_path: Path to the WSDL files for ONVIF discovery.
        :return: Dictionary containing camera information.
        """
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
            logger.error("Error connecting to camera:", e)
            return []

    def get_snapshot(self, name):
        """
        Retrieve a snapshot from a camera.
        :param name: Name of the camera.
        :return: PIL.Image object representing the snapshot.
        """
        camera = self.cameras[name]
        logger.debug("Retrieving snapshot from", name)
        response = requests.get(camera['uri'], auth=HTTPDigestAuth(
            camera['username'], camera['password']), stream=True)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            return image
        else:
            logger.error("Failed to retrieve snapshot. Status code:",
                         response.status_code)
            return None

    def show_snapshot(self, camera_name):
        """
        Display a snapshot from a camera.
        :param camera_name: Name of the camera.
        :return: None
        """
        image = self.get_snapshot(camera_name)
        if image:
            image.show()

    def save_snapshot(self, camera_name, image_name):
        """
        Save a snapshot from a camera to a file.
        :param camera_name: Name of the camera.
        :param image_name: Name of the file to save the snapshot to.
        :return: None
        """
        image = self.get_snapshot(camera_name)
        if image:
            image.save(image_name)
            logger.debug("Snapshot saved as 'snapshot.jpg'")

    def get_camera_list(self):
        """
        Get the list of cameras.
        :return: List of camera names.
        """
        return self.cameras.keys()


if __name__ == "__main__":

    # Set logging level for direct runs
    logging.basicConfig(level=logging.INFO)

    # Discover cameras
    cameras = myOnvifClass()

    for camera in cameras.get_camera_list():
        # cameras.show_snapshot(camera)
        cameras.save_snapshot(camera, camera+".jpg")
