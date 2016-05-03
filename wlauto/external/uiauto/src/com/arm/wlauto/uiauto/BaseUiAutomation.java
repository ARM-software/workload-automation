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

import android.app.Activity;
import android.os.Bundle;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

public class BaseUiAutomation extends UiAutomatorTestCase {

    public long waitTimeout = TimeUnit.SECONDS.toMillis(4);

    public void sleep(int second) {
        super.sleep(second * 1000);
    }

    public boolean takeScreenshot(String name) {
        Bundle params = getParams();
        String png_dir = params.getString("workdir");

        try {
            return getUiDevice().takeScreenshot(new File(png_dir, name + ".png"));
        } catch(NoSuchMethodError e) {
            return true;
        }
    }

    public void waitText(String text) throws UiObjectNotFoundException {
        waitText(text, 600);
    }

    public void waitText(String text, int second) throws UiObjectNotFoundException {
        UiSelector selector = new UiSelector();
        UiObject text_obj = new UiObject(selector.text(text)
                                       .className("android.widget.TextView"));
        waitObject(text_obj, second);
    }

    public void waitObject(UiObject obj) throws UiObjectNotFoundException {
        waitObject(obj, 600);
    }

    public void waitObject(UiObject obj, int second) throws UiObjectNotFoundException {
        if (! obj.waitForExists(second * 1000)){
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
        while ((currentTime - startTime) < timeout){
            sleep(2);  // poll every two seconds

            while((line=reader.readLine())!=null) {
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
            throw new TimeoutException("Timed out waiting for Logcat text \"%s\"".format(searchText));
        }
    }

    public UiObject getUiObjectByResourceId(String resourceId, String className) throws Exception {
        UiObject object = new UiObject(new UiSelector().resourceId(resourceId)
                                                       .className(className));
        if (!object.waitForExists(waitTimeout)) {
           throw new UiObjectNotFoundException(String.format("Could not find \"%s\" \"%s\"",
                                                              resourceId, className));
        };
        return object;
    }

    public UiObject getUiObjectByDescription(String description, String className) throws Exception {
        UiObject object = new UiObject(new UiSelector().descriptionContains(description)
                                                       .className(className));
        if (!object.waitForExists(waitTimeout)) {
            throw new UiObjectNotFoundException(String.format("Could not find \"%s\" \"%s\"",
                                                              description, className));
        };
        return object;
    }

    public UiObject getUiObjectByText(String text, String className) throws Exception {
        UiObject object = new UiObject(new UiSelector().textContains(text)
                                                      .className(className));
        if (!object.waitForExists(waitTimeout)) {
            throw new UiObjectNotFoundException(String.format("Could not find \"%s\" \"%s\"",
                                                              text, className));
        };
        return object;
    }

    public void clickUiObject(UiObject uiobject, long timeout) throws Exception {
        if (!uiobject.clickAndWaitForNewWindow(timeout)) {
            throw new UiObjectNotFoundException(String.format("Timeout waiting for New Window"));
        }
    }

    public int getDisplayHeight () {
        return getUiDevice().getInstance().getDisplayHeight();
    }

    public int getDisplayWidth () {
        return getUiDevice().getInstance().getDisplayWidth();
    }

    public int getDisplayCentreWidth () {
        return getDisplayWidth() / 2;
    }

    public int getDisplayCentreHeight () {
        return getDisplayHeight() / 2;
    }

    public void tapDisplayCentre () {
        tapDisplay(getDisplayCentreWidth(),  getDisplayCentreHeight());
    }

    public void tapDisplay (int x, int y) {
        getUiDevice().getInstance().click(x, y);
    }

    public void uiDeviceSwipeUp (int steps) {
        getUiDevice().getInstance().swipe(
            getDisplayCentreWidth(),
            (getDisplayCentreHeight() / 2),
            getDisplayCentreWidth(),
            (getDisplayCentreHeight() + (getDisplayCentreHeight() / 2)),
            steps);
    }

    public void uiDeviceSwipeDown (int steps) {
        getUiDevice().getInstance().swipe(
            getDisplayCentreWidth(),
            (getDisplayCentreHeight() + (getDisplayCentreHeight() / 2)),
            getDisplayCentreWidth(),
            (getDisplayCentreHeight() / 2),
            steps);
    }

    public void uiDeviceSwipeLeft (int steps) {
        getUiDevice().getInstance().swipe(
            (getDisplayCentreWidth() + (getDisplayCentreWidth() / 2)),
            getDisplayCentreHeight(),
            (getDisplayCentreWidth() / 2),
            getDisplayCentreHeight(),
            steps);
    }

    public void uiDeviceSwipeRight (int steps) {
        getUiDevice().getInstance().swipe(
            (getDisplayCentreWidth() / 2),
            getDisplayCentreHeight(),
            (getDisplayCentreWidth() + (getDisplayCentreWidth() / 2)),
            getDisplayCentreHeight(),
            steps);
    }
}
