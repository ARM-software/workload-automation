package com.arm.wlauto.uiauto.googlephotos;

import android.os.Bundle;

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

        confirmLocalFileAccess();
        dismissWelcomeView();
        gesturesTest();
        editPhotoTest();

        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    private void confirmLocalFileAccess() throws Exception {
        // First time run requires confirmation to allow access to local files
        UiObject allowButton = new UiObject(new UiSelector().textContains("Allow")
                                                            .className("android.widget.Button"));
        if (allowButton.waitForExists(timeout)) {
            allowButton.clickAndWaitForNewWindow(timeout);
        }
    }


    private void dismissWelcomeView() throws Exception {

        // Click through the first two pages and make sure that we don't sign
        // in to our google account. This ensures the same set of photographs
        // are placed in the camera directory for each run.

        sleep(5); // Pause while splash screen loads

        UiObject getStartedButton =
            new UiObject (new UiSelector().textContains("Get started")
                                          .className("android.widget.Button"));

        tapDisplayCentre();
        waitObject(getStartedButton, 10);

        getStartedButton.clickAndWaitForNewWindow();

        UiObject welcomeButton =
            getUiObjectByResourceId("com.google.android.apps.photos:id/name",
                                    "android.widget.TextView");
        welcomeButton.clickAndWaitForNewWindow();

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

        // Select third photograph
        selectPhoto(2);

        while (it.hasNext()) {
            Map.Entry<String, GestureTestParams> pair = it.next();
            GestureType type = pair.getValue().gestureType;
            Direction dir = pair.getValue().gestureDirection;
            PinchType pinch = pair.getValue().pinchType;
            int steps = pair.getValue().steps;
            int percent = pair.getValue().percent;

            String runName = String.format(testTag + "_" + pair.getKey());
            String gfxInfologName =  String.format(TAG + "_" + runName + "_gfxInfo.log");
            String surfFlingerlogName =  String.format(runName + "_surfFlinger.log");
            String viewName = new String("com.google.android.apps.photos.home.HomeActivity");

            UiObject view = new UiObject(new UiSelector().enabled(true));

            if (!view.waitForExists(viewTimeout)) {
                throw new UiObjectNotFoundException("Could not find \"photo view\".");
            }

            startDumpsysGfxInfo(parameters);
            startDumpsysSurfaceFlinger(parameters, viewName);

            Timer results = new Timer();

            switch (type) {
                case UIDEVICE_SWIPE:
                    results = uiDeviceSwipeTest(dir, steps);
                    break;
                case UIOBJECT_SWIPE:
                    results = uiObjectSwipeTest(view, dir, steps);
                    break;
                case PINCH:
                    results = uiObjectVertPinchTest(view, pinch, steps, percent);
                    break;
                default:
                    break;
            }

            stopDumpsysSurfaceFlinger(parameters, viewName, surfFlingerlogName);
            stopDumpsysGfxInfo(parameters, gfxInfologName);

            timingResults.put(runName, results);
        }

        UiObject navigateUpButton =
            getUiObjectByDescription("Navigate Up", "android.widget.ImageButton");
        navigateUpButton.click();
    }

    private void editPhotoTest() throws Exception {
        String testTag = "edit_photo";

        Timer result = new Timer();
        result.start();

        // Select first photograph
        selectPhoto(0);
        UiObject editView = getUiObjectByResourceId("com.google.android.apps.photos:id/edit",
                                                    "android.widget.ImageView");
        editView.click();

        UiObject editColor = getUiObjectByText("Colour", "android.widget.RadioButton");
        editColor.click();

        UiObject seekBar = getUiObjectByResourceId("com.google.android.apps.photos:id/cpe_strength_seek_bar",
                                                   "android.widget.SeekBar");
        seekBar.swipeLeft(10);

        UiObject accept = getUiObjectByDescription("Accept", "android.widget.ImageView");
        accept.click();

        UiObject save = getUiObjectByText("SAVE", "android.widget.TextView");
        save.click();

        // Return to application home screen
        getUiDevice().pressBack();

        result.end();
        timingResults.put(testTag, result);
    }

    // Helper to click on an individual photographs based on index in wa-working gallery.
    private void selectPhoto(final int index) throws Exception {
        UiObject cameraHeading = new UiObject(new UiSelector().text("wa-working"));
        cameraHeading.clickAndWaitForNewWindow();

        UiObject photo =
            new UiObject(new UiSelector().resourceId("com.google.android.apps.photos:id/recycler_view")
                                         .childSelector(new UiSelector()
                                         .index(index)));
        photo.click();
    }
}
