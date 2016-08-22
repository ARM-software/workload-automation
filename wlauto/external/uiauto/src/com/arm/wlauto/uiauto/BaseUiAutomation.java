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


package com.arm.wlauto.uiauto;

import java.io.File;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.TimeUnit;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import android.app.Activity;
import android.os.Bundle;
import android.os.SystemClock;
import android.graphics.Point;
import android.graphics.Rect;
import android.util.Log;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.core.UiDevice;
import com.android.uiautomator.core.UiWatcher;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

public class BaseUiAutomation extends UiAutomatorTestCase {

    public long uiAutoTimeout = TimeUnit.SECONDS.toMillis(4);

    public enum ScreenOrientation { RIGHT, NATURAL, LEFT };
    public enum Direction { UP, DOWN, LEFT, RIGHT, NULL };
    public enum PinchType { IN, OUT, NULL };

    public static final int CLICK_REPEAT_INTERVAL_MINIMUM = 5;
    public static final int CLICK_REPEAT_INTERVAL_DEFAULT = 50;

    /*
     * Used by clickUiObject() methods in order to provide a consistent API
     */
    public enum FindByCriteria { BY_ID, BY_TEXT, BY_DESC; }

    /**
     * Basic marker API for workloads to generate start and end markers for
     * deliminating and timing actions. Markers are output to logcat with debug
     * priority. Actions represent a series of UI interactions to time.
     *
     * The marker API provides a way for instruments and result processors to hook into
     * per-action timings by parsing logcat logs produced per workload iteration.
     *
     * The marker output consists of a logcat tag 'UX_PERF' and a message. The
     * message consists of a name for the action and a timestamp. The timestamp
     * is separated by a single space from the name of the action.
     *
     * Typical usage:
     *
     * ActionLogger logger = ActionLogger("testTag", parameters);
     * logger.start();
     * // actions to be recorded
     * logger.stop();
     */
    public class ActionLogger {

        private String testTag;
        private boolean enabled;

        public ActionLogger(String testTag, Bundle parameters) {
            this.testTag = testTag;
            this.enabled = Boolean.parseBoolean(parameters.getString("markers_enabled"));
        }

        public void start() {
            if (enabled) {
                Log.d("UX_PERF", testTag + "_start " + System.nanoTime());
            }
        }

        public void stop() throws Exception {
            if (enabled) {
                Log.d("UX_PERF", testTag + "_end " + System.nanoTime());
            }
        }
    }

    public void sleep(int second) {
        super.sleep(second * 1000);
    }

    public boolean takeScreenshot(String name) {
        Bundle params = getParams();
        String pngDir = params.getString("workdir");

        try {
            return getUiDevice().takeScreenshot(new File(pngDir, name + ".png"));
        } catch (NoSuchMethodError e) {
            return true;
        }
    }

    public void waitResourceId(String text, String className) throws UiObjectNotFoundException {
        waitResourceId(text, 600, className);
    }

    public void waitResourceId(String text, int second, String className) throws UiObjectNotFoundException {
        UiSelector selector = new UiSelector();
        UiObject resourceObj = new UiObject(selector.resourceId(text)
                                       .className(className));
        waitObject(resourceObj, second);
    }

    public void waitText(String text) throws UiObjectNotFoundException {
        waitText(text, 600);
    }

    public void waitText(String text, int second) throws UiObjectNotFoundException {
        UiSelector selector = new UiSelector();
        UiObject textObj = new UiObject(selector.text(text)
                                       .className("android.widget.TextView"));
        waitObject(textObj, second);
    }

    public void waitObject(UiObject obj) throws UiObjectNotFoundException {
        waitObject(obj, 600);
    }

    public void waitObject(UiObject obj, int second) throws UiObjectNotFoundException {
        if (!obj.waitForExists(second * 1000)) {
            throw new UiObjectNotFoundException("UiObject is not found: "
                    + obj.getSelector().toString());
        }
    }

    public boolean waitUntilNoObject(UiObject obj, int second) {
        return obj.waitUntilGone(second * 1000);
    }

    public void clearLogcat() throws Exception {
        Runtime.getRuntime().exec("logcat -c");
    }

    public void waitForLogcatText(String searchText, long timeout) throws Exception {
        long startTime = System.currentTimeMillis();
        Process process = Runtime.getRuntime().exec("logcat");
        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        String line;

        long currentTime = System.currentTimeMillis();
        boolean found = false;
        while ((currentTime - startTime) < timeout) {
            sleep(2);  // poll every two seconds

            while ((line = reader.readLine()) != null) {
                if (line.contains(searchText)) {
                    found = true;
                    break;
                }
            }

            if (found) {
                break;
            }
            currentTime = System.currentTimeMillis();
        }

        process.destroy();

        if ((currentTime - startTime) >= timeout) {
            throw new TimeoutException(String.format("Timed out waiting for Logcat text \"%s\"",
                                                     searchText));
        }
    }

