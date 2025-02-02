"""
Provides a decorator for automatically showing the results of current stage to the screen.
"""

import os
import tkinter as tk
from typing import Callable, Dict
import cv2
from baboon_tracking.mixins.capture_mixin import CaptureMixin
from baboon_tracking.models.frame import Frame

from pipeline.stage_result import StageResult
from pipeline.decorators import runtime_config, stage


def show_result(function: Callable):
    """
    Provides a decorator for automatically showing the results of current stage to the screen.
    """
    prev_execute = function.execute
    display = True
    im_size = None
    capture = None
    frame_attributes = None

    def set_runtime_config(_, rconfig: Dict[str, any]):
        nonlocal display

        if "display" in rconfig:
            display = rconfig["display"]

    def set_capture(_, cap: CaptureMixin):
        nonlocal capture
        capture = cap

    def execute(self) -> StageResult:
        nonlocal im_size
        nonlocal frame_attributes

        result = prev_execute(self)

        if display:
            if im_size is None:
                scale = 0.85

                width = os.getenv("WIDTH")
                height = os.getenv("HEIGHT")

                if not width or not height:
                    if os.environ.get("DISPLAY", "") == "":
                        width = 0
                        height = 0
                    else:
                        root = tk.Tk()

                        width = root.winfo_screenwidth()
                        height = root.winfo_screenheight()

                width = int(width)
                height = int(height)

                width_scale = width / capture.frame_width
                height_scale = height / capture.frame_height

                if width_scale < height_scale:
                    height = capture.frame_height * width_scale
                else:
                    width = capture.frame_width * height_scale

                width = int(width * scale)
                height = int(height * scale)

                im_size = (width, height)

            if os.environ.get("DISPLAY", "") != "":
                # This searches the current object for frame types.
                if not frame_attributes:
                    frame_attributes = [
                        a for a in dir(self) if isinstance(getattr(self, a), Frame)
                    ]

                # Display one cv2.imshow for each frame object.
                for frame_attribute in frame_attributes:
                    cv2.imshow(
                        "{stage_name}.{frame_attribute}".format(
                            stage_name=type(self).__name__,
                            frame_attribute=frame_attribute,
                        ),
                        cv2.resize(
                            getattr(self, frame_attribute).get_frame(), im_size,
                        ),
                    )

        return result

    function.execute = execute
    function.show_result_set_runtime_config = set_runtime_config
    function.show_result_set_capture = set_capture

    function = runtime_config("show_result_set_runtime_config", is_property=True)(
        function
    )
    function = stage("show_result_set_capture", is_property=True)(function)

    return function
