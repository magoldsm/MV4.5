# Import libraries
import json
import sys
import time

import ConfigManager

usingNTCore = False
try:
# Older OSes use pynetworktables
    from networktables import NetworkTables
    from networktables import NetworkTablesInstance
except ImportError:
# New have ntcore preinstalled
    import ntcore # type: ignore
    usingNTCore = True

import cv2
import platform

cscoreAvailable = True
try:
    from cscore import CameraServer # type: ignore
except ImportError:
    cscoreAvailable = False

ROMI_FILE = "/boot/romi.json"   # used when running on a Romi robot
FRC_FILE = "/boot/frc.json"     # Some camera settings incuding laser power
NN_FILE = "/boot/nn.json"       # NN config file


# TODO - move to config file

CAMERA_FPS = 25
DESIRED_FPS = 10		# seem to actually get 1/2 this.  Don't know why.....; THIS IS BECAUSE OF MATH BELOW MEANS THAT YOU GET 25  % 10 = 5
PREVIEW_WIDTH = 200
PREVIEW_HEIGHT = 200
DS_SCALE = 0.25         # Amount to scale down the composite image before sending to DS

def extract_value(j, key, default=None, message=None):
    try:
        return j[key]
    except KeyError:
        if message is not None:
            print("config error in '" + FRC_FILE + "': " + message)
        return default
    


class FRC:


    def __init__(self):
        # Tells you if you are on the robot or not by looking at the platform name (if you are using the WPILib pi image?)
        # onRobot really should be called "headless".  It means there's no graphics capability on the underlying hardware

        self.onRobot = platform.uname().node == "wpilibpi"

        self.frcConfig = ConfigManager.FRCConfig(FRC_FILE)


        # NetworkTable Instance holder; Initialized below
        self.ntinst = None
        # Vision NetworkTable; Initialized below; getTable MonsterVision
        self.sd = None
        # Num frames; Maybe used for FPS counting?
        self.frame_counter = 0
        # FPS counting
        self.lastTime = 0

        if usingNTCore:
            self.ntinst = ntcore.NetworkTableInstance.getDefault()
        else:
            self.ntinst = NetworkTablesInstance.getDefault() # Create a NetworkTable Instance

        # Sets up the NT depending on config
        if self.frcConfig.server:
            print("Setting up NetworkTables server")
            self.ntinst.startServer()
        else:
            print("Setting up NetworkTables client for team {}".format(self.frcConfig.team))
            self.ntinst.startClientTeam(self.frcConfig.team)
            self.ntinst.startDSClient()

        if usingNTCore:
            self.sd = self.ntinst.getTable("MonsterVision")
        else:
            self.sd = NetworkTables.getTable("MonsterVision") # Get the MonsterVision NT; Maybe creates it

        # TODO perhaps width should be function of # of cameras

        if cscoreAvailable:
            # self.cs = CameraServer.getInstance()
            CameraServer.enableLogging()
            self.csoutput = CameraServer.putVideo("MonsterVision", PREVIEW_WIDTH, PREVIEW_HEIGHT) # TODOnot        


    # Return True if we're running on Romi.  False if we're a coprocessor on a big 'bot
    # Never used but checks if the files exists
    def is_romi(self):
        try:
            with open(self.ROMI_FILE, "rt", encoding="utf-8") as f:
                json.load(f)
                # j = json.load(f)
        except OSError as err:
            print("Could not open '{}': {}".format(self.ROMI_FILE, err), file=sys.stderr)
            return False
        return True


    # NT writing for NN detections and AprilTags
    def writeObjectsToNetworkTable(self, objects, cam):
        jasonString = json.dumps(objects)
        res = self.sd.putString("ObjectTracker-" + cam.name, jasonString)
        res = self.ntinst.flush() # Puts all values onto table immediately
        res = True


    def displayCamResults(self, cam):
        if not self.onRobot:
            if cam.frame is not None:
                cv2.imshow(cam.name + " rgb", cam.frame)
            # if cam.ispFrame is not None:
            #     cv2.imshow(cam.name + " ISP", cam.ispFrame) 
            if cam.depthFrameColor is not None:
                cv2.imshow(cam.name + " depth", cam.depthFrameColor)


    # Composite all camera images into a single frame for DS display

    def sendResultsToDS(self, cams):
        # First, enumerate the images

        if cscoreAvailable:
            images = []
            for camTuple in cams:
                cam = camTuple[0]
                if cam.frame is not None:
                    images.append(cam.frame)

            if len(images) > 0:
                if len(images) > 1:
                    img = cv2.hconcat(images)
                else:
                    img = images[0]

                dim = (int(img.shape[1] * DS_SCALE) , int(img.shape[0] * DS_SCALE))
                resized = cv2.resize(img, dim)
                self.csoutput.putFrame(resized)