    public Integer[] splitVersion(String versionString) {
        String pattern = "(\\d+).(\\d+).(\\d+)";
        Pattern r = Pattern.compile(pattern);
        ArrayList<Integer> result = new ArrayList<Integer>();

        Matcher m = r.matcher(versionString);
        if (m.find() && m.groupCount() > 0) {
            for(int i=1; i<=m.groupCount(); i++) {
                result.add(Integer.parseInt(m.group(i)));
            }
        } else {
            throw new IllegalArgumentException(versionString + " - unknown format");
        }
        return result.toArray(new Integer[result.size()]);
    }

    //Return values:
    // -1 = a lower than b
    //  0 = a and b equal
    //  1 = a greater than b
    public int compareVersions(Integer[] a, Integer[] b) {
        if (a.length != b.length) {
            String msg = "Versions do not match format:\n %1$s\n %1$s";
            msg = String.format(msg, Arrays.toString(a), Arrays.toString(b));
            throw new IllegalArgumentException(msg);
        }
        for(int i=0; i<a.length; i++) {
            if(a[i] > b[i])
                return 1;
            else if(a[i] < b[i])
                return -1;
        }
        return 0;
    }

    public void registerWatcher(String name, UiWatcher watcher) {
        UiDevice.getInstance().registerWatcher(name, watcher);
    }

    public void runWatchers() {
        UiDevice.getInstance().runWatchers();
    }

    public void removeWatcher(String name) {
        UiDevice.getInstance().removeWatcher(name);
    }

    public void pressEnter() {
        UiDevice.getInstance().pressEnter();
    }

    public void pressBack() {
        UiDevice.getInstance().pressBack();
    }

    public void pressDPadUp() {
        UiDevice.getInstance().pressDPadUp();
    }

    public void pressDPadDown() {
        UiDevice.getInstance().pressDPadDown();
    }

    public void pressDPadLeft() {
        UiDevice.getInstance().pressDPadLeft();
    }

    public void pressDPadRight() {
        UiDevice.getInstance().pressDPadRight();
    }

    public int getDisplayHeight() {
        return UiDevice.getInstance().getDisplayHeight();
    }

    public int getDisplayWidth() {
        return UiDevice.getInstance().getDisplayWidth();
    }

    public int getDisplayCentreWidth() {
        return getDisplayWidth() / 2;
    }

    public int getDisplayCentreHeight() {
        return getDisplayHeight() / 2;
    }

    public void tapDisplayCentre() {
        tapDisplay(getDisplayCentreWidth(),  getDisplayCentreHeight());
    }

    public void tapDisplay(int x, int y) {
        UiDevice.getInstance().click(x, y);
    }

    public void uiDeviceSwipeUp(int steps) {
        UiDevice.getInstance().swipe(
            getDisplayCentreWidth(),
            (getDisplayCentreHeight() / 2),
            getDisplayCentreWidth(),
            (getDisplayCentreHeight() + (getDisplayCentreHeight() / 2)),
            steps);
    }

    public void uiDeviceSwipeDown(int steps) {
        UiDevice.getInstance().swipe(
            getDisplayCentreWidth(),
            (getDisplayCentreHeight() + (getDisplayCentreHeight() / 2)),
            getDisplayCentreWidth(),
            (getDisplayCentreHeight() / 2),
            steps);
    }

    public void uiDeviceSwipeLeft(int steps) {
        UiDevice.getInstance().swipe(
            (getDisplayCentreWidth() + (getDisplayCentreWidth() / 2)),
            getDisplayCentreHeight(),
            (getDisplayCentreWidth() / 2),
            getDisplayCentreHeight(),
            steps);
    }

    public void uiDeviceSwipeRight(int steps) {
        UiDevice.getInstance().swipe(
            (getDisplayCentreWidth() / 2),
            getDisplayCentreHeight(),
            (getDisplayCentreWidth() + (getDisplayCentreWidth() / 2)),
            getDisplayCentreHeight(),
            steps);
    }

    public void uiDeviceSwipe(Direction direction, int steps) throws Exception {
        switch (direction) {
            case UP:
                uiDeviceSwipeUp(steps);
                break;
            case DOWN:
                uiDeviceSwipeDown(steps);
                break;
            case LEFT:
                uiDeviceSwipeLeft(steps);
                break;
            case RIGHT:
                uiDeviceSwipeRight(steps);
                break;
            case NULL:
                throw new Exception("No direction specified");
            default:
                break;
        }
    }

