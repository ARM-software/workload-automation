#    Copyright 2013-2016 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# pylint: disable=no-member


"""
State detection functionality for revent workloads. Uses OpenCV to analyse screenshots from the device.
Requires a 'statedetection' directory in the workload directory that includes the state definition yaml file,
and the 'templates' folder with PNGs of all templates mentioned in the yaml file.

Requires the following Python libraries:
numpy, pyyaml (yaml), imutils and opencv-python

"""

import os

import yaml
try:
    import numpy as np
except ImportError:
    np = None
try:
    import cv2
except ImportError:
    cv2 = None
try:
    import imutils
except ImportError:
    imutils = None

from wlauto.exceptions import HostError


class StateDefinitionError(RuntimeError):
    pass


def auto_canny(image, sigma=0.33):
    # compute the median of the single channel pixel intensities
    v = np.median(image)

    # apply automatic Canny edge detection using the computed median
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)

    # return the edged image
    return edged


def check_match_state_dependencies():
    if np is None or cv2 is None or imutils is None:
        raise HostError("State detection requires numpy, opencv (cv2) and imutils.")


def match_state(screenshot_file, defpath, state_definitions):  # pylint: disable=too-many-locals
    # check dependencies
    check_match_state_dependencies()

    # check if file exists, then load screenshot into opencv and create edge map
    if not os.path.isfile(screenshot_file):
        raise StateDefinitionError("Screenshot file not found")
    img_rgb = cv2.imread(screenshot_file)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    img_edge = auto_canny(img_gray)

    # make a list of all templates defined in the state definitions
    template_list = []
    for state in state_definitions["workload_states"]:
        template_list.extend(state["templates"])

    # check all template PNGs exist
    for template_png in template_list:
        if not os.path.isfile(os.path.join(defpath, 'templates', template_png + '.png')):
            raise StateDefinitionError("Missing template PNG file: " + template_png + ".png")

    # try to match each PNG
    matched_templates = []
    for template_png in template_list:
        template = cv2.imread(os.path.join(defpath, 'templates', template_png + '.png'), 0)
        template_edge = auto_canny(template)
        template_height, template_width = template_edge.shape[:2]

        # loop over the scales of the image
        for scale in np.linspace(1.4, 0.6, 61):
            resized = imutils.resize(img_edge, width=int(img_edge.shape[1] * scale))

            # skip if the resized image is smaller than the template
            if resized.shape[0] < template_height or resized.shape[1] < template_width:
                break

            res = cv2.matchTemplate(resized, template_edge, cv2.TM_CCOEFF_NORMED)
            threshold = 0.4
            loc = np.where(res >= threshold)
            zipped = zip(*loc[::-1])

            if len(zipped) > 0:
                matched_templates.append(template_png)
                break

    # determine the state according to the matched templates
    matched_state = "none"
    for state in state_definitions["workload_states"]:
        # look in the matched templates list for each template of this state
        match_count = 0
        for template in state["templates"]:
            if template in matched_templates:
                match_count += 1

        if match_count >= state["matches"]:
            # we have a match
            matched_state = state["state_name"]
            break

    return matched_state


def verify_state(screenshot_file, state_defs_path, workload_phase):
    # load and parse state definition file
    statedefs_file = os.path.join(state_defs_path, 'definition.yaml')
    if not os.path.isfile(statedefs_file):
        raise StateDefinitionError("Missing state definitions yaml file: " + statedefs_file)
    with open(statedefs_file) as fh:
        state_definitions = yaml.load(fh)

    # run a match on the screenshot
    matched_state = match_state(screenshot_file, state_defs_path, state_definitions)

    # find what the expected state is for the given workload phase
    expected_state = None
    for phase in state_definitions["workload_phases"]:
        if phase["phase_name"] == workload_phase:
            expected_state = phase["expected_state"]

    if expected_state is None:
        raise StateDefinitionError("Phase not defined")

    return expected_state == matched_state
