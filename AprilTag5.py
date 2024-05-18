import numpy as np
import robotpy_apriltag
import cv2

class AprilTag:
    def __init__(self, tagFamily, tagSize, cameraIntrinsics):
        self.detector = robotpy_apriltag.AprilTagDetector()
        self.detector.addFamily(tagFamily)  

        self.haveIntrinsics = cameraIntrinsics is not None
        self.estimator = None

        # Set up Pose Estimator - parameters come from the cameraIntrinsics object

        if (self.haveIntrinsics):
            poseEstConfig = robotpy_apriltag.AprilTagPoseEstimator.Config(
                tagSize,
                cameraIntrinsics[0][0],       # fx
                cameraIntrinsics[1][1],       # fy
                cameraIntrinsics[0][2],       # cx
                cameraIntrinsics[1][2]        # cy
            )
            self.estimator = robotpy_apriltag.AprilTagPoseEstimator(poseEstConfig) 


    def detect(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        detections = self.detector.detect(gray)

        for detection in detections:
            corners = (0, 0, 0, 0, 0, 0, 0, 0)
            corners = detection.getCorners(corners)
            # cv2.rectangle(image, (int(corners[0]), int(corners[1])), (int(corners[4]), int(corners[5])), color=(0, 255, 0), thickness=3)

            pts = np.array([[int(corners[0]), int(corners[1])], [int(corners[2]), int(corners[3])], [int(corners[4]), int(corners[5])], [int(corners[6]), int(corners[7])]], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(image, [pts], True, (0, 255, 0), 1)
            cv2.putText(image, str(detection.getId()), (int(corners[0]), int(corners[1])), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 255, 0), 2)
            center = detection.getCenter()            
            cv2.circle(image, (int(center.x), int(center.y)), 5, (0, 255, 0), -1)

            if (self.haveIntrinsics):
                pose = self.estimator.estimate(detection)
                rot = pose.rotation()

                print(f"X: {pose.X()}, Y: {pose.Y()}, Z: {pose.Z()}, XR: {rot.X()}, YR: {rot.Y()}, ZR: {rot.Z()}")
        return detections