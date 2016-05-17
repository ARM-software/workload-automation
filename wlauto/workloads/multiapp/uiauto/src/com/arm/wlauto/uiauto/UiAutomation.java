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
    private String outputDir;
    private LinkedHashMap<String, Timer> timingResults = new LinkedHashMap<String, Timer>();

    public void runUiAutomation() throws Exception {
        parameters = getParams();

        com.arm.wlauto.uiauto.googlephotos.UiAutomation googlephotos =
            new com.arm.wlauto.uiauto.googlephotos.UiAutomation();

        confirmAccess();
        googlephotos.dismissWelcomeView();

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

        final String dumpsysTag = "sendToGmail";
        final String PACKAGE = "com.google.android.gm";
        String outputDir = parameters.getString("output_dir", "/sdcard/wa-working");

        com.arm.wlauto.uiauto.gmail.UiAutomation gmail =
            new com.arm.wlauto.uiauto.gmail.UiAutomation();

        Timer result = new Timer();
        result.start();

        initDumpsysGfxInfo(PACKAGE);
        shareUsingApp("Gmail");
        gmail.clearFirstRunDialogues();

        if (!gmail.hasComposeView()) {
            waitForSync();
        }

        gmail.setToField(parameters);
        gmail.setSubjectField();
        gmail.setComposeField();
        gmail.clickSendButton();
        exitDumpsysGfxInfo(PACKAGE, new File(outputDir, dumpsysTag + "_gfxInfo.log"));

        result.end();
        timingResults.put("send_to_gmail_contact", result);
    }

    private void waitForSync() throws Exception {

        // After the initial share request on some devices Gmail returns back
        // to the launching app, so we need to share the photo onces more and
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

        final String dumpsysTag = "logInToSkype";
        final String PACKAGE = "com.skype.raider";
        String outputDir = parameters.getString("output_dir", "/sdcard/wa-working");

        com.arm.wlauto.uiauto.skype.UiAutomation skype =
            new com.arm.wlauto.uiauto.skype.UiAutomation();

        String loginName = parameters.getString("my_id");
        String loginPass = parameters.getString("my_pwd");

        Timer result = new Timer();
        result.start();

        initDumpsysGfxInfo(PACKAGE);
        shareUsingApp("Skype");
        skype.handleLoginScreen(loginName, loginPass);
        confirmAccess();
        exitDumpsysGfxInfo(PACKAGE, new File(outputDir, dumpsysTag + "_gfxInfo.log"));

        result.end();
        timingResults.put("log_into_skype", result);
    }

    private void sendToSkype() throws Exception {

        final String dumpsysTag = "sendToSkype";
        final String PACKAGE = "com.skype.raider";
        String outputDir = parameters.getString("output_dir", "/sdcard/wa-working");

        com.arm.wlauto.uiauto.skype.UiAutomation skype =
            new com.arm.wlauto.uiauto.skype.UiAutomation();

        String contactName = parameters.getString("name").replace("_", " ");

        Timer result = new Timer();
        result.start();

        initDumpsysGfxInfo(PACKAGE);
        shareUsingApp("Skype");
        skype.searchForContact(contactName);
        exitDumpsysGfxInfo(PACKAGE, new File(outputDir, dumpsysTag + "_gfxInfo.log"));

        result.end();
        timingResults.put("send_to_skype_contact", result);
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