    public void uiObjectSwipe(UiObject view, Direction direction, int steps) throws Exception {
        switch (direction) {
            case UP:
                view.swipeUp(steps);
                break;
            case DOWN:
                view.swipeDown(steps);
                break;
            case LEFT:
                view.swipeLeft(steps);
                break;
            case RIGHT:
                view.swipeRight(steps);
                break;
            case NULL:
                throw new Exception("No direction specified");
            default:
                break;
        }
    }

    public void uiObjectVertPinchIn(UiObject view, int steps, int percent) throws Exception {
        final int FINGER_TOUCH_HALF_WIDTH = 20;

        // Make value between 1 and 100
        int nPercent = (percent < 0) ? 1 : (percent > 100) ? 100 : percent;
        float percentage = nPercent / 100f;

        Rect rect = view.getVisibleBounds();

        if (rect.width() <= FINGER_TOUCH_HALF_WIDTH * 2) {
            throw new IllegalStateException("Object width is too small for operation");
        }

        // Start at the top-center and bottom-center of the control
        Point startPoint1 = new Point(rect.centerX(), rect.centerY()
                          + (int) ((rect.height() / 2) * percentage));
        Point startPoint2 = new Point(rect.centerX(), rect.centerY()
                          - (int) ((rect.height() / 2) * percentage));

        // End at the same point at the center of the control
        Point endPoint1 = new Point(rect.centerX(), rect.centerY() + FINGER_TOUCH_HALF_WIDTH);
        Point endPoint2 = new Point(rect.centerX(), rect.centerY() - FINGER_TOUCH_HALF_WIDTH);

        view.performTwoPointerGesture(startPoint1, startPoint2, endPoint1, endPoint2, steps);
    }

    public void uiObjectVertPinchOut(UiObject view, int steps, int percent) throws Exception {
        final int FINGER_TOUCH_HALF_WIDTH = 20;

        // Make value between 1 and 100
        int nPercent = (percent < 0) ? 1 : (percent > 100) ? 100 : percent;
        float percentage = nPercent / 100f;

        Rect rect = view.getVisibleBounds();

        if (rect.width() <= FINGER_TOUCH_HALF_WIDTH * 2) {
            throw new IllegalStateException("Object width is too small for operation");
        }

        // Start from the same point at the center of the control
        Point startPoint1 = new Point(rect.centerX(), rect.centerY() + FINGER_TOUCH_HALF_WIDTH);
        Point startPoint2 = new Point(rect.centerX(), rect.centerY() - FINGER_TOUCH_HALF_WIDTH);

        // End at the top-center and bottom-center of the control
        Point endPoint1 = new Point(rect.centerX(), rect.centerY()
                        + (int) ((rect.height() / 2) * percentage));
        Point endPoint2 = new Point(rect.centerX(), rect.centerY()
                        - (int) ((rect.height() / 2) * percentage));

        view.performTwoPointerGesture(startPoint1, startPoint2, endPoint1, endPoint2, steps);
    }

    public void setScreenOrientation(ScreenOrientation orientation) throws Exception {
        switch (orientation) {
            case RIGHT:
                getUiDevice().setOrientationRight();
                break;
            case NATURAL:
                getUiDevice().setOrientationNatural();
                break;
            case LEFT:
                getUiDevice().setOrientationLeft();
                break;
            default:
                throw new Exception("No orientation specified");
        }
    }

    public void unsetScreenOrientation() throws Exception {
        getUiDevice().unfreezeRotation();
    }

   public void uiObjectPerformLongClick(UiObject view, int steps) throws Exception {
        Rect rect = view.getBounds();
        UiDevice.getInstance().swipe(rect.centerX(), rect.centerY(),
                                     rect.centerX(), rect.centerY(), steps);
    }

    public void uiDeviceSwipeVertical(int startY, int endY, int xCoordinate, int steps) {
        getUiDevice().swipe(startY, xCoordinate, endY, xCoordinate, steps);
    }

    public void uiDeviceSwipeHorizontal(int startX, int endX, int yCoordinate, int steps) {
        getUiDevice().swipe(startX, yCoordinate, endX, yCoordinate, steps);
    }

    public void uiObjectPinch(UiObject view, PinchType direction, int steps,
                                  int percent) throws Exception {
        if (direction.equals(PinchType.IN)) {
            view.pinchIn(percent, steps);
        } else if (direction.equals(PinchType.OUT)) {
            view.pinchOut(percent, steps);
        }
    }

