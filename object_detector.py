from ultralytics import YOLO
import cv2
import os


class YOLODetector:
    def __init__(self, model_path='yolov8n.pt'):
        """
        Initialize the YOLO detector with a given model.
        :param model_path: Path to the YOLO model file.
        """
        self.model = YOLO(model_path)

    def detect_stored_image(self, image_path, save_rois=False):
        if not os.path.exists(image_path):
            raise FileNotFoundError(
                f"Image file '{image_path}' does not exist.")

        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(
                f"Image file '{image_path}' is not a valid image or has an unsupported format.")

        return self.detect_objects(image, save_rois=save_rois)

    def detect_objects(self, image, save_rois=False):
        """
        Perform object detection on an input image.
        :param image_path: Path to the input image.
        :return: List of detected objects with class names and confidence scores.
        """
        results = self.model(image)

        detections = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # Bounding box coordinates
                class_name = self.model.names[class_id]

                # Extract ROI from the image
                x1, y1, x2, y2 = map(int, bbox)
                roi = image[y1:y2, x1:x2]

                # discard low confidence detections
                if confidence < 0.25:
                    print("Discarding low confidence detection:",
                          class_name, " with confidence:", confidence)
                    continue

                # discard small detection
                minimum = 30
                bbox_width = x2 - x1
                bbox_height = y2 - y1
                if bbox_height < minimum and bbox_width < minimum:
                    print("Discarding small detection, height:",
                          bbox_height, "width:", bbox_width)
                    continue

                # Optionally save ROI as an image file
                if save_rois:
                    roi_filename = f"roi_{class_name}_{x1}_{y1}.jpg"
                    cv2.imwrite(roi_filename, roi)
                    print("Saved ROI as", roi_filename)

                detections.append({
                    'class': class_name,
                    'confidence': confidence,
                    'bbox': bbox,
                    'image': roi
                })
        return detections


# Example usage:
if __name__ == '__main__':
    detector = YOLODetector()
    image_path = 'terrassa.jpg'
    # image_path = 'tortugues.jpg'
    detections = detector.detect_stored_image(image_path, save_rois=False)
    for det in detections:
        print(
            f"Detected {det['class']} with {det['confidence']:.2f} confidence at {det['bbox']}")
