import argparse
from myonvif import myOnvifClass
from object_detector import YOLODetector
import time

if __name__ == '__main__':

    # Initialize cameras
    cameras = myOnvifClass()

    # Initialize object detector
    detector = YOLODetector()

    for loop in range(1):
        print(f"Loop {loop}")

        for camera in cameras.get_camera_list():
            snapshot = cameras.get_snapshot(camera)

            detections = detector.detect_objects(snapshot)

            # print detections
            for det in detections:
                print(
                    f"Detected {det['class']} with {det['confidence']:.2f} confidence at {det['bbox']}")
                det['image'].show()

        time.sleep(10)
