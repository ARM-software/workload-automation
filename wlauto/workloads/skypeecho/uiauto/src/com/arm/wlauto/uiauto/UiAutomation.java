package com.arm.wlauto.uiauto.skypeecho;

import java.io.File;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.util.TreeMap;
import java.util.Map;
import java.util.Map.Entry;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.KeyEvent;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

public class UiAutomation extends UxPerfUiAutomation {

    public static final String TAG = "skypeecho";
    public static final String PACKAGE = "com.skype.raider";
    public static final String PACKAGE_ID = "com.skype.raider:id/";

    public static String sendSmsButtonResourceId = PACKAGE_ID + "chat_menu_item_send_sms";
    public static String voiceCallButtonResourceId = PACKAGE_ID + "chat_menu_item_call_voice";
    public static String videoCallButtonResourceId = PACKAGE_ID + "chat_menu_item_call_video";
    public static String endCallButtonResourceId = PACKAGE_ID + "call_end_button";
    public static String noContactMessage = "Could not find contact \"%s\" in the contacts list.";

    private Map<String, Timer> results = new TreeMap<String, Timer>();
    private boolean dumpsysEnabled;
    private String outputDir;

    private static Arguments args;

    private static final class Arguments {
        String loginName;
        String loginPass;
        String contactSkypeid;
        String contactName;
        int callDuration;
        String callType;
        String resultsFile;
        String outputDir;
        boolean dumpsysEnabled;
    }

    private static Arguments parseBundle(Bundle bundle) {
        Arguments args = new Arguments();
        args.loginName = bundle.getString("my_id");
        args.loginPass = bundle.getString("my_pwd");
        args.contactSkypeid = bundle.getString("skypeid");
        args.contactName = bundle.getString("name").replace("_", " ");
        args.callDuration = Integer.parseInt(bundle.getString("duration"));
        args.callType = bundle.getString("action");
        args.resultsFile = bundle.getString("results_file");
        args.outputDir = bundle.getString("output_dir");
        args.dumpsysEnabled = bundle.getBoolean("dumpsys_enabled");
        return args;
    }

    public void runUiAutomation() throws Exception {
        // Get Params
        Bundle parameters = getParams();
        String loginName = parameters.getString("my_id");
        String loginPass = parameters.getString("my_pwd");
        String contactSkypeid = parameters.getString("skypeid");
        String contactName = parameters.getString("name").replace("_", " ");
        int callDuration = Integer.parseInt(parameters.getString("duration"));
        String callType = parameters.getString("action");
        String resultsFile = parameters.getString("results_file");
        outputDir = parameters.getString("output_dir", "/sdcard/wa-working");
        dumpsysEnabled = parameters.getBoolean("dumpsys_enabled", true);

        // Run tests
        Timer overallTimer = new Timer();
        overallTimer.start();
        handleLoginScreen(loginName, loginPass);
        selectContact(contactName, contactSkypeid);
        if ("video".equalsIgnoreCase(callType)) {
            videoCallTest(callDuration);
        } else if ("voice".equalsIgnoreCase(callType)) {
            voiceCallTest(callDuration);
        } else {
            // both ?
            // voiceCallTest(callDuration);
            // videoCallTest(callDuration);
        }
        overallTimer.end();

        // Save results
        results.put("overall_test", overallTimer);
        saveResults(results, resultsFile);
    }

    private void saveResults(Map<String, Timer> results, String file) throws Exception {
        BufferedWriter out = new BufferedWriter(new FileWriter(file));
        long start, finish, duration;
        for (Map.Entry<String, Timer> entry : results.entrySet()) {
            Timer timer = entry.getValue();
            start = timer.getStart();
            finish = timer.getFinish();
            duration = timer.getDuration();
            // Format used to parse out results in workload's update_result function
            out.write(String.format("timer: %s %d %d %d\n", entry.getKey(), start, finish, duration));
        }
        out.close();
    }

    private void handleLoginScreen(String username, String password) throws Exception {
        String useridResoureId = PACKAGE_ID + "sign_in_userid";
        String nextButtonResourceId = PACKAGE_ID + "sign_in_next_btn";
        UiObject useridField = new UiObject(new UiSelector().resourceId(useridResoureId));
        UiObject nextButton = new UiObject(new UiSelector().resourceId(nextButtonResourceId));
        useridField.setText(username);
        nextButton.clickAndWaitForNewWindow();

        String skypenameResoureId = PACKAGE_ID + "signin_skypename";
        String passwordResoureId = PACKAGE_ID + "signin_password";
        String signinButtonResourceId = PACKAGE_ID + "sign_in_btn";
        // UiObject skypenameField = new UiObject(new UiSelector().resourceId(skypenameResoureId));
        UiObject passwordField = new UiObject(new UiSelector().resourceId(passwordResoureId));
        UiObject signinButton = new UiObject(new UiSelector().resourceId(signinButtonResourceId));
        // skypenameField.setText(username);
        passwordField.setText(password);
        signinButton.clickAndWaitForNewWindow();
    }

    private void selectContact(String name, String id) throws Exception {
        Timer timer = new Timer();
        timer.start();
        UiObject peopleTab;
        // Open the 'People' tab aka contacts view
        // On phones, it is represented by an image with description
        // On tablets, it the full text is shown without a description
        try {
            peopleTab = getUiObjectByDescription("People", "android.widget.TextView");
        } catch (UiObjectNotFoundException e) {
            peopleTab = getUiObjectByText("People", "android.widget.TextView");
        }
        peopleTab.click();

        // On first startup, the app may take a while to load the display name,
        // so try twice before declaring failure
        UiObject contactCard;
        try {
            contactCard = getUiObjectByText(name, "android.widget.TextView");
        } catch (UiObjectNotFoundException e) {
            contactCard = getUiObjectByText(name, "android.widget.TextView");
            // contactCard = getUiObjectByText(id, "android.widget.TextView");
        }
        contactCard.clickAndWaitForNewWindow();
        timer.end();
        results.put("select_contact", timer);
    }

    private void voiceCallTest(int duration) throws Exception {
        String testTag = "voice_call";
        Timer timer = new Timer();
        timer.start();
        makeCall(duration, false, testTag);
        timer.end();
        results.put(testTag, timer);
    }

    private void videoCallTest(int duration) throws Exception {
        String testTag = "video_call";
        Timer timer = new Timer();
        timer.start();
        makeCall(duration, true, testTag);
        timer.end();
        results.put(testTag, timer);
    }

    private void makeCall(int duration, boolean video, String testTag) throws Exception {
        String viewName = "com.skype.android.app.calling.CallActivity";
        String dumpsysTag = TAG + "_" + testTag;
        int viewTimeout = 5000;
        if (video && dumpsysEnabled) {
            initDumpsysSurfaceFlinger(PACKAGE, viewName);
            initDumpsysGfxInfo(PACKAGE);
        }

        // String resource = video ? videoCallButtonResourceId : voiceCallButtonResourceId;
        // UiObject callButton = new UiObject(new UiSelector().resourceId(resource));
        String description = video ? "Video call" : "Call options";
        UiObject callButton = new UiObject(new UiSelector().descriptionContains(description));
        callButton.click();
        // callButton.clickAndWaitForNewWindow();
        sleep(duration);
        // endCall();

        if (video && dumpsysEnabled) {
            exitDumpsysSurfaceFlinger(PACKAGE, viewName, new File(outputDir, dumpsysTag + "_surface_flinger.log"));
            exitDumpsysGfxInfo(PACKAGE, new File(outputDir, dumpsysTag + "_gfxinfo.log"));
        }
    }

}
