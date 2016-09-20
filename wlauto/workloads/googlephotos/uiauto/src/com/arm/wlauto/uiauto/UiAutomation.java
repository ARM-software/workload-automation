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
import com.android.uiautomator.core.UiScrollable;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.util.concurrent.TimeUnit;
import java.util.LinkedHashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Map.Entry;

public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "uxperf_googlephotos";

    public Bundle parameters;
    public String packageName;
    public String packageID;

    private int viewTimeoutSecs = 10;
    private long viewTimeout =  TimeUnit.SECONDS.toMillis(viewTimeoutSecs);

    public void runUiAutomation() throws Exception {
        parameters = getParams();
        packageName = parameters.getString("package");
        packageID = packageName + ":id/";

        sleep(5); // Pause while splash screen loads
        setScreenOrientation(ScreenOrientation.NATURAL);
        dismissWelcomeView();
        closePromotionPopUp();
        selectWorkingGallery();
        gesturesTest();
        editPhotoColorTest();
        cropPhotoTest();
        rotatePhotoTest();
        unsetScreenOrientation();
    }

    public void dismissWelcomeView() throws Exception {
        // Click through the first two pages and make sure that we don't sign
        // in to our google account. This ensures the same set of photographs
        // are placed in the camera directory for each run.
        UiObject getStartedButton =
            new UiObject(new UiSelector().textContains("Get started")
                                         .className("android.widget.Button"));

        if (getStartedButton.waitForExists(viewTimeout)) {
            getStartedButton.click();
        }

        // A network connection is not required for this workload. However,
        // when the Google Photos app is invoked from the multiapp workload a
        // connection is required for sharing content. Handle the different UI
        // pathways when dismissing welcome views here.
        UiObject doNotSignInButton =
            new UiObject(new UiSelector().resourceId(packageID + "dont_sign_in_button"));

        if (doNotSignInButton.exists()) {
            doNotSignInButton.click();
        } else {
            UiObject welcomeButton =
                getUiObjectByResourceId(packageID + "name",
                        "android.widget.TextView");
            welcomeButton.click();

            UiObject useWithoutAccount =
                getUiObjectByText("Use without an account", "android.widget.TextView");
            useWithoutAccount.clickAndWaitForNewWindow();

            // Folder containing test images (early check required)
            UiObject workingFolder = new UiObject(new UiSelector().text("wa-working"));

            // On some devices the welcome views don't always appear so check
            // for the existence of the wa-working directory before attempting
            // to dismiss welcome views promoting app features
            if (!workingFolder.exists()) {
                sleep(1);
                uiDeviceSwipeLeft(10);
                sleep(1);
                uiDeviceSwipeLeft(10);
                sleep(1);
                uiDeviceSwipeLeft(10);
                sleep(1);
            }
        }

        UiObject nextButton =
            new UiObject(new UiSelector().resourceId(packageID + "next_button")
                                         .className("android.widget.ImageView"));

        if (nextButton.exists()) {
            nextButton.clickAndWaitForNewWindow();
        }
    }

    public void closePromotionPopUp() throws Exception {
        UiObject promoCloseButton =
            new UiObject(new UiSelector().resourceId(packageID + "promo_close_button"));

        if (promoCloseButton.exists()) {
            promoCloseButton.click();
        }
    }

    // Helper to click on the wa-working gallery.
    public void selectWorkingGallery() throws Exception {
        UiObject workdir = new UiObject(new UiSelector().text("wa-working")
                                                        .className("android.widget.TextView"));

        // If the wa-working gallery is not present wait for a short time for
        // the media server to refresh its index.
        boolean discovered = workdir.waitForExists(viewTimeout);
        UiScrollable scrollView = new UiScrollable(new UiSelector().scrollable(true));

        if (!discovered && scrollView.exists()) {
            // First check if the wa-working directory is visible on the first
            // screen and if not scroll to the bottom of the screen to look for it.
            discovered = scrollView.scrollIntoView(workdir);

            // If still not discovered scroll back to the top of the screen and
            // wait for a longer amount of time for the media server to refresh
            // its index.
            if (!discovered) {
                // scrollView.scrollToBeggining() doesn't work for this
                // particular scrollable view so use device method instead
                for (int i = 0; i < 10; i++) {
                    uiDeviceSwipeUp(20);
                }
                discovered = workdir.waitForExists(TimeUnit.SECONDS.toMillis(60));

                // Scroll to the bottom of the screen one last time
                if (!discovered) {
                    discovered = scrollView.scrollIntoView(workdir);
                }
            }
        }

        if (discovered) {
            workdir.clickAndWaitForNewWindow();
        } else {
            throw new UiObjectNotFoundException("Could not find \"wa-working\" folder");
        }
    }

    // Helper to click on an individual photograph based on index in wa-working gallery.
    public void selectPhoto(final int index) throws Exception {
        UiObject photo =
            new UiObject(new UiSelector().resourceId(packageID + "recycler_view")
                                         .childSelector(new UiSelector()
                                         .index(index)));

        // On some versions of the app a non-zero index is used for the
        // photographs position while on other versions a zero index is used.
        // Try both possiblities before throwing an exception.
        if (photo.exists()) {
            photo.click();
        } else {
            photo = new UiObject(new UiSelector().resourceId(packageID + "recycler_view")
                                                 .childSelector(new UiSelector()
                                                 .index(index - 1)));
            photo.click();
        }
    }

    // Helper that accepts, closes and navigates back to application home screen after an edit operation.
    // dontsave - True will discard the image. False will save the image
    public void closeAndReturn(final boolean dontsave) throws Exception {
        UiObject accept = new UiObject(new UiSelector().description("Accept"));
        UiObject done = new UiObject(new UiSelector().resourceId(packageID + "cpe_save_button"));

        long timeout =  TimeUnit.SECONDS.toMillis(3);

        // On some edit operations we can either confirm an edit with "Accept" or "DONE"
        if (accept.waitForExists(timeout)) {
            accept.click();
        } else if (done.waitForExists(timeout)) {
            done.click();
        } else {
            throw new UiObjectNotFoundException("Could not find \"Accept\" or \"DONE\" button.");
        }

        if (dontsave) {
            UiObject close = getUiObjectByDescription("Close editor", "android.widget.ImageView");
            close.click();

            UiObject discard = getUiObjectByText("DISCARD", "android.widget.Button");
            discard.waitForExists(viewTimeout);
            discard.click();
        } else {
            UiObject save = getUiObjectByText("SAVE", "android.widget.TextView");
            save.waitForExists(viewTimeout);
            save.click();
        }

        UiObject navigateUpButton =
            new UiObject(new UiSelector().descriptionContains("Navigate Up")
                                         .className("android.widget.ImageButton"));
        navigateUpButton.waitForExists(viewTimeout);
        navigateUpButton.click();
    }

    private void gesturesTest() throws Exception {
        String testTag = "gesture";

        // Perform a range of swipe tests while browsing photo gallery
        LinkedHashMap<String, GestureTestParams> testParams = new LinkedHashMap<String, GestureTestParams>();
        testParams.put("swipe_left", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.LEFT, 10));
        testParams.put("pinch_out", new GestureTestParams(GestureType.PINCH, PinchType.OUT, 100, 50));
        testParams.put("pinch_in", new GestureTestParams(GestureType.PINCH, PinchType.IN, 100, 50));
        testParams.put("swipe_right", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.RIGHT, 10));

        Iterator<Entry<String, GestureTestParams>> it = testParams.entrySet().iterator();

        // Select first photograph
        selectPhoto(1);

        while (it.hasNext()) {
            Map.Entry<String, GestureTestParams> pair = it.next();
            GestureType type = pair.getValue().gestureType;
            Direction dir = pair.getValue().gestureDirection;
            PinchType pinch = pair.getValue().pinchType;
            int steps = pair.getValue().steps;
            int percent = pair.getValue().percent;

            UiObject view = new UiObject(new UiSelector().enabled(true));

            if (!view.waitForExists(viewTimeout)) {
                throw new UiObjectNotFoundException("Could not find \"photo view\".");
            }

            String runName = String.format(testTag + "_" + pair.getKey());
            ActionLogger logger = new ActionLogger(runName, parameters);
            logger.start();

            switch (type) {
                case UIDEVICE_SWIPE:
                    uiDeviceSwipe(dir, steps);
                    break;
                case PINCH:
                    uiObjectVertPinch(view, pinch, steps, percent);
                    break;
                default:
                    break;
            }

            logger.stop();
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
        String testTag = "edit";

        // Perform a range of swipe tests while browsing photo gallery
        LinkedHashMap<String, SeekBarTestParams> testParams = new LinkedHashMap<String, SeekBarTestParams>();
        testParams.put("color_increment", new SeekBarTestParams(Position.RIGHT, 10, 20));
        testParams.put("color_reset", new SeekBarTestParams(Position.CENTRE, 0, 0));
        testParams.put("color_decrement", new SeekBarTestParams(Position.LEFT, 10, 20));

        Iterator<Entry<String, SeekBarTestParams>> it = testParams.entrySet().iterator();

        // Select second photograph
        selectPhoto(2);

        UiObject editView = getUiObjectByResourceId(packageID + "edit",
                                                    "android.widget.ImageView");
        editView.click();

        // Manage potential different spelling of UI element
        UiObject editCol = new UiObject(new UiSelector().textMatches("Colou?r"));
        long timeout =  TimeUnit.SECONDS.toMillis(3);
        if (editCol.waitForExists(timeout)) {
            editCol.click();
        } else {
            throw new UiObjectNotFoundException(String.format("Could not find \"%s\" \"%s\"",
                                                              "Color/Colour", "android.widget.RadioButton"));
        }

        UiObject seekBar = getUiObjectByResourceId(packageID + "cpe_strength_seek_bar",
                                                   "android.widget.SeekBar");

        while (it.hasNext()) {
            Map.Entry<String, SeekBarTestParams> pair = it.next();
            Position pos = pair.getValue().seekBarPosition;
            int steps = pair.getValue().steps;
            int percent = pair.getValue().percent;

            String runName = String.format(testTag + "_" + pair.getKey());
            ActionLogger logger = new ActionLogger(runName, parameters);

            sleep(1); // pause for stability before editing the colour

            logger.start();
            seekBarTest(seekBar, pos, steps);
            logger.stop();
        }

        closeAndReturn(true);
    }

    private void cropPhotoTest() throws Exception {
        String testTag = "crop";

        // To improve travel accuracy perform the slide bar operation slowly
        final int steps = 500;

        // Perform a range of swipe tests while browsing photo gallery
        LinkedHashMap<String, Position> testParams = new LinkedHashMap<String, Position>();
        testParams.put("tilt_positive", Position.LEFT);
        testParams.put("tilt_reset", Position.RIGHT);
        testParams.put("tilt_negative", Position.RIGHT);

        Iterator<Entry<String, Position>> it = testParams.entrySet().iterator();

        // Select third photograph
        selectPhoto(3);

        UiObject editView = getUiObjectByResourceId(packageID + "edit",
                                                    "android.widget.ImageView");
        editView.click();

        UiObject cropTool = getUiObjectByResourceId(packageID + "cpe_crop_tool",
                                                    "android.widget.ImageView");
        cropTool.click();

        UiObject straightenSlider = getUiObjectByResourceId(packageID + "cpe_straighten_slider");

        while (it.hasNext()) {
            Map.Entry<String, Position> pair = it.next();
            Position pos = pair.getValue();

            String runName = String.format(testTag + "_" + pair.getKey());
            ActionLogger logger = new ActionLogger(runName, parameters);

            logger.start();
            slideBarTest(straightenSlider, pos, steps);
            logger.stop();
        }

        closeAndReturn(true);
    }

    private void rotatePhotoTest() throws Exception {
        String testTag = "rotate";

        String[] subTests = {"90", "180", "270"};

        // Select fourth photograph
        selectPhoto(4);

        UiObject editView = getUiObjectByResourceId(packageID + "edit",
                                                    "android.widget.ImageView");
        editView.click();

        UiObject cropTool = getUiObjectByResourceId(packageID + "cpe_crop_tool");
        cropTool.click();

        UiObject rotate = getUiObjectByResourceId(packageID + "cpe_rotate_90");

        for (String subTest : subTests) {
            String runName = String.format(testTag + "_" + subTest);
            ActionLogger logger = new ActionLogger(runName, parameters);

            logger.start();
            rotate.click();
            logger.stop();
        }

        closeAndReturn(true);
    }

    // Helper to slide the seekbar during photo edit.
    private void seekBarTest(final UiObject view, final Position pos, final int steps) throws Exception {
        final int SWIPE_MARGIN_LIMIT = 5;
        Rect rect = view.getVisibleBounds();

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
    }

    // Helper to slide the slidebar during photo edit.
    private void slideBarTest(final UiObject view, final Position pos, final int steps) throws Exception {
        final int SWIPE_MARGIN_LIMIT = 5;
        Rect rect = view.getBounds();

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
    }
}
