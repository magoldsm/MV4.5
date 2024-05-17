#!/usr/bin/env python3

import cv2
import depthai as dai
import contextlib
import CameraPipeline as cp
from Detections import Detections



with contextlib.ExitStack() as stack:
    deviceInfos = dai.Device.getAllAvailableDevices()
    usbSpeed = dai.UsbSpeed.SUPER
    openVinoVersion = dai.OpenVINO.Version.VERSION_UNIVERSAL

    oakCameras = []

    for deviceInfo in deviceInfos:
        deviceInfo: dai.DeviceInfo
        # examineDevice(deviceInfo)

        device: dai.Device = dai.Device(deviceInfo)
        print("===Connected to ", deviceInfo.getMxId())
        mxId = deviceInfo.getMxId()
        cameras = device.getConnectedCameras()
        usbSpeed = device.getUsbSpeed()
        try:
            eepromData = device.readCalibration().getEepromData()
        except:
            eepromData = None
        print("   >>> MXID:", mxId)
        print("   >>> Num of cameras:", len(cameras))
        print("   >>> USB speed:", usbSpeed)
        if eepromData is not None and eepromData.boardName != "":
            print("   >>> Board name:", eepromData.boardName)
        if eepromData is not None and eepromData.productName != "":
            print("   >>> Product name:", eepromData.productName)

        xxx = device.getIrDrivers()
        print("   >>> IR drivers:", xxx)

        if eepromData is not None: productName = eepromData.productName

        cameras = None
        usbSpeed = None
        eepromData = None
        device = None
        
        cam1 = cp.CameraPipeline(deviceInfo, "/boot/nn.json")
        sdn = cam1.setupSDN()
        cam1.buildPipeline(sdn)
        cam1.startPipeline()

        detector = Detections(cam1.bbfraction, cam1.LABELS)

        oakCameras.append((cam1, mxId, detector))


    while True:
        cam : cp
        for (cam, mxId, detector) in oakCameras:
            cam.processNextFrame()
            if cam.detections is not None and len(cam.detections) != 0:
                objects = detector.processDetections(cam.detections, cam.frame, cam.depthFrameColor, cam.fps)
            if cam.frame is not None:
                cv2.imshow(mxId + " rgb", cam.frame)
            # if cam.ispFrame is not None:
            #     cv2.imshow(mxId + " ISP", cam.ispFrame) 
            # if cam.depthFrameColor is not None:
            #     cv2.imshow(mxId + " depth", cam.depthFrameColor)

        if cv2.waitKey(1) == ord('q'):
            break