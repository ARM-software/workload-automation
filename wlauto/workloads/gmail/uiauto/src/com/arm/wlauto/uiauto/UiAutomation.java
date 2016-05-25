/*    Copyright 2014-2016 ARM Limited
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

package com.arm.wlauto.uiauto.gmail;

import android.os.Bundle;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.util.concurrent.TimeUnit;
import java.util.LinkedHashMap;

public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "uxperf_gmail";

    private Bundle parameters;
    private int networkTimeoutSecs = 20;
    private long networkTimeout =  TimeUnit.SECONDS.toMillis(networkTimeoutSecs);
    private LinkedHashMap<String, Timer> timingResults = new LinkedHashMap<String, Timer>();

    public void runUiAutomation() throws Exception {
        parameters = getParams();

        setScreenOrientation(ScreenOrientation.NATURAL);

        clearFirstRunDialogues();

        clickNewMail();
        setToField(parameters);
        setSubjectField();
        setComposeField();
        attachFiles();
        clickSendButton();

        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    public void clearFirstRunDialogues() throws Exception {
        // The first run dialogues vary on different devices so check if they are there and dismiss
        UiObject gotItBox = new UiObject(new UiSelector().resourceId("com.google.android.gm:id/welcome_tour_got_it")
                                                     .className("android.widget.TextView"));
        if (gotItBox.exists()) {
            clickUiObject(gotItBox, timeout);
        }
        UiObject takeMeToBox = new UiObject(new UiSelector().textContains("Take me to Gmail")
                                                            .className("android.widget.TextView"));
        if (takeMeToBox.exists()) {
            clickUiObject(takeMeToBox, timeout);
        }

        UiObject syncNowButton = new UiObject(new UiSelector().textContains("Sync now")
                                                              .className("android.widget.Button"));

        // On some devices we need to wait for a sync to occur after clearing the data
        // We also need to sleep here since waiting for a new window is not enough
        if (syncNowButton.exists()) {
            syncNowButton.clickAndWaitForNewWindow(timeout);
            sleep(10);
        }
    }

    public void clickNewMail() throws Exception {
        UiObject conversationView = new UiObject(new UiSelector()
                                            .resourceId("com.google.android.gm:id/conversation_list_view")
                                            .className("android.widget.ListView"));

        if (!conversationView.waitForExists(networkTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"conversationView\".");
        }

        Timer result = new Timer();
        UiObject newMailButton = getUiObjectByDescription("Compose", "android.widget.ImageButton");
        result.start();
        clickUiObject(newMailButton, timeout);
        result.end();
        timingResults.put("Create_newMail", result);
    }

    public boolean hasComposeView() throws Exception {
        UiObject composeView = new UiObject(new UiSelector().resourceId("com.google.android.gm:id/compose"));
        return composeView.waitForExists(networkTimeout);
    }

    public void setToField(final Bundle parameters) throws Exception {
        Timer result = new Timer();
        UiObject toField = getUiObjectByText("To", "android.widget.TextView");
        String recipient = parameters.getString("recipient").replace('_', ' ');
        result.start();
        toField.setText(recipient);
        getUiDevice().getInstance().pressEnter();
        result.end();
        timingResults.put("Create_To", result);
    }

    public void setSubjectField() throws Exception {
        Timer result = new Timer();
        UiObject subjectField = getUiObjectByText("Subject", "android.widget.EditText");
        result.start();
        // Click on the subject field is required on some platforms to exit the To box cleanly
        subjectField.click();
        subjectField.setText("This is a test message");
        getUiDevice().getInstance().pressEnter();
        result.end();
        timingResults.put("Create_Subject", result);
    }

    public void setComposeField() throws Exception {
        Timer result = new Timer();
        UiObject composeField = getUiObjectByText("Compose email", "android.widget.EditText");
        result.start();
        composeField.setText("This is a test composition");
        getUiDevice().getInstance().pressEnter();
        result.end();
        timingResults.put("Create_Compose", result);
    }

    public void clickSendButton() throws Exception {
        Timer result = new Timer();
        UiObject sendButton = getUiObjectByDescription("Send", "android.widget.TextView");
        result.start();
        clickUiObject(sendButton, timeout);
        result.end();
        timingResults.put("Create_Send", result);

        sendButton.waitUntilGone(networkTimeoutSecs);
    }

    public void attachFiles() throws Exception {
        UiObject attachIcon = getUiObjectByResourceId("com.google.android.gm:id/add_attachment",
                                                      "android.widget.TextView");

        String[] imageFiles = {"1.jpg", "2.jpg", "3.jpg", "4.jpg", "5.jpg"};

        for ( int i = 0; i < imageFiles.length; i++) {
            Timer result = new Timer();
            result.start();

            clickUiObject(attachIcon, timeout);
            UiObject attachFile = getUiObjectByText("Attach file", "android.widget.TextView");
            clickUiObject(attachFile, timeout);

            UiObject titleIsWaWorking = new UiObject(new UiSelector()
                                                .className("android.widget.TextView")
                                                .textContains("wa-working"));
            UiObject titleIsImages = new UiObject(new UiSelector()
                                                .className("android.widget.TextView")
                                                .textContains("Images"));
            UiObject frameLayout = new UiObject(new UiSelector()
                                                .className("android.widget.FrameLayout")
                                                .resourceId("android:id/action_bar_container"));
            UiObject rootMenu = new UiObject(new UiSelector()
                                                .className("android.widget.ImageButton")
                                                .descriptionContains("Show roots"));
            UiObject imagesEntry = new UiObject(new UiSelector()
                                                .className("android.widget.TextView")
                                                .textContains("Images"));
            UiObject waFolder =  new UiObject(new UiSelector()
                                                .className("android.widget.TextView")
                                                .textContains("wa-working"));

            // Some devices use a FrameLayout as oppoised to a view Group so treat them differently
            if (frameLayout.exists()) {
                imagesEntry.click();
                waitObject(titleIsImages, 4);
                waFolder.click();
                waitObject(titleIsWaWorking, 4);
            } else {
                // Portrait devices will roll the menu up so click the root menu icon
                if (!titleIsWaWorking.exists()) {
                    if (rootMenu.exists()) {
                       rootMenu.click();
                    }
                    imagesEntry.click();
                    waitObject(titleIsImages, 4);
                    waFolder.click();
                    waitObject(titleIsWaWorking, 4);
                }
            }

            UiObject imageFileButton = new UiObject(new UiSelector()
                                                .resourceId("com.android.documentsui:id/grid")
                                                .className("android.widget.GridView")
                                                .childSelector(new UiSelector()
                                                .index(i).className("android.widget.FrameLayout")));
            imageFileButton.click();
            imageFileButton.waitUntilGone(timeout);

            result.end();

            // Replace whitespace and full stops within the filename
            String file = imageFiles[i].replaceAll("\\.", "_").replaceAll("\\s+", "_");
            timingResults.put(String.format("AttachFiles" + "_" + file), result);
        }
    }
}
