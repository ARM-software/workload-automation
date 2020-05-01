/*    Copyright 2014-2018 ARM Limited
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

package com.arm.wa.uiauto.jetstream;

import android.os.Bundle;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiSelector;
import android.support.test.uiautomator.UiScrollable;

import com.arm.wa.uiauto.BaseUiAutomation;
import android.util.Log;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.concurrent.TimeUnit;

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends BaseUiAutomation {

    private int networkTimeoutSecs = 30;
    private long networkTimeout =  TimeUnit.SECONDS.toMillis(networkTimeoutSecs);
    public static String TAG = "UXPERF";

    @Before
    public void initialize(){
        initialize_instrumentation();
    }

    @Test
    public void setup() throws Exception{
        setScreenOrientation(ScreenOrientation.NATURAL);
        dismissChromePopup();
        openJetstream();
    }

    @Test
    public void runWorkload() throws Exception {
        runBenchmark();
    }

    @Test
    public void teardown() throws Exception{
        clearChromeTabs();
        unsetScreenOrientation();
    }

    public void runBenchmark() throws Exception {
        UiObject start =
            mDevice.findObject(new UiSelector().description("Start Test"));
            
        UiObject starttext =
            mDevice.findObject(new UiSelector().text("Start Test"));
        
        // Run Jetstream test
        if (start.waitForExists(20000)) {
            start.click();
        } else {
            starttext.click();
        }
     
        UiObject scores =
            mDevice.findObject(new UiSelector().resourceId("result-summary"));
        scores.waitForExists(2100000);
    }

    public void openJetstream() throws Exception {
        UiObject urlBar =
            mDevice.findObject(new UiSelector().resourceId("com.android.chrome:id/url_bar"));
         
        UiObject searchBox =  mDevice.findObject(new UiSelector().resourceId("com.android.chrome:id/search_box_text"));
        
        if (!urlBar.waitForExists(5000)) {
                searchBox.click();
        }

        String url = "http://browserbench.org/JetStream/";

        // Clicking search box turns it into url bar on some deivces
        if(urlBar.waitForExists(2000)) {
            urlBar.click();
            sleep(2);
            urlBar.setText(url);
        } else {
            searchBox.setText(url);
        }
        pressEnter();
    }
}
