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
import java.util.Arrays;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

public class BaseUiAutomation extends UiAutomatorTestCase {   

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
            this.enabled = Boolean.parseBoolean(parameters.getString("dumpsys_enabled"));
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
}

