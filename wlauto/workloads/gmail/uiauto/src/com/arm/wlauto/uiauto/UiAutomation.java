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
    private long networkTimeout =  TimeUnit.SECONDS.toMillis(20);
    private LinkedHashMap<String, Timer> timingResults = new LinkedHashMap<String, Timer>();

    public void runUiAutomation() throws Exception {
        parameters = getParams();

        clearFirstRunDialogues();

        clickNewMail();
        attachFiles();
        setToField();
        setSubjectField();
        setComposeField();
        clickSendButton();

        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    public void clearFirstRunDialogues () throws Exception {
        // Enter search text into the file searchBox.  This will automatically filter the list.
        UiObject gotItBox = getUiObjectByResourceId("com.google.android.gm:id/welcome_tour_got_it",
                                                     "android.widget.TextView");
        clickUiObject(gotItBox, timeout);
        UiObject takeMeToBox = getUiObjectByText("Take me to Gmail", "android.widget.TextView");
        clickUiObject(takeMeToBox, timeout);
        UiObject converationView = new UiObject(new UiSelector()
                                            .resourceId("com.google.android.gm:id/conversation_list_view")
                                            .className("android.widget.ListView"));
        if (!converationView.waitForExists(networkTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"converationView\".");
        }
    }

    public void clickNewMail() throws Exception {
        Timer result = new Timer();
        UiObject newMailButton = getUiObjectByDescription("Compose", "android.widget.ImageButton");
        result.start();
        clickUiObject(newMailButton, timeout);
        result.end();
        timingResults.put("newMail", result);
    }

    public void setToField() throws Exception {
        Timer result = new Timer();
        UiObject toField = getUiObjectByDescription("To", "android.widget.TextView");
        String recipient = parameters.getString("recipient").replace('_', ' ');
        result.start();
        toField.setText(recipient);
        getUiDevice().pressEnter();
        result.end();
        timingResults.put("To", result);
    }

    public void setSubjectField() throws Exception {
        Timer result = new Timer();
        UiObject subjectField = getUiObjectByText("Subject", "android.widget.EditText");
        result.start();
        subjectField.setText("This is a test message");
        getUiDevice().pressEnter();
        result.end();
        timingResults.put("Subject", result);
    }

    public void setComposeField() throws Exception {
        Timer result = new Timer();
        UiObject composeField = getUiObjectByText("Compose email", "android.widget.EditText");
        result.start();
        composeField.setText("This is a test composition");
        getUiDevice().pressEnter();
        result.end();
        timingResults.put("Compose", result);
    }

    public void clickSendButton() throws Exception {
        Timer result = new Timer();
        UiObject sendButton = getUiObjectByDescription("Send", "android.widget.TextView");
        result.start();
        clickUiObject(sendButton, timeout);
        result.end();
        timingResults.put("Send", result);
    }

    public void attachFiles() throws Exception {
        Timer result = new Timer();
        UiObject attachIcon = getUiObjectByResourceId("com.google.android.gm:id/add_attachment",
                                                      "android.widget.TextView");

        String[] imageFiles = {"1.jpg", "2.jpg", "3.jpg", "4.jpg", "5.jpg"};

        for ( int i = 0; i < imageFiles.length; i++) {
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

            clickUiObject(imageFileButton, timeout);

            result.end();

            // Replace whitespace and full stops within the filename
            String file = imageFiles[i].replaceAll("\\.", "_").replaceAll("\\s+", "_");
            timingResults.put(String.format("AttachFiles" + "_" + file), result);
        }
    }
}
