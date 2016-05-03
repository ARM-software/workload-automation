package com.arm.wlauto.uiauto.googlephotos;

import android.os.Bundle;
import android.graphics.Point;
import android.graphics.Rect;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.io.File;
import java.io.FileWriter;
import java.io.BufferedWriter;
import java.util.concurrent.TimeUnit;
import java.util.LinkedHashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Map.Entry;

public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "uxperf_googlephotos";

    public Bundle parameters;
    private long viewTimeout =  TimeUnit.SECONDS.toMillis(20);
    private LinkedHashMap<String, Timer> timingResults = new LinkedHashMap<String, Timer>();

    public void runUiAutomation() throws Exception {
        Timer result = new Timer();
        result.start();
        parameters = getParams();

        dismissWelcomeView();
        gesturesTest();
        editPhotoTest();

        result.end();
        timingResults.put("total", result);

        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    private void dismissWelcomeView() throws Exception {
        // Click through the first two pages and make sure that we don't sign
        // in to our google account. This ensures the same set of photographs
        // are placed in the camera directory for each run.

        sleep(3); // Pause while splash screen loads

        UiObject getStarteddButton =
            getUiObjectByResourceId("com.google.android.apps.photos:id/get_started",
                                    "android.widget.Button");
        getStarteddButton.clickAndWaitForNewWindow();

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
    }

    private void gesturesTest () throws Exception {
        String testTag = "gestures";

        // Perform a range of swipe tests while browsing photo gallery
        LinkedHashMap<String, GestureTestParams> testParams = new LinkedHashMap<String, GestureTestParams>();
        testParams.put("swipe_left", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.LEFT, 10));
        testParams.put("pinch_out", new GestureTestParams(GestureType.PINCH, PinchType.OUT, 100, 50));
        testParams.put("pinch_in", new GestureTestParams(GestureType.PINCH, PinchType.IN, 100, 50));
        testParams.put("swipe_right", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.RIGHT, 10));
        testParams.put("swipe_up", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.UP, 10));

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
            };

            startDumpsysGfxInfo();
            startDumpsysSurfaceFlinger(viewName);

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

            stopDumpsysSurfaceFlinger(viewName, surfFlingerlogName);
            stopDumpsysGfxInfo(gfxInfologName);

            timingResults.put(runName, results);
        }
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

    // Helper to click on an individual photographs based on index in Camera gallery.
    private void selectPhoto(int index) throws Exception {
        UiObject cameraHeading = new UiObject(new UiSelector().text("Camera"));
        cameraHeading.clickAndWaitForNewWindow();

        UiObject photo =
            new UiObject(new UiSelector().resourceId("com.google.android.apps.photos:id/recycler_view")
                                         .childSelector(new UiSelector()
                                         .index(index)));
        photo.click();
    }

    // Helper for testing zoom facility. NOTE: the built in UiObject methods
    // pinchIn() and pinchOut() do not zoom appropriately for this application.
    private Timer uiObjectVertPinchTest(
            UiObject view, PinchType direction,
            int steps, int percent) throws Exception {

        Timer results = new Timer();
        results.start();

        final int FINGER_TOUCH_HALF_WIDTH = 20;

        // make value between 1 and 100
        percent = (percent < 0) ? 1 : (percent > 100) ? 100 : percent;
        float percentage = percent / 100f;

        Rect rect = view.getVisibleBounds();
        if (rect.width() <= FINGER_TOUCH_HALF_WIDTH * 2)
            throw new IllegalStateException("Object width is too small for operation");

        // start from the same point at the center of the control
        Point startPoint1 = new Point(rect.centerX(), rect.centerY() + FINGER_TOUCH_HALF_WIDTH);
        Point startPoint2 = new Point(rect.centerX(), rect.centerY() - FINGER_TOUCH_HALF_WIDTH);

        // End at the top-center and bottom-center of the control
        Point endPoint1 = new Point(rect.centerX(), rect.centerY() + (int) ((rect.height() / 2) * percentage));
        Point endPoint2 = new Point(rect.centerX(), rect.centerY() - (int) ((rect.height() / 2) * percentage));

        if (direction.equals(PinchType.IN)) {
            view.performTwoPointerGesture(endPoint1, endPoint2, startPoint1, startPoint2, steps);
        } else if (direction.equals(PinchType.OUT)) {
            view.performTwoPointerGesture(startPoint1, startPoint2, endPoint1, endPoint2, steps);
        }

        results.end();

        return results;
    }

    private class GestureTestParams {
        GestureType gestureType;
        Direction gestureDirection;
        PinchType pinchType;
        private int percent;
        private int steps;

        GestureTestParams(GestureType gesture, Direction direction, int steps) {
            this.gestureType = gesture;
            this.gestureDirection = direction;
            this.pinchType = PinchType.NULL;
            this.steps = steps;
            this.percent = 0;
        }

        GestureTestParams(GestureType gesture, PinchType pinchType, int steps, int percent) {
            this.gestureType = gesture;
            this.gestureDirection = Direction.NULL;
            this.pinchType = pinchType;
            this.steps = steps;
            this.percent = percent;
        }
    }

    private void writeResultsToFile(LinkedHashMap timingResults, String file) throws Exception {
        // Write out the key/value pairs to the instrumentation log file
        FileWriter fstream = new FileWriter(file);
        BufferedWriter out = new BufferedWriter(fstream);
        Iterator<Entry<String, Timer>> it = timingResults.entrySet().iterator();

        while (it.hasNext()) {
            Map.Entry<String, Timer> pairs = it.next();
            Timer results = pairs.getValue();
            long start = results.getStart();
            long finish = results.getFinish();
            long duration = results.getDuration();
            out.write(String.format(pairs .getKey() + " " + start + " " + finish + " " + duration + "\n"));
        }
        out.close();
    }

    private void startDumpsysSurfaceFlinger(String view) {
        if (Boolean.parseBoolean(parameters.getString("dumpsys_enabled"))) {
            initDumpsysSurfaceFlinger(parameters.getString("package"), view);
        }
    }

    private void stopDumpsysSurfaceFlinger(String view, String filename) throws Exception {
        if (Boolean.parseBoolean(parameters.getString("dumpsys_enabled"))) {
            File out_file = new File(parameters.getString("output_dir"), filename);
            exitDumpsysSurfaceFlinger(parameters.getString("package"), view, out_file);
          }
    }

    private void startDumpsysGfxInfo() {
        if (Boolean.parseBoolean(parameters.getString("dumpsys_enabled"))) {
            initDumpsysGfxInfo(parameters.getString("package"));
          }
    }

    private void stopDumpsysGfxInfo(String filename) throws Exception {
      if (Boolean.parseBoolean(parameters.getString("dumpsys_enabled"))) {
            File out_file = new File(parameters.getString("output_dir"), filename);
            exitDumpsysGfxInfo(parameters.getString("package"), out_file);
          }
    }
}
