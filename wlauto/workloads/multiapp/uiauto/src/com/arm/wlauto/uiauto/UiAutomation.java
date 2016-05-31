package com.arm.wlauto.uiauto.multiapp;

import android.os.Bundle;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.io.File;
import java.util.concurrent.TimeUnit;
import java.util.LinkedHashMap;

public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "uxperf_multiapp";

    public Bundle parameters;
    private LinkedHashMap<String, Timer> timingResults = new LinkedHashMap<String, Timer>();

    public void runUiAutomation() throws Exception {
        parameters = getParams();

        com.arm.wlauto.uiauto.googlephotos.UiAutomation googlephotos =
            new com.arm.wlauto.uiauto.googlephotos.UiAutomation();

        confirmAccess();
        googlephotos.dismissWelcomeView();
        googlephotos.selectWorkingGallery();

        // select the first photo
        googlephotos.tagPhoto(0);
        sendToGmail();

        // select the second photo
        googlephotos.tagPhoto(1);
        logIntoSkype();

        // Skype won't allow us to login and share on first visit so invoke
        // once more from googlephotos
        pressBack();
        pressBack();
        googlephotos.tagPhoto(1);

        sendToSkype();

        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    private void sendToGmail() throws Exception {
        com.arm.wlauto.uiauto.gmail.UiAutomation gmail =
            new com.arm.wlauto.uiauto.gmail.UiAutomation();

        shareUsingApp("Gmail");
        gmail.clearFirstRunDialogues();

        if (!gmail.hasComposeView()) {
            waitForSync();
        }

        gmail.setToField(parameters);
        gmail.setSubjectField();
        gmail.setComposeField();
        gmail.clickSendButton();
    }

    private void waitForSync() throws Exception {
        // After the initial share request on some devices Gmail returns back
        // to the launching app, so we need to share the photo once more and
        // wait for Gmail to sync.
        com.arm.wlauto.uiauto.googlephotos.UiAutomation googlephotos =
            new com.arm.wlauto.uiauto.googlephotos.UiAutomation();

        com.arm.wlauto.uiauto.gmail.UiAutomation gmail =
            new com.arm.wlauto.uiauto.gmail.UiAutomation();

        googlephotos.tagPhoto(1);
        shareUsingApp("Gmail");
        gmail.clearFirstRunDialogues();
    }

    private void logIntoSkype()  throws Exception {
        com.arm.wlauto.uiauto.skype.UiAutomation skype =
            new com.arm.wlauto.uiauto.skype.UiAutomation();

        String loginName = parameters.getString("my_id");
        String loginPass = parameters.getString("my_pwd");

        shareUsingApp("Skype");
        skype.handleLoginScreen(loginName, loginPass);
        confirmAccess();

        sleep(10); // Pause while the app settles before returning
    }

    private void sendToSkype() throws Exception {
        com.arm.wlauto.uiauto.skype.UiAutomation skype =
            new com.arm.wlauto.uiauto.skype.UiAutomation();

        String contactName = parameters.getString("name").replace("_", " ");

        shareUsingApp("Skype");
        skype.searchForContact(contactName);
    }

    private void shareUsingApp(String appName) throws Exception {
        Timer result = new Timer();
        result.start();
        UiObject shareButton = getUiObjectByDescription("Share", "android.widget.TextView");
        shareButton.click();

        UiScrollable applicationGrid =
            new UiScrollable(new UiSelector().resourceId("com.google.android.apps.photos:id/application_grid"));

        UiObject openApp = new UiObject(new UiSelector().className("android.widget.TextView").text(appName));

        while (!openApp.exists()) {
            applicationGrid.scrollForward();
        }

        openApp.clickAndWaitForNewWindow();
        String testTag = String.format("share_using_%s", appName);

        result.end();
        timingResults.put(testTag, result);
    }
}
