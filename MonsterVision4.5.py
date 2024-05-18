#!/usr/bin/env python3

import json
import cv2
import depthai as dai
import contextlib
import CameraPipeline as cp
from Detections import Detections
from AprilTag5 import AprilTag

# Stuff that may change from year to year
# Ideally, this would be in a config file

tagFamily = "tag36h11"
tagSize = 0.1651            # 6.5 inches


# Prints "interesting" information about the camera
# and returns the camera intrinsics

def printDeviceInfo(devInfo: dai.DeviceInfo):
        device: dai.Device = dai.Device(deviceInfo)
        mxId = deviceInfo.getMxId()
        cameras = device.getConnectedCameras()
        usbSpeed = device.getUsbSpeed()
        calibData = device.readCalibration()
        try:
            eepromData = calibData.getEepromData()
        except:
            eepromData = None
        if eepromData is not None: productName = eepromData.productName

        print("   >>> MXID:", mxId)
        print("   >>> Num of cameras:", len(cameras))
        for cam in cameras:
            print("   >>> Camera:", cam)
        print("   >>> USB speed:", usbSpeed)
        if eepromData is not None and eepromData.boardName != "":
            print("   >>> Board name:", eepromData.boardName)
        if eepromData is not None and eepromData.productName != "":
            print("   >>> Product name:", eepromData.productName)

        xxx = device.getIrDrivers()
        print("   >>> IR drivers:", xxx)

        return


with contextlib.ExitStack() as stack:
    deviceInfos = dai.Device.getAllAvailableDevices()

    oakCameras = []

    # This section enumerates all connected devices and prints out their information
    # It needs to be customized to each year's set of cameras and uses

    for deviceInfo in deviceInfos:
        deviceInfo: dai.DeviceInfo

        cameraIntrinsics = printDeviceInfo(deviceInfo)
        mxId = deviceInfo.getMxId()
        print("===Connected to ", mxId)

        # Here we can customize the NN being used on the camera
        # You can have different NN's on each camera (or none)

        # cam1 = cp.CameraPipeline(deviceInfo, True, "/boot/nn.json")
        cam1 = cp.CameraPipeline(deviceInfo, False, "/boot/nn.json")
        sdn = cam1.setupSDN()
        cam1.buildPipeline(sdn)
        cam1.startPipeline()

        # Either of the following can be set to None if not needed for a particular camera

        detector = Detections(cam1.bbfraction, cam1.LABELS)
        tagDetector = AprilTag(tagFamily, tagSize, cam1.cameraIntrinsics)

        oakCameras.append((cam1, mxId, detector, tagDetector))


    while True:
        cam : cp
        for (cam, mxId, detector, tagDetector) in oakCameras:
            cam.processNextFrame()
            if detector is not None and cam.detections is not None and len(cam.detections) != 0:
                objects = detector.processDetections(cam.detections, cam.frame, cam.depthFrameColor, cam.fps)
            if tagDetector is not None and cam.frame is not None:
                tagDetector.detect(cam.frame)
            if cam.frame is not None:
                cv2.imshow(mxId + " rgb", cam.frame)
            # if cam.ispFrame is not None:
            #     cv2.imshow(mxId + " ISP", cam.ispFrame) 
            # if cam.depthFrameColor is not None:
            #     cv2.imshow(mxId + " depth", cam.depthFrameColor)

        if cv2.waitKey(1) == ord('q'):
            break