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


package com.arm.wlauto.uiauto.reallinpack;

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

@Test
public void runUiAutomation() throws Exception{
        initialize_instrumentation();
        Bundle status = new Bundle();
        status.putString("product", mDevice.getProductName());
        UiSelector selector = new UiSelector();
        // set the maximum number of threads
        String maxThreads = getParams().getString("max_threads");
        UiObject maxThreadNumberField = mDevice.findObject(selector.index(3));
        maxThreadNumberField.clearTextField();
        maxThreadNumberField.setText(maxThreads);
        // start the benchamrk
        UiObject btn_st = mDevice.findObject(selector.text("Run"));
        btn_st.click();
        btn_st.waitUntilGone(500);
        // set timeout for the benchmark
        btn_st.waitForExists(60 * 60 * 1000);
        mInstrumentation.sendStatus(Activity.RESULT_OK, status);
    }

}
