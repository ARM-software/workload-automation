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
import com.arm.wlauto.uiauto.ApplaunchInterface;
import com.arm.wlauto.uiauto.UiAutoUtils;

import java.util.concurrent.TimeUnit;

public class UiAutomation extends UxPerfUiAutomation implements ApplaunchInterface{

    private int networkTimeoutSecs = 30;
    private long networkTimeout =  TimeUnit.SECONDS.toMillis(networkTimeoutSecs);

    public void runUiAutomation() throws Exception {
        parameters = getParams();

        String recipient = parameters.getString("recipient");

        setScreenOrientation(ScreenOrientation.NATURAL);
        runApplicationInitialization();

        clickNewMail();
        attachImage();
        setToField(recipient);
        setSubjectField();
        setComposeField();
        clickSendButton();

        unsetScreenOrientation();
    }
    
    // Get application parameters and clear the initial run dialogues of the application launch.
    public void runApplicationInitialization() throws Exception {
        getPackageParameters();
        clearFirstRunDialogues();
    }
    
    // Sets the UiObject that marks the end of the application launch.
    public UiObject getLaunchEndObject() {
        UiObject launchEndObject = 
                        new UiObject(new UiSelector().className("android.widget.ImageButton"));
        return launchEndObject;
    }
    
    // Returns the launch command for the application.
    public String getLaunchCommand() {
        String launch_command;
        launch_command = UiAutoUtils.createLaunchCommand(parameters);
        return launch_command;
    }
    
    // Pass the workload parameters, used for applaunch
    public void setWorkloadParameters(Bundle workload_parameters) {
        parameters = workload_parameters;
    }

    public void clearFirstRunDialogues() throws Exception {
        // The first run dialogues vary on different devices so check if they are there and dismiss
        UiObject gotItBox =
            new UiObject(new UiSelector().resourceId(packageID + "welcome_tour_got_it")
                                         .className("android.widget.TextView"));
        if (gotItBox.exists()) {
            gotItBox.clickAndWaitForNewWindow(uiAutoTimeout);
        }

        UiObject takeMeToBox =
            new UiObject(new UiSelector().textContains("Take me to Gmail")
                                         .className("android.widget.TextView"));
        if (takeMeToBox.exists()) {
            takeMeToBox.clickAndWaitForNewWindow(uiAutoTimeout);
        }

        UiObject syncNowButton =
            new UiObject(new UiSelector().textContains("Sync now")
                                         .className("android.widget.Button"));
        if (syncNowButton.exists()) {
            syncNowButton.clickAndWaitForNewWindow(uiAutoTimeout);
            // On some devices we need to wait for a sync to occur after clearing the data
            // We also need to sleep here since waiting for a new window is not enough
            sleep(10);
        }

        // Wait an obnoxiously long period of time for the sync operation to finish
        // If it still fails, then there is a problem with the app obtaining the data it needs
        // Recommend restarting the phone and/or clearing the app data
        UiObject gettingMessages =
            new UiObject(new UiSelector().textContains("Getting your messages")
                                         .className("android.widget.TextView"));
        UiObject waitingSync =
            new UiObject(new UiSelector().textContains("Waiting for sync")
                                         .className("android.widget.TextView"));
        if (!waitUntilNoObject(gettingMessages, networkTimeoutSecs*4) ||
            !waitUntilNoObject(waitingSync, networkTimeoutSecs*4)) {
            throw new UiObjectNotFoundException("Device cannot sync! Try rebooting or clearing app data");
        }
    }

    public void clickNewMail() throws Exception {
        String testTag = "click_new";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        UiObject conversationView =
            new UiObject(new UiSelector().resourceId(packageID + "conversation_list_view")
                                         .className("android.widget.ListView"));
        if (!conversationView.waitForExists(networkTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"conversationView\".");
        }

        UiObject newMailButton =
            getUiObjectByDescription("Compose", "android.widget.ImageButton");
        logger.start();
        newMailButton.clickAndWaitForNewWindow(uiAutoTimeout);
        logger.stop();
    }

    public void attachImage() throws Exception {
        String testTag = "attach_img";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        UiObject attachIcon =
            getUiObjectByResourceId(packageID + "add_attachment", "android.widget.TextView");

        logger.start();

        attachIcon.click();
        UiObject attachFile =
            getUiObjectByText("Attach file", "android.widget.TextView");
        attachFile.clickAndWaitForNewWindow(uiAutoTimeout);

        UiObject waFolder = 
            new UiObject(new UiSelector().textContains("wa-working")
                                         .className("android.widget.TextView"));
        // Some devices use a FrameLayout as oppoised to a view Group so treat them differently
        if (!waFolder.waitForExists(uiAutoTimeout)) {
            UiObject rootMenu =
                new UiObject(new UiSelector().descriptionContains("Show roots")
                                             .className("android.widget.ImageButton"));
            // Portrait devices will roll the menu up so click the root menu icon
            if (rootMenu.exists()) {
               rootMenu.click();
            }

            UiObject imagesEntry =
                new UiObject(new UiSelector().textContains("Images")
                                             .className("android.widget.TextView"));
            // Go to the 'Images' section
            if (imagesEntry.waitForExists(uiAutoTimeout)) {
                imagesEntry.click();
            }
            // Find and select the folder
            selectGalleryFolder("wa-working");
        }

        UiObject imageFileButton =
            new UiObject(new UiSelector().resourceId("com.android.documentsui:id/grid")
                                         .className("android.widget.GridView")
                                         .childSelector(new UiSelector().index(0)
                                         .className("android.widget.FrameLayout")));
        imageFileButton.click();
        imageFileButton.waitUntilGone(uiAutoTimeout);

        logger.stop();
    }

    public void setToField(String recipient) throws Exception {
        String testTag = "text_to";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        UiObject toField = getUiObjectByText("To", "android.widget.TextView");
        logger.start();
        toField.setText(recipient);
        getUiDevice().getInstance().pressEnter();
        logger.stop();
    }

    public void setSubjectField() throws Exception {
        String testTag = "text_subject";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        UiObject subjectField = getUiObjectByText("Subject", "android.widget.EditText");
        logger.start();
        // Click on the subject field is required on some platforms to exit the To box cleanly
        subjectField.click();
        subjectField.setText("This is a test message");
        getUiDevice().getInstance().pressEnter();
        logger.stop();
    }

    public void setComposeField() throws Exception {
        String testTag = "text_body";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        UiObject composeField = getUiObjectByText("Compose email", "android.widget.EditText");
        logger.start();
        composeField.setText("This is a test composition");
        getUiDevice().getInstance().pressEnter();
        logger.stop();
    }

    public void clickSendButton() throws Exception {
        String testTag = "click_send";
        ActionLogger logger = new ActionLogger(testTag, parameters);
        
        UiObject sendButton = getUiObjectByDescription("Send", "android.widget.TextView");
        logger.start();
        sendButton.clickAndWaitForNewWindow(uiAutoTimeout);
        logger.stop();
        sendButton.waitUntilGone(networkTimeoutSecs);
    }
}
