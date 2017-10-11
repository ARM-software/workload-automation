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


package com.arm.wlauto.uiauto.androbench;

import android.app.Activity;
import android.os.Bundle;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiSelector;

import com.arm.wlauto.uiauto.BaseUiAutomation;

import org.junit.Test;
import org.junit.runner.RunWith;

// Import the uiautomator libraries

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends BaseUiAutomation {

    public static String TAG = "androbench";

@Test
public void runUiAutomation() throws Exception {
        initialize_instrumentation();
        Bundle status = new Bundle();
        status.putString("product", mDevice.getProductName());
        UiSelector selector = new UiSelector();
        sleep(3);
        UiObject btn_microbench = mDevice.findObject(selector.textContains("Micro")
                                                     .className("android.widget.Button"));
        if (btn_microbench.exists()) {
            btn_microbench.click();
        } else {
            UiObject bench =
                mDevice.findObject(new UiSelector().resourceIdMatches("com.andromeda.androbench2:id/btnStartingBenchmarking"));
                bench.click();
        }        

        UiObject btn_yes= mDevice.findObject(selector.textContains("Yes")
                                                     .className("android.widget.Button"));
        btn_yes.click();

        try {
            UiObject complete_text = mDevice.findObject(selector.text("Cancel")
                                                        .className("android.widget.Button"));

            waitObject(complete_text);

            sleep(2);
            complete_text.click();
        } finally {
            //complete_text.click();
        }

        sleep(5);
        takeScreenshot("Androbench");
        mInstrumentation.sendStatus(Activity.RESULT_OK, status);
    }
}
