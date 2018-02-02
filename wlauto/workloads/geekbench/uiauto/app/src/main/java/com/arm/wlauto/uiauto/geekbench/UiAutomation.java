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
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;
import android.view.KeyEvent;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.concurrent.TimeUnit;

// Import the uiautomator libraries

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "geekbench";
    public static final long WAIT_TIMEOUT_5SEC = TimeUnit.SECONDS.toMillis(5);
    public static final long WAIT_TIMEOUT_20MIN = TimeUnit.SECONDS.toMillis(20 * 60);

@Test
public void runUiAutomation() throws Exception {
        initialize_instrumentation();
        Bundle params = getParams();
        boolean isCorporate = params.getBoolean("is_corporate");
        String packageName = mDevice.getCurrentPackageName();

        if (packageName.equals("com.primatelabs.geekbench4.corporate"))
            isCorporate = true;
        
        if (!isCorporate)
            dismissEula();
            runCpuBenchmarks(isCorporate);
            waitForResultsv3onwards();

        Bundle status = new Bundle();
        mInstrumentation.sendStatus(Activity.RESULT_OK, status);
    }

    public void dismissEula() throws Exception {
        UiObject acceptButton =
           mDevice.findObject(new UiSelector().resourceId("android:id/button1")
                                         .className("android.widget.Button"));
        if (!acceptButton.waitForExists(WAIT_TIMEOUT_5SEC)) {
            throw new UiObjectNotFoundException("Could not find Accept button");
        }
        acceptButton.click();
    }

    public void runCpuBenchmarks(boolean isCorporate) throws Exception {
        // The run button is at the bottom of the view and may be off the screen so swipe to be sure
        uiDeviceSwipe(Direction.DOWN, 50);

        String packageName = isCorporate ? "com.primatelabs.geekbench4.corporate"
                                         : "com.primatelabs.geekbench";
        UiObject runButton =
           mDevice.findObject(new UiSelector().resourceId(packageName + ":id/runCpuBenchmarks")
                                         .className("android.widget.Button"));
        if (!runButton.waitForExists(WAIT_TIMEOUT_5SEC)) {
            throw new UiObjectNotFoundException("Could not find Run button");
        }
        runButton.click();
    }

    public void waitForResultsv3onwards() throws Exception {
        UiSelector selector = new UiSelector();
        UiObject runningTextView = mDevice.findObject(selector.textContains("Running")
                                                        .className("android.widget.TextView"));

        if (!runningTextView.waitUntilGone(WAIT_TIMEOUT_20MIN)) {
            throw new UiObjectNotFoundException("Did not get to Geekbench results screen.");
        }
    }
}
