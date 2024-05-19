import numpy as np
import robotpy_apriltag
import cv2
import wpimath.geometry as geo

METERS_TO_INCHES = 39.3701

class AprilTag:
    def __init__(self, tagFamily, tagSize, cameraIntrinsics=None, field=None):
        self.detector = robotpy_apriltag.AprilTagDetector()
        self.detector.addFamily(tagFamily)  
        self.tagFamily = tagFamily

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

        if field is not None:
            robotpy_apriltag.AprilTagFieldLayout.loadField(field) 


    def detect(self, image, depthFrame):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        detections = self.detector.detect(gray)

        for detection in detections:
            corners = (0, 0, 0, 0, 0, 0, 0, 0)
            corners = detection.getCorners(corners)
            # cv2.rectangle(image, (int(corners[0]), int(corners[1])), (int(corners[4]), int(corners[5])), color=(0, 255, 0), thickness=3)

            pts = np.array([[int(corners[0]), int(corners[1])], [int(corners[2]), int(corners[3])], [int(corners[4]), int(corners[5])], [int(corners[6]), int(corners[7])]], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(image, [pts], True, (0, 255, 0), 1)
            cv2.putText(image, str(detection.getId()), (int(corners[0]), int(corners[1])), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 255, 0))
            center = detection.getCenter()            
            cv2.circle(image, (int(center.x), int(center.y)), 5, (0, 255, 0), -1)

            wd = abs(corners[6]-corners[0])
            ht = abs(corners[3]-corners[1])

            lblX = int(center.x - wd/2)
            lblY = int(center.y - ht/2)
            # draw the tag family on the image
            # tagID= '{}: {}'.format(r.tag_family.decode("utf-8"), r.tag_id)
            tagID = self.tagFamily
            color = (0, 255, 0)

            if lblY < 75:
                lblY = 75
            if lblY > image.shape[0]:
                lblY = image.shape[0]

            if (self.haveIntrinsics):
                pose = self.estimator.estimate(detection)
                rot = pose.rotation()

            units = "in"

            cv2.putText(image, tagID, (lblX, lblY - 75), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(image, f" X: {round(pose.X()*METERS_TO_INCHES, 1)} {units}", (lblX, lblY - 60), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(image, f" Y: {round(pose.Y()*METERS_TO_INCHES, 1)} {units}", (lblX, lblY - 45), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(image, f" Z: {round(pose.Z()*METERS_TO_INCHES, 1)} {units}", (lblX, lblY - 30), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(image, f"XA: {round(rot.x_degrees, 1)} deg", (lblX, lblY - 15), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(image, f"YA: {round(rot.y_degrees, 1)} deg", (lblX, lblY + 0), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            cv2.putText(image, f"ZA: {round(rot.z_degrees, 1)} deg", (lblX, lblY + 15), cv2.FONT_HERSHEY_TRIPLEX, 0.5, color)
            # print(f"X: {pose.X()*METERS_TO_INCHES}, Y: {pose.Y()*METERS_TO_INCHES}, Z: {pose.Z()*METERS_TO_INCHES}, XR: {rot.x_degrees}, YR: {rot.y_degrees}, ZR: {rot.z_degrees}")
        return detections


