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


package com.arm.wlauto.uiauto.peacekeeper;

import android.os.Bundle;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiSelector;

import com.arm.wlauto.uiauto.BaseUiAutomation;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.PrintWriter;

// Import the uiautomator libraries

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends BaseUiAutomation {

    public static String TAG = "peacekeeper";

@Test
public void runUiAutomation() throws Exception {
        // maximum time for running peacekeeper benchmark 80 * 10 sec
        final int TIMEOUT = 80;

        // reading the input parameter
        initialize_instrumentation();
        Bundle parameters = getParams();
        String browser = parameters.getString("browser");
        String outputFile = parameters.getString("output_file");
        String peacekeeperUrl = parameters.getString("peacekeeper_url");

        String urlAddress = "";

        PrintWriter writer = new PrintWriter(outputFile, "UTF-8");

        // firefox browser uiautomator code
        if (browser.equals("firefox")) {

            UiObject addressBar = mDevice.findObject(new UiSelector()
                                  .className("android.widget.TextView")
                                  .text("Enter Search or Address"));
            if (!addressBar.exists()) {
                addressBar = mDevice.findObject(new UiSelector()
                             .resourceIdMatches(".*/url_bar_title"));
            }
            addressBar.click();
            UiObject setUrl = mDevice.findObject(new UiSelector()
                              .className("android.widget.EditText"));
            setUrl.clearTextField();
            setUrl.setText(peacekeeperUrl);
            mDevice.pressEnter();

            // Allow time for UI to update
            sleep(1);


            UiObject currentUrl = mDevice.findObject(new UiSelector()
                               .className("android.widget.TextView").index(1));

            if (!currentUrl.getText().contains("run.action")) {
                currentUrl = addressBar;
            }
            for (int i = 0; i < TIMEOUT; i++) {

                if (!currentUrl.getText().contains("run.action")) {

                    // write url address to peacekeeper.txt file
                    currentUrl.click();
                    if (!setUrl.exists()){
                        setUrl = addressBar;
                    }
                    urlAddress = setUrl.getText();
                    writer.println(urlAddress);
                    break;
                }
            sleep(10);
            }
        } else if (browser.equals("chrome")) { // Code for Chrome browser

            //Check for welcome screen and dismiss if present.
            UiObject acceptTerms = mDevice.findObject(new UiSelector()
                                   .className("android.widget.Button")
                                   .textContains("Accept & continue"));
            if (acceptTerms.exists()){
                acceptTerms.click();
                UiObject dismiss = mDevice.findObject(new UiSelector()
                                   .className("android.widget.Button")
                                   .resourceIdMatches(".*/negative_button"));
                if (dismiss.exists()){
                    dismiss.clickAndWaitForNewWindow();
                }
            }

            UiObject addressBar = mDevice.findObject(new UiSelector()
                                  .className("android.widget.EditText")
                                  .descriptionMatches("Search or type url"));
            if (!addressBar.exists()){
                addressBar = mDevice.findObject(new UiSelector()
                        .className("android.widget.EditText")
                        .text("Search or type URL"));
            }

            addressBar.click();
            addressBar.clearTextField();
            addressBar.setText(peacekeeperUrl);
            mDevice.pressEnter();

            // Allow time for UI to update
            sleep(5);

            if (!addressBar.exists()){
                addressBar = mDevice.findObject(new UiSelector()
                             .resourceIdMatches(".*/url_bar"));
            }
            for (int i = 0; i < TIMEOUT; i++) {

                if (!addressBar.getText().contains("run.action")) {

                    // write url address to peacekeeper.txt file
                    urlAddress = addressBar.getText();
                    if (!urlAddress.contains("http"))
                    urlAddress = "http://" + urlAddress;
                    writer.println(urlAddress);
                    break;
                }
            sleep(10);
            }
        }
        writer.close();
        mDevice.pressHome();
    }
}
