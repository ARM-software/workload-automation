package com.arm.wlauto.uiauto.skypeecho;

import java.io.File;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.util.HashMap;
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

    public static String TAG = "uxperf_skypeecho";

    public static String PACKAGE = "com.skype.raider";

    public static String sendSmsButtonResourceId = "com.skype.raider:id/chat_menu_item_send_sms";
    public static String voiceCallButtonResourceId = "com.skype.raider:id/chat_menu_item_call_voice";
    public static String videoCallButtonResourceId = "com.skype.raider:id/chat_menu_item_call_video";
    public static String endCallButtonResourceId = "com.skype.raider:id/call_end_button";
    public static String noContactMessage = "Could not find contact \"%s\" in the contacts list.";

    private Map<String, Timer> results = new HashMap<String, Timer>();

    public void runUiAutomation() throws Exception {
            // Get Params
            Bundle parameters = getParams();
            String loginName = parameters.getString("my_id");
            String loginPass = parameters.getString("my_pwd");
            String contactSkypeid = parameters.getString("skypeid");
            String contactName = parameters.getString("name").replace("_", " ");
            int callDuration = Integer.parseInt(parameters.getString("duration"));
            boolean isVideo = "video".equals(parameters.getString("action"));
            String resultsFile = parameters.getString("results_file");

            // Run tests
            Timer overallTimer = new Timer();
            Timer callTimer = new Timer();
            overallTimer.start();
            handleLoginScreen(loginName, loginPass);
            selectContact(contactName, contactSkypeid);
            callTimer.start();
            makeCall(callDuration, isVideo);
            callTimer.end();
            overallTimer.end();

            // Save results
            results.put("call_test", callTimer);
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
            out.write(entry.getKey() + " " + start + " " + finish + " " + duration + "\n");
        }
        out.close();
    }

    public void selectContact(String name, String id) throws Exception {
            // UiObject peopleTab = new UiObject(selector.text("People"));
            UiObject peopleTab = getUiObjectByDescription("People", "android.widget.TextView");
            peopleTab.click();

            // On first startup, the app may take a while to load the display name, so try twice
            // before declaring failure
            UiObject contactCard;
            try {
                contactCard = getUiObjectByText(name, "android.widget.TextView");
            } catch (UiObjectNotFoundException e) {
                contactCard = getUiObjectByText(name, "android.widget.TextView");
                // contactCard = getUiObjectByText(id, "android.widget.TextView");
            }
            contactCard.clickAndWaitForNewWindow();
    }

    public void makeCall(int duration, boolean video) throws Exception {
            // String resource = video ? videoCallButtonResourceId : voiceCallButtonResourceId;
            // UiObject callButton = new UiObject(new UiSelector().resourceId(resource));
            String description = video ? "Video call" : "Call options";
            UiObject callButton = new UiObject(new UiSelector().descriptionContains(description));
            callButton.click();
            sleep(duration);
            // endCall();g
    }

    /*
    // TODO Needs to be run on UI thread after sleep
    public void endCall() {
        final UiObject endButton = getUiObjectByResourceId(endCallButtonResourceId, "android.widget.ImageView");
        new Handler(Looper.getMainLooper()).postDelayed(new Runnable() {
            @Override
            public void run() {
                try {
                    endButton.click();
                } catch (UiObjectNotFoundException e) {
                    // Do nothing
                }
            }
        }, 10000);
    }
    */

    public void handleLoginScreen(String username, String password) throws Exception {
        String useridResoureId = "com.skype.raider:id/sign_in_userid";
        String nextButtonResourceId = "com.skype.raider:id/sign_in_next_btn";
        UiObject useridField = new UiObject(new UiSelector().resourceId(useridResoureId));
        UiObject nextButton = new UiObject(new UiSelector().resourceId(nextButtonResourceId));
        useridField.setText(username);
        nextButton.clickAndWaitForNewWindow();

        String skypenameResoureId = "com.skype.raider:id/signin_skypename";
        String passwordResoureId = "com.skype.raider:id/signin_password";
        String signinButtonResourceId = "com.skype.raider:id/sign_in_btn";
        // UiObject skypenameField = new UiObject(new UiSelector().resourceId(skypenameResoureId));
        UiObject passwordField = new UiObject(new UiSelector().resourceId(passwordResoureId));
        UiObject signinButton = new UiObject(new UiSelector().resourceId(signinButtonResourceId));
        // skypenameField.setText(username);
        passwordField.setText(password);
        signinButton.clickAndWaitForNewWindow();
    }
}
