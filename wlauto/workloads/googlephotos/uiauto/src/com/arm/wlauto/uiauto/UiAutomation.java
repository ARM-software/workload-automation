/*    Copyright 2014-2016 ARM Limited
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

package com.arm.wlauto.uiauto.googlephotos;

import android.os.Bundle;
import android.graphics.Rect;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.util.concurrent.TimeUnit;
import java.util.LinkedHashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Map.Entry;

public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "uxperf_googlephotos";

    public Bundle parameters;
    private int viewTimeoutSecs = 10;
    private long viewTimeout =  TimeUnit.SECONDS.toMillis(viewTimeoutSecs);
    private LinkedHashMap<String, Timer> timingResults = new LinkedHashMap<String, Timer>();

    public void runUiAutomation() throws Exception {
        parameters = getParams();

        pauseForSplashScreen();
        setScreenOrientation(ScreenOrientation.NATURAL);
        confirmAccess();
        dismissWelcomeView();
        selectWorkingGallery();
        gesturesTest();
        editPhotoColorTest();
        cropPhotoTest();
        rotatePhotoTest();
        unsetScreenOrientation();

        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    public void pauseForSplashScreen() {
        sleep(5); // Pause while splash screen loads
    }

    public void dismissWelcomeView() throws Exception {

        // Click through the first two pages and make sure that we don't sign
        // in to our google account. This ensures the same set of photographs
        // are placed in the camera directory for each run.

        UiObject getStartedButton =
            new UiObject(new UiSelector().textContains("Get started")
                                         .className("android.widget.Button"));

        waitObject(getStartedButton, viewTimeoutSecs);
        getStartedButton.click();

        UiObject welcomeButton =
            getUiObjectByResourceId("com.google.android.apps.photos:id/name",
                                    "android.widget.TextView");
        welcomeButton.click();

        UiObject useWithoutAccount =
            getUiObjectByText("Use without an account", "android.widget.TextView");
        useWithoutAccount.clickAndWaitForNewWindow();

        // Dismiss welcome views promoting app features
        sleep(1);
        uiDeviceSwipeLeft(10);
        sleep(1);
        uiDeviceSwipeLeft(10);
        sleep(1);
        uiDeviceSwipeLeft(10);
        sleep(1);

        UiObject nextButton =
            getUiObjectByResourceId("com.google.android.apps.photos:id/next_button",
                                    "android.widget.ImageView");
        nextButton.clickAndWaitForNewWindow();

        UiObject workingFolder = new UiObject(new UiSelector().text("wa-working"));
        waitObject(workingFolder, viewTimeoutSecs);
    }

    private void gesturesTest() throws Exception {
        String testTag = "gestures";

        // Perform a range of swipe tests while browsing photo gallery
        LinkedHashMap<String, GestureTestParams> testParams = new LinkedHashMap<String, GestureTestParams>();
        testParams.put("swipe_left", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.LEFT, 10));
        testParams.put("pinch_out", new GestureTestParams(GestureType.PINCH, PinchType.OUT, 100, 50));
        testParams.put("pinch_in", new GestureTestParams(GestureType.PINCH, PinchType.IN, 100, 50));
        testParams.put("swipe_right", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.RIGHT, 10));

        Iterator<Entry<String, GestureTestParams>> it = testParams.entrySet().iterator();

        // Select first photograph
        selectPhoto(0);

        while (it.hasNext()) {
            Map.Entry<String, GestureTestParams> pair = it.next();
            GestureType type = pair.getValue().gestureType;
            Direction dir = pair.getValue().gestureDirection;
            PinchType pinch = pair.getValue().pinchType;
            int steps = pair.getValue().steps;
            int percent = pair.getValue().percent;

            String runName = String.format(testTag + "_" + pair.getKey());
            String gfxInfologName =  String.format(runName + "_gfxInfo.log");
            String surfFlingerlogName =  String.format(runName + "_surfFlinger.log");

            UiObject view = new UiObject(new UiSelector().enabled(true));

            if (!view.waitForExists(viewTimeout)) {
                throw new UiObjectNotFoundException("Could not find \"photo view\".");
            }

            startDumpsysGfxInfo(parameters);
            startDumpsysSurfaceFlinger(parameters);

            Timer result = new Timer();

            switch (type) {
                case UIDEVICE_SWIPE:
                    result = uiDeviceSwipeTest(dir, steps);
                    break;
                case UIOBJECT_SWIPE:
                    result = uiObjectSwipeTest(view, dir, steps);
                    break;
                case PINCH:
                    result = uiObjectVertPinchTest(view, pinch, steps, percent);
                    break;
                default:
                    break;
            }

            stopDumpsysSurfaceFlinger(parameters, surfFlingerlogName);
            stopDumpsysGfxInfo(parameters, gfxInfologName);

            timingResults.put(runName, result);
        }

        UiObject navigateUpButton =
            getUiObjectByDescription("Navigate Up", "android.widget.ImageButton");
        navigateUpButton.click();
    }

    public enum Position { LEFT, RIGHT, CENTRE };

    private class SeekBarTestParams {

        private Position seekBarPosition;
        private int percent;
        private int steps;

        SeekBarTestParams(final Position position, final int steps, final int percent) {
            this.seekBarPosition = position;
            this.steps = steps;
            this.percent = percent;
        }
    }

    private void editPhotoColorTest() throws Exception {
        String testTag = "edit_photo";

        // Perform a range of swipe tests while browsing photo gallery
        LinkedHashMap<String, SeekBarTestParams> testParams = new LinkedHashMap<String, SeekBarTestParams>();
        testParams.put("increment_color", new SeekBarTestParams(Position.RIGHT, 10, 20));
        testParams.put("reset_color", new SeekBarTestParams(Position.CENTRE, 0, 0));
        testParams.put("decrement_color", new SeekBarTestParams(Position.LEFT, 10, 20));

        Iterator<Entry<String, SeekBarTestParams>> it = testParams.entrySet().iterator();

        // Select second photograph
        selectPhoto(1);
        UiObject editView = getUiObjectByResourceId("com.google.android.apps.photos:id/edit",
                                                    "android.widget.ImageView");
        editView.click();

        // Manage potential different spelling of UI element
        UiObject editColor = new UiObject(new UiSelector().text("Color"));
        UiObject editColour = new UiObject(new UiSelector().text("Colour"));

        if (editColor.exists()) {
            editColor.click();
        } else if (editColour.exists()) {
            editColour.click();
        } else {
            throw new UiObjectNotFoundException(String.format("Could not find \"%s\" \"%s\"",
                                                              "Color/Colour", "android.widget.RadioButton"));
        }

        UiObject seekBar = getUiObjectByResourceId("com.google.android.apps.photos:id/cpe_strength_seek_bar",
                                                   "android.widget.SeekBar");

        while (it.hasNext()) {
            Map.Entry<String, SeekBarTestParams> pair = it.next();
            Position pos = pair.getValue().seekBarPosition;
            int steps = pair.getValue().steps;
            int percent = pair.getValue().percent;

            String runName = String.format(testTag + "_" + pair.getKey());
            String gfxInfologName =  String.format(runName + "_gfxInfo.log");
            String surfFlingerlogName =  String.format(runName + "_surfFlinger.log");

            startDumpsysGfxInfo(parameters);
            startDumpsysSurfaceFlinger(parameters);

            Timer result = new Timer();
            result = seekBarTest(seekBar, pos, steps);

            stopDumpsysSurfaceFlinger(parameters, surfFlingerlogName);
            stopDumpsysGfxInfo(parameters, gfxInfologName);

            timingResults.put(runName, result);
        }

        saveAndReturn();
    }

    private void cropPhotoTest() throws Exception {
        String testTag = "crop_photo";

        // To improve travel accuracy perform the slide bar operation slowly
        final int steps = 500;

        // Perform a range of swipe tests while browsing photo gallery
        LinkedHashMap<String, Position> testParams = new LinkedHashMap<String, Position>();
        testParams.put("tilt_positive", Position.LEFT);
        testParams.put("tilt_reset", Position.RIGHT);
        testParams.put("tilt_negative", Position.RIGHT);

        Iterator<Entry<String, Position>> it = testParams.entrySet().iterator();

        // Select third photograph
        selectPhoto(2);
        UiObject editView = getUiObjectByResourceId("com.google.android.apps.photos:id/edit",
                                                    "android.widget.ImageView");
        editView.click();

        UiObject cropTool = getUiObjectByResourceId("com.google.android.apps.photos:id/cpe_crop_tool",
                                                    "android.widget.ImageView");
        cropTool.click();

        UiObject straightenSlider = getUiObjectByResourceId("com.google.android.apps.photos:id/cpe_straighten_slider",
                                                             "android.view.View");

        while (it.hasNext()) {
            Map.Entry<String, Position> pair = it.next();
            Position pos = pair.getValue();

            String runName = String.format(testTag + "_" + pair.getKey());
            String gfxInfologName =  String.format(runName + "_gfxInfo.log");
            String surfFlingerlogName =  String.format(runName + "_surfFlinger.log");

            startDumpsysGfxInfo(parameters);
            startDumpsysSurfaceFlinger(parameters);

            Timer result = new Timer();
            result = slideBarTest(straightenSlider, pos, steps);

            stopDumpsysSurfaceFlinger(parameters, surfFlingerlogName);
            stopDumpsysGfxInfo(parameters, gfxInfologName);

            timingResults.put(runName, result);
        }

        saveAndReturn();
    }

    private void rotatePhotoTest() throws Exception {
        String testTag = "rotate_photo";

        String[] subTests = {"anticlockwise_90", "anticlockwise_180", "anticlockwise_270"};

        // Select fourth photograph
        selectPhoto(3);
        UiObject editView = getUiObjectByResourceId("com.google.android.apps.photos:id/edit",
                                                    "android.widget.ImageView");
        editView.click();

        UiObject cropTool = getUiObjectByResourceId("com.google.android.apps.photos:id/cpe_crop_tool",
                                                    "android.widget.ImageView");
        cropTool.click();

        UiObject rotate = getUiObjectByResourceId("com.google.android.apps.photos:id/cpe_rotate_90",
                                                  "android.widget.ImageView");

        for (String subTest : subTests) {
            String runName = String.format(testTag + "_" + subTest);
            String gfxInfologName =  String.format(runName + "_gfxInfo.log");
            String surfFlingerlogName =  String.format(runName + "_surfFlinger.log");

            startDumpsysGfxInfo(parameters);
            startDumpsysSurfaceFlinger(parameters);

            Timer result = new Timer();
            result.start();
            rotate.click();
            result.end();

            stopDumpsysSurfaceFlinger(parameters, surfFlingerlogName);
            stopDumpsysGfxInfo(parameters, gfxInfologName);

            timingResults.put(runName, result);
        }

        saveAndReturn();
    }

    // Helper to slide the seekbar during photo edit.
    private Timer seekBarTest(final UiObject view, final Position pos, final int steps) throws Exception {
        final int SWIPE_MARGIN_LIMIT = 5;
        Rect rect = view.getVisibleBounds();

        Timer result = new Timer();
        result.start();

        switch (pos) {
            case LEFT:
                getUiDevice().click(rect.left + SWIPE_MARGIN_LIMIT, rect.centerY());
                break;
            case RIGHT:
                getUiDevice().click(rect.right - SWIPE_MARGIN_LIMIT, rect.centerY());
                break;
            case CENTRE:
                view.click();
                break;
            default:
                break;
        }

        result.end();
        return result;
    }

    // Helper to slide the slidebar during photo edit.
    private Timer slideBarTest(final UiObject view, final Position pos, final int steps) throws Exception {
        final int SWIPE_MARGIN_LIMIT = 5;
        Rect rect = view.getBounds();

        Timer result = new Timer();
        result.start();

        switch (pos) {
            case LEFT:
                getUiDevice().drag(rect.left + SWIPE_MARGIN_LIMIT, rect.centerY(),
                                   rect.left + rect.width() / 4, rect.centerY(),
                                   steps);
                break;
            case RIGHT:
                getUiDevice().drag(rect.right - SWIPE_MARGIN_LIMIT, rect.centerY(),
                                   rect.right - rect.width() / 4, rect.centerY(),
                                   steps);
                break;
            default:
                break;
        }

        result.end();
        return result;
    }

    // Helper to click on the wa-working gallery.
    public void selectWorkingGallery() throws Exception {
        UiObject workdir = getUiObjectByText("wa-working", "android.widget.TextView");
        workdir.clickAndWaitForNewWindow();
    }

    // Helper to click on an individual photograph based on index in wa-working gallery.
    public void selectPhoto(final int index) throws Exception {
        UiObject photo =
            new UiObject(new UiSelector().resourceId("com.google.android.apps.photos:id/recycler_view")
                                         .childSelector(new UiSelector()
                                         .index(index)));
        photo.click();
    }

    // Helper that accepts, saves and navigates back to application home screen after an edit operation
    public void saveAndReturn() throws Exception {

        UiObject accept = getUiObjectByDescription("Accept", "android.widget.ImageView");
        accept.click();

        UiObject save = getUiObjectByText("SAVE", "android.widget.TextView");
        save.waitForExists(viewTimeout);
        save.click();

        UiObject navigateUpButton =
            new UiObject(new UiSelector().descriptionContains("Navigate Up")
                                         .className("android.widget.ImageButton"));
        navigateUpButton.waitForExists(viewTimeout);
        navigateUpButton.click();
    }

    // Helper to tag an individual photograph based on the index in wa-working
    // gallery.  After long clicking it tags the photograph with a tick in the
    // corner of the image to indicate that the photograph has been selected
    public void tagPhoto(final int index) throws Exception {
        UiObject photo =
            new UiObject(new UiSelector().resourceId("com.google.android.apps.photos:id/recycler_view")
                                         .childSelector(new UiSelector()
                                         .index(index)));
        photo.waitForExists(viewTimeout);
        uiDevicePerformLongClick(photo, 100);
    }
}
