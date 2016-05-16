/*    Copyright 2013-2015 ARM Limited
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
*/


package com.arm.wlauto.uiauto.cameracapture;

import java.util.concurrent.TimeUnit;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;
import android.view.KeyEvent;

import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

import com.arm.wlauto.uiauto.BaseUiAutomation;

public class UiAutomation extends BaseUiAutomation {

    public static String TAG = "cameracapture";
    int timeDurationBetweenEachCapture = 0;
    int sleepTime = 2;
    int iterations = 0;
    int api = 0;
    Integer[] version = {0,0,0};

    public void runUiAutomation() throws Exception {
        Bundle parameters = getParams();
        if (parameters.size() > 0) {
            iterations = Integer.parseInt(parameters
                    .getString("no_of_captures"));
            timeDurationBetweenEachCapture = Integer.parseInt(parameters
                    .getString("time_between_captures"));
            api = Integer.parseInt(parameters.getString("api_level"));
            String versionString = parameters.getString("version");
            version = splitVersion(versionString);
        }
        
        // Pre Android M UI
        if(api < 23) 
            takePhotosAosp();
        else
        {
            if(compareVersions(version, new Integer[]{3,2,0}) >= 0)
                takePhotosGoogleV3_2();
            else
                takePhotosGoogle();
        }
    }

    private void takePhotosAosp() throws Exception 
    {
        // switch to camera capture mode
        UiObject clickModes = new UiObject(new UiSelector().descriptionMatches("Camera, video or panorama selector"));
        clickModes.click();
        sleep(sleepTime);

        UiObject changeModeToCapture = new UiObject(new UiSelector().descriptionMatches("Switch to photo"));

        changeModeToCapture.click();
        sleep(sleepTime);

        // click to capture photos
        UiObject clickCaptureButton = new UiObject(new UiSelector().descriptionMatches("Shutter button"));

        for (int i = 0; i < iterations; i++) {
            clickCaptureButton.longClick();
            sleep(timeDurationBetweenEachCapture);
        }
        getUiDevice().pressBack();
    }

    private void takePhotosGoogleV3_2() throws Exception 
    {
        // clear tutorial if needed
        UiObject tutorialText = new UiObject(new UiSelector().resourceId("com.android.camera2:id/photoVideoSwipeTutorialText"));
        if (tutorialText.waitForExists(TimeUnit.SECONDS.toMillis(5))) {
            tutorialText.swipeLeft(5);
            sleep(sleepTime);
            tutorialText.swipeRight(5);
        }
        
        // ensure we are in photo mode
        UiObject viewFinder = new UiObject(new UiSelector().resourceId("com.android.camera2:id/viewfinder_frame"));
        viewFinder.swipeRight(5);

        // click to capture photos
        UiObject clickCaptureButton = new UiObject(new UiSelector().resourceId("com.android.camera2:id/photo_video_button"));

        for (int i = 0; i < iterations; i++) {
            clickCaptureButton.longClick();
            sleep(timeDurationBetweenEachCapture);
        }
    }

    private void takePhotosGoogle() throws Exception 
    {
        // open mode select menu
        UiObject swipeScreen = new UiObject(new UiSelector().resourceId("com.android.camera2:id/mode_options_overlay"));
        swipeScreen.swipeRight(5);

        // switch to video mode
        UiObject changeModeToCapture = new UiObject(new UiSelector().descriptionMatches("Switch to Camera Mode"));
        changeModeToCapture.click();
        sleep(sleepTime);

        // click to capture photos
        UiObject clickCaptureButton = new UiObject(new UiSelector().descriptionMatches("Shutter"));

        for (int i = 0; i < iterations; i++) {
            clickCaptureButton.longClick();
            sleep(timeDurationBetweenEachCapture);
        }
    }
}
