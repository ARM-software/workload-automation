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


"""
State detection functionality for revent workloads. Uses OpenCV to analyse screenshots from the device.
Requires a 'statedetection' directory in the workload directory that includes the state definition yaml file,
and the 'templates' folder with PNGs of all templates mentioned in the yaml file.

Requires the following python plugins:
numpy, pyyaml (yaml), imutils and opencv (cv2)

"""

import cv2
import numpy as np
import imutils
import yaml
import os

class StateDefinitionError(RuntimeError):
	def __init__(self, arg):
		self.args = arg

def auto_canny(image, sigma=0.33):
	# compute the median of the single channel pixel intensities
	v = np.median(image)
 
	# apply automatic Canny edge detection using the computed median
	lower = int(max(0, (1.0 - sigma) * v))
	upper = int(min(255, (1.0 + sigma) * v))
	edged = cv2.Canny(image, lower, upper)
 
	# return the edged image
	return edged

def match_state(screenshotFile, defpath):
	# load and parse state definition file
	if not os.path.isfile(defpath+'/definition.yaml'): raise StateDefinitionError("Missing state definitions yaml file")
	stateDefinitions = yaml.load(file(defpath+'/definition.yaml', 'r'))	

	# check if file exists, then load screenshot into opencv and create edge map
	if not os.path.isfile(screenshotFile): raise StateDefinitionError("Screenshot file not found")
	img_rgb = cv2.imread(screenshotFile)
	img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
	img_edge = auto_canny(img_gray)

	# make a list of all templates defined in the state definitions
	templateList = []
	for state in stateDefinitions["workloadStates"]:
		templateList.extend(state["templates"])

	# check all template PNGs exist
	missingFiles = 0
	for templatePng in templateList:
		if not os.path.isfile(defpath+'/templates/'+templatePng+'.png'):
			missingFiles += 1

	if missingFiles: raise StateDefinitionError("Missing template PNG files")

	# try to match each PNG              
	matchedTemplates = []
	for templatePng in templateList:
		template = cv2.imread(defpath+'/templates/'+templatePng+'.png',0)
		template_edge = auto_canny(template)
		w, h = template.shape[::-1]

		res = cv2.matchTemplate(img_edge,template_edge,cv2.TM_CCOEFF_NORMED)
		threshold = 0.5
		loc = np.where(res >= threshold)
		zipped = zip(*loc[::-1])
		   
		if len(zipped) > 0: matchedTemplates.append(templatePng)


	# determine the state according to the matched templates
	matchedState = "none"
	for state in stateDefinitions["workloadStates"]:
		# look in the matched templates list for each template of this state
		matchCount = 0
		for template in state["templates"]:
			if template in matchedTemplates:
				matchCount += 1

		if matchCount >= state["matches"]:
			# we have a match
			matchedState = state["stateName"]
			break

	return matchedState

def verify_state(screenshotFile, stateDefsPath, workloadPhase):
	# run a match on the screenshot
	matchedState = match_state(screenshotFile, stateDefsPath)

	# load and parse state definition file
	if not os.path.isfile(stateDefsPath+'/definition.yaml'): raise StateDefinitionError("Missing state definitions yaml file")
	stateDefinitions = yaml.load(file(stateDefsPath+'/definition.yaml', 'r'))

	# find what the expected state is for the given workload phase
	expectedState = None
	for phase in stateDefinitions["workloadExpectedStates"]:
		if phase["phaseName"] == workloadPhase:
			expectedState = phase["expectedState"]

	if expectedState is None: raise StateDefinitionError("Phase not defined")

	return expectedState == matchedState
