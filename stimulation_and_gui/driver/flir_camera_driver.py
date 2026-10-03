import logging
from enum import Enum
from typing import Optional

import numpy as np
import PySpin

from driver.camera_driver import CameraDriver

logger = logging.getLogger(__name__)


class StreamMode(Enum):
    """
    'Enum' for choosing stream mode
    """

    STREAM_MODE_TELEDYNE_GIGE_VISION = (
        0  # Teledyne Gige Vision stream mode is the default stream mode for spinview which is supported on Windows
    )
    STREAM_MODE_PGRLWF = 1  # Light Weight Filter driver is our legacy driver which is supported on Windows
    STREAM_MODE_SOCKET = (
        2  # Socket is supported for MacOS and Linux, and uses native OS network sockets instead of a filter driver
    )


CHOSEN_STREAMMODE = StreamMode.STREAM_MODE_TELEDYNE_GIGE_VISION
NUM_IMAGES = 10  # number of images to grab


class FLIRCameraDriver(CameraDriver):
    def __init__(self) -> None:
        # Retrieve singleton reference to system object
        self._system = PySpin.System.GetInstance()

        self._cam_list = None
        self._camera = None
        self._nodemap = None
        self._nodemap_tldevice = None
        self._processor = None

        self._connected = False

        # Get current library version
        version = self._system.GetLibraryVersion()
        logger.info(f"Library version: {version.major}.{version.minor}.{version.type}.{version.build}")

    def connect(self):
        if self._connected:
            logger.warning("Already connected, skipping")

        # Retrieve list of cameras from the system
        self._cam_list = self._system.GetCameras()
        num_cameras = self._cam_list.GetSize()

        logger.info("Number of cameras detected: %d" % num_cameras)

        # Finish if there are no cameras
        if num_cameras == 0:
            logger.error("No camera detected!")
            self.disconnect()
            return

        self._camera = self._cam_list[0]

        try:
            # Initialize camera
            self._camera.Init()

            # Retrieve TL device nodemap and print device information
            self._nodemap_tldevice = self._camera.GetTLDeviceNodeMap()
            self._nodemap = self._camera.GetNodeMap()

            self._print_device_info()

            # Set Stream Modes
            self._set_stream_mode()

            node_acquisition_mode = PySpin.CEnumerationPtr(self._nodemap.GetNode("AcquisitionMode"))
            if not PySpin.IsReadable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                logger.error("Unable to set acquisition mode to continuous (enum retrieval). Aborting...")
                self.disconnect()
                return

            # Retrieve entry node from enumeration node
            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName("Continuous")
            if not PySpin.IsReadable(node_acquisition_mode_continuous):
                logger.error("Unable to set acquisition mode to continuous (entry retrieval). Aborting...")
                self.disconnect()
                return

            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)
            logger.info("Acquisition mode set to continuous...")

            self._camera.BeginAcquisition()

            device_serial_number = ""
            node_device_serial_number = PySpin.CStringPtr(self._nodemap_tldevice.GetNode("DeviceSerialNumber"))
            if PySpin.IsReadable(node_device_serial_number):
                device_serial_number = node_device_serial_number.GetValue()
                logger.info("Device serial number retrieved as %s..." % device_serial_number)

            # Create ImageProcessor instance for post processing images
            self._processor = PySpin.ImageProcessor()
            self._processor.SetColorProcessing(PySpin.SPINNAKER_COLOR_PROCESSING_ALGORITHM_HQ_LINEAR)

        except PySpin.SpinnakerException as ex:
            logger.error("Error: %s" % ex)
            self.disconnect()
            return

        self._connected = True

    def disconnect(self):
        self._processor = None
        self._nodemap_tldevice = None
        self._nodemap = None

        if self._camera is not None:
            self._camera.EndAcquisition()
            self._camera.DeInit()
            del self._camera
            self._camera = None

        if self._cam_list is not None:
            self._cam_list.Clear()
            self._cam_list = None

        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def read_frame(self) -> Optional[np.ndarray]:
        if self._camera is None or self._processor is None:
            return None
        try:
            image_result = self._camera.GetNextImage(100)
            if image_result.IsIncomplete():
                logger.warning("Image incomplete with image status %d ..." % image_result.GetImageStatus())

            else:
                width = image_result.GetWidth()
                height = image_result.GetHeight()

                image_converted = self._processor.Convert(image_result, PySpin.PixelFormat_Mono8)
                image_result.Release()

                return image_converted.GetNDArray()

        except PySpin.SpinnakerException as ex:
            logger.error("Error: %s" % ex)
            return None

    def close(self):
        self.disconnect()
        self._system.ReleaseInstance()

    def __del__(self):
        self.close()

    def _set_stream_mode(self):
        """
        This function changes the stream mode
        """
        if self._camera is None:
            return False

        streamMode = "TeledyneGigeVision"

        if CHOSEN_STREAMMODE == StreamMode.STREAM_MODE_TELEDYNE_GIGE_VISION:
            streamMode = "TeledyneGigeVision"
        elif CHOSEN_STREAMMODE == StreamMode.STREAM_MODE_PGRLWF:
            streamMode = "LWF"
        elif CHOSEN_STREAMMODE == StreamMode.STREAM_MODE_SOCKET:
            streamMode = "Socket"

        result = True

        # Retrieve Stream nodemap
        nodemap_tlstream = self._camera.GetTLStreamNodeMap()

        # In order to access the node entries, they have to be casted to a pointer type (CEnumerationPtr here)
        node_stream_mode = PySpin.CEnumerationPtr(nodemap_tlstream.GetNode("StreamMode"))

        # The node "StreamMode" is only available for GEV cameras.
        # Skip setting stream mode if the node is inaccessible.
        if not PySpin.IsReadable(node_stream_mode) or not PySpin.IsWritable(node_stream_mode):
            return True

        # Retrieve the desired entry node from the enumeration node
        node_stream_mode_custom = PySpin.CEnumEntryPtr(node_stream_mode.GetEntryByName(streamMode))

        if not PySpin.IsReadable(node_stream_mode_custom):
            # Failed to get custom stream node
            logger.error("Stream mode " + streamMode + " not available. Aborting...")
            return False

        # Retrieve integer value from entry node
        stream_mode_custom = node_stream_mode_custom.GetValue()

        # Set integer as new value for enumeration node
        node_stream_mode.SetIntValue(stream_mode_custom)

        logger.info("Stream Mode set to %s..." % node_stream_mode.GetCurrentEntry().GetSymbolic())
        return result

    def _print_device_info(self):
        if self._nodemap_tldevice is None:
            return

        print("*** DEVICE INFORMATION ***\n")

        try:
            result = True
            node_device_information = PySpin.CCategoryPtr(self._nodemap_tldevice.GetNode("DeviceInformation"))

            if PySpin.IsReadable(node_device_information):
                features = node_device_information.GetFeatures()
                for feature in features:
                    node_feature = PySpin.CValuePtr(feature)
                    print(
                        "%s: %s"
                        % (
                            node_feature.GetName(),
                            node_feature.ToString() if PySpin.IsReadable(node_feature) else "Node not readable",
                        )
                    )

            else:
                print("Device control information not readable.")

        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            return False

        return result