    public void uiObjectVertPinch(UiObject view, PinchType direction,
                                       int steps, int percent) throws Exception {
        if (direction.equals(PinchType.IN)) {
            uiObjectVertPinchIn(view, steps, percent);
        } else if (direction.equals(PinchType.OUT)) {
            uiObjectVertPinchOut(view, steps, percent);
        }
    }

    public void repeatClickUiObject(UiObject view, int repeatCount, int intervalInMillis) throws Exception {
        int repeatInterval = intervalInMillis > CLICK_REPEAT_INTERVAL_MINIMUM
                           ? intervalInMillis : CLICK_REPEAT_INTERVAL_DEFAULT;
        if (repeatCount < 1 || !view.isClickable()) {
            return;
        }

        for (int i = 0; i < repeatCount; ++i) {
            view.click();
            SystemClock.sleep(repeatInterval); // in order to register as separate click
        }
    }

    public UiObject clickUiObject(FindByCriteria criteria, String matching) throws Exception {
        return clickUiObject(criteria, matching, null, false);
    }

    public UiObject clickUiObject(FindByCriteria criteria, String matching, boolean wait) throws Exception {
        return clickUiObject(criteria, matching, null, wait);
    }

    public UiObject clickUiObject(FindByCriteria criteria, String matching, String clazz) throws Exception {
        return clickUiObject(criteria, matching, clazz, false);
    }

    public UiObject clickUiObject(FindByCriteria criteria, String matching, String clazz, boolean wait) throws Exception {
        UiObject view;

        switch (criteria) {
            case BY_ID:
                view = (clazz == null)
                     ? getUiObjectByResourceId(matching) : getUiObjectByResourceId(matching, clazz);
                break;
            case BY_DESC:
                view = (clazz == null)
                     ? getUiObjectByDescription(matching) : getUiObjectByDescription(matching, clazz);
                break;
            case BY_TEXT:
            default:
                view = (clazz == null)
                     ? getUiObjectByText(matching) : getUiObjectByText(matching, clazz);
                break;
        }

        if (wait) {
            view.clickAndWaitForNewWindow();
        } else {
            view.click();
        }
        return view;
    }

    public UiObject getUiObjectByResourceId(String resourceId, String className) throws Exception {
        return getUiObjectByResourceId(resourceId, className, uiAutoTimeout);
    }

    public UiObject getUiObjectByResourceId(String resourceId, String className, long timeout) throws Exception {
        UiObject object = new UiObject(new UiSelector().resourceId(resourceId)
                                                       .className(className));
        if (!object.waitForExists(timeout)) {
           throw new UiObjectNotFoundException(String.format("Could not find \"%s\" \"%s\"",
                                                              resourceId, className));
        }
        return object;
    }

    public UiObject getUiObjectByResourceId(String id) throws Exception {
        UiObject object = new UiObject(new UiSelector().resourceId(id));

        if (!object.waitForExists(uiAutoTimeout)) {
           throw new UiObjectNotFoundException("Could not find view with resource ID: " + id);
        }
        return object;
    }

    public UiObject getUiObjectByDescription(String description, String className) throws Exception {
        return getUiObjectByDescription(description, className, uiAutoTimeout);
    }

    public UiObject getUiObjectByDescription(String description, String className, long timeout) throws Exception {
        UiObject object = new UiObject(new UiSelector().descriptionContains(description)
                                                       .className(className));
        if (!object.waitForExists(timeout)) {
            throw new UiObjectNotFoundException(String.format("Could not find \"%s\" \"%s\"",
                                                              description, className));
        }
        return object;
    }

    public UiObject getUiObjectByDescription(String desc) throws Exception {
        UiObject object = new UiObject(new UiSelector().descriptionContains(desc));

        if (!object.waitForExists(uiAutoTimeout)) {
           throw new UiObjectNotFoundException("Could not find view with description: " + desc);
        }
        return object;
    }

    public UiObject getUiObjectByText(String text, String className) throws Exception {
        return getUiObjectByText(text, className, uiAutoTimeout);
    }

    public UiObject getUiObjectByText(String text, String className, long timeout) throws Exception {
        UiObject object = new UiObject(new UiSelector().textContains(text)
                                                       .className(className));
        if (!object.waitForExists(timeout)) {
            throw new UiObjectNotFoundException(String.format("Could not find \"%s\" \"%s\"",
                                                              text, className));
        }
        return object;
    }

    public UiObject getUiObjectByText(String text) throws Exception {
        UiObject object = new UiObject(new UiSelector().textContains(text));

        if (!object.waitForExists(uiAutoTimeout)) {
           throw new UiObjectNotFoundException("Could not find view with text: " + text);
        }
        return object;
    }
}
