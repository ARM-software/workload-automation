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


package com.arm.wlauto.uiauto.cfbench;

import android.app.Activity;
import android.os.Bundle;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;

import com.arm.wlauto.uiauto.BaseUiAutomation;

import org.junit.Test;
import org.junit.runner.RunWith;

// Import the uiautomator libraries

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends BaseUiAutomation {

    public static String TAG = "cfbench";

@Test
public void runUiAutomation() throws Exception{
        initialize_instrumentation();
        Bundle status = new Bundle();
        status.putString("product", mDevice.getProductName());
        UiSelector selector = new UiSelector();
        UiObject text_bench = mDevice.findObject(selector.text("Full Benchmark")
                                                   .className("android.widget.TextView"));

        text_bench.click();
        sleep(2);

        try {
            UiObject stop_text = mDevice.findObject(selector.textContains("Benchmarking ...")
                                                      .className("android.widget.TextView"));
            waitUntilNoObject(stop_text, 600);

            sleep(2);
        } finally {
            takeScreenshot("cf-bench");
        }

        UiScrollable res = new UiScrollable(new UiSelector());//.scrollable(true));
        res.flingToEnd(10);
        sleep(2);

        mInstrumentation.sendStatus(Activity.RESULT_OK, status);
    }

}
