/*    Copyright 2016 Linaro Limited
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


package org.linaro.wlauto.uiauto.octane2;

import android.app.Activity;
import android.os.Bundle;
import android.util.Log;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.BaseUiAutomation;

public class UiAutomation extends BaseUiAutomation {

    public static String TAG = "octane2";
    public String[] categories = {
        "Result-Richards",
        "Result-DeltaBlue",
        "Result-RayTrace",
        "Result-RegExp",
        "Result-NavierStokes",
        "Result-Crypto",
        "Result-Splay",
        "Result-SplayLatency",
        "Result-EarleyBoyer",
        "Result-PdfJS",
        "Result-Mandreel",
        "Result-MandreelLatency",
        "Result-Gameboy",
        "Result-CodeLoad",
        "Result-Box2D",
        "Result-zlib",
        "Result-Typescript"
    };

    public void runUiAutomation() throws Exception {
        final int timeout = 10;
        Bundle status = new Bundle();
        status.putString("product", getUiDevice().getProductName());

        sleep(timeout);
        UiSelector selector = new UiSelector();
        /* Accept terms of service */
        try {
            UiObject acceptButton = new UiObject(selector.text("Accept & continue")
                .className("android.widget.Button"));
            acceptButton.click();
        } catch(UiObjectNotFoundException e) {
            /* Do nothing. Apparently dialog wasn't there */
        }
        /* Don't set up account */
        try {
            UiObject acceptButton = new UiObject(selector.textMatches("(?i:No.?\\sThanks)")
                .className("android.widget.Button"));
            acceptButton.click();
        } catch(UiObjectNotFoundException e) {
            /* Do nothing. Apparently dialog wasn't there */
            Log.v(TAG, ">No, Thanks< button not found");
        }
        /* Click Next on Chromium setup dialog */
        try {
            UiObject acceptButton = new UiObject(selector.text("Next")
                .className("android.widget.Button"));
            acceptButton.click();
        } catch(UiObjectNotFoundException e) {
            /* Do nothing. Apparently dialog wasn't there */
            Log.v(TAG, ">Next< button not found");
        }

        /* wait for browser to load index */
        sleep(timeout);
        UiObject runButton = new UiObject(selector.descriptionStartsWith("Start Octane 2.0")
            .className("android.view.View"));
        runButton.click();

        waitResourceId("bottom-text", "android.view.View");
        extractDetailedScores();

        getAutomationSupport().sendStatus(Activity.RESULT_OK, status);
    }

    public void extractDetailedScores() throws Exception {
        UiSelector selector = new UiSelector();
        for (String benchmarkName : categories) {
          UiObject benchmarkObject = new UiObject(selector.resourceId(benchmarkName));
          String detailedScore = benchmarkObject.getContentDescription();
          Log.v(TAG,"OCTANE2 RESULT: " + benchmarkName.split("-")[1] + " " + detailedScore);
        }
    }
}
