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


package com.arm.wlauto.uiauto.geekbench;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;
import android.view.KeyEvent;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.util.concurrent.TimeUnit;

public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "geekbench";
    public static final int WAIT_TIMEOUT_1SEC = 1000;
    public static final long WAIT_TIMEOUT_5MIN = TimeUnit.SECONDS.toMillis(5 * 60);
    public static final long WAIT_TIMEOUT_10MIN = TimeUnit.SECONDS.toMillis(10 * 60);

    public void runUiAutomation() throws Exception {
        Bundle params = getParams();
        String[] version = params.getString("version").split("\\.");
        int majorVersion = Integer.parseInt(version[0]);
        int minorVersion = Integer.parseInt(version[1]);
        int times = Integer.parseInt(params.getString("times"));

        dismissEula();

        for (int i = 0; i < times; i++) {
            switch (majorVersion) {
                case 2:
                    // In version 2, we scroll through the results WebView to make sure
                    // all results appear on the screen, which causes them to be dumped into
                    // logcat by the Linaro hacks.
                    runBenchmarks();
                    waitForResultsv2();
                    scrollThroughResults();
                    break;
                case 3:
                    runBenchmarks();
                    waitForResultsv3onwards();
                    if (minorVersion < 4) {
                        // Attempting to share the results will generate the .gb3 file with
                        // results that can then be pulled from the device. This is not possible
                        // in verison 2 of Geekbench (Share option was added later).
                        // Sharing is not necessary from 3.4.1 onwards as the .gb3 files are always
                        // created.
                        shareResults();
                    }
                    break;
                case 4:
                    runCpuBenchmarks();
                    waitForResultsv3onwards();
                    break;
                default :
                    throw new RuntimeException("Invalid version of Geekbench requested");
            }

            if (i < (times - 1)) {
                getUiDevice().pressBack();
                getUiDevice().pressBack();  // twice
            }
        }

        Bundle status = new Bundle();
        getAutomationSupport().sendStatus(Activity.RESULT_OK, status);
    }

    public void dismissEula() throws Exception {
        UiObject acceptButton =
            // new UiObject(new UiSelector().textContains("Accept")
            new UiObject(new UiSelector().resourceId("android:id/button1")
                                         .className("android.widget.Button"));
        if (!acceptButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            throw new UiObjectNotFoundException("Could not find Accept button");
        }
        acceptButton.click();
    }

    public void runBenchmarks() throws Exception {
        UiObject runButton =
            new UiObject(new UiSelector().textContains("Run Benchmarks")
                                         .className("android.widget.Button"));
        if (!runButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            throw new UiObjectNotFoundException("Could not find Run button");
        }
        runButton.click();
    }

    public void runCpuBenchmarks() throws Exception {
        // The run button is at the bottom of the view and may be off the screen so swipe to be sure
        uiDeviceSwipe(Direction.DOWN, 50);

        UiObject runButton =
            new UiObject(new UiSelector().resourceId("com.primatelabs.geekbench:id/runCpuBenchmarks")
                                         .className("android.widget.Button"));
        if (!runButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            throw new UiObjectNotFoundException("Could not find Run button");
        }
        runButton.click();
    }

    public void waitForResultsv2() throws Exception {
        UiSelector selector = new UiSelector();
        UiObject resultsWebview = new UiObject(selector.className("android.webkit.WebView"));
        if (!resultsWebview.waitForExists(WAIT_TIMEOUT_5MIN)) {
            throw new UiObjectNotFoundException("Did not see Geekbench results screen.");
        }
    }

    public void waitForResultsv3onwards() throws Exception {
        UiSelector selector = new UiSelector();
        UiObject runningTextView = new UiObject(selector.text("Running Benchmarks...")
                                                        .className("android.widget.TextView"));

        if (!runningTextView.waitForExists(WAIT_TIMEOUT_1SEC)) {
            throw new UiObjectNotFoundException("Did not get to Running Benchmarks... screen.");
        }
        if (!runningTextView.waitUntilGone(WAIT_TIMEOUT_10MIN)) {
            throw new UiObjectNotFoundException("Did not get to Geekbench results screen.");
        }
    }

    public void scrollThroughResults() throws Exception {
        UiSelector selector = new UiSelector();
        getUiDevice().pressKeyCode(KeyEvent.KEYCODE_PAGE_DOWN);
        sleep(1);
        getUiDevice().pressKeyCode(KeyEvent.KEYCODE_PAGE_DOWN);
        sleep(1);
        getUiDevice().pressKeyCode(KeyEvent.KEYCODE_PAGE_DOWN);
        sleep(1);
        getUiDevice().pressKeyCode(KeyEvent.KEYCODE_PAGE_DOWN);
    }

    public void shareResults() throws Exception {
        sleep(2); // transition
        UiSelector selector = new UiSelector();
        getUiDevice().pressMenu();
        UiObject shareButton = new UiObject(selector.text("Share")
                                                    .className("android.widget.TextView"));
        shareButton.waitForExists(WAIT_TIMEOUT_1SEC);
        shareButton.click();
    }
}
