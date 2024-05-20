import json
import sys

class ComputedValue:
    def __init__(self, value):
        self.value = value

    # def __repr__(self):
    #     return str(self.value)
    

class ConfigManager:

    def __init__(self, file: str, configTable):
        self.file = file
        self.success = False

        try:
            with open(self.file, "rt", encoding="utf-8") as f:
                j = json.load(f)
        except OSError as err:
            raise Exception("could not open '{}': {}".format(self.file, err))
        
        # top level must be an object
        if not isinstance(j, dict):
            raise Exception("must be JSON object")


        
        for entry in configTable:
       
            try:
                entry['value'].value = j[entry['name']]
            except:
                if entry['mess'] is not None:
                    raise Exception("config error in '" + self.file + "': " + entry['mess'].value)
                pass

        self.success = True


# Derive a new class from ComputedValue


class FRCConfig (ConfigManager):

    __team = ComputedValue(0)
    __hasDisplay = ComputedValue(False)
    __ntmode = ComputedValue("client")
    __LaserDotProjectorCurrent = ComputedValue(0)

    __table = [
        { "name" : "team", "value" : __team, "mess" : "Could not read team number"},
        { "name" : "hasDisplay", "value" : __hasDisplay, "mess" : None},
        { "name" : "ntmode", "value" : __ntmode, "mess" : None},
        { "name" : "LaserDotProjectorCurrent", "value" : __LaserDotProjectorCurrent, "mess" : None}
    ]

    def __init__(self, file: str):
        super().__init__( file, self.__table)

        if self.success:
            if self.__ntmode.value == "client":
                self.server = False
            elif self.__ntmode.value == "server":
                self.server = True
            else:
                success = False
                raise Exception(f"could not understand ntmode value '{self.__ntmode.value}'")
            self.team = self.__team.value
            self.hasDisplay = self.__hasDisplay.value
            self.LaserDotProjectorCurrent = self.__LaserDotProjectorCurrent.value * 1.0

            

