package com.arm.wa.uiauto.chrome;

import android.app.Activity;
import android.os.Bundle;
import org.junit.Test;
import org.junit.runner.RunWith;
import android.support.test.runner.AndroidJUnit4;

import android.util.Log;
import android.view.KeyEvent;

// Import the uiautomator libraries
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import com.arm.wa.uiauto.BaseUiAutomation;

import java.util.concurrent.TimeUnit;

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends BaseUiAutomation {

    protected Bundle parameters;
    protected String packageID;
    protected int example_parameter;

    public static String TAG = "speedometer";

    public static final long WAIT_TIMEOUT_5SEC = TimeUnit.SECONDS.toMillis(5);
    public static final long WAIT_TIMEOUT_30SEC = TimeUnit.SECONDS.toMillis(30);
    public static final long WAIT_TIMEOUT_20MIN = TimeUnit.SECONDS.toMillis(20 * 60);

    @Before
    public void initialize() throws Exception {
    }

    @Test
    public void setup() throws Exception {
        dismissSignIn();
        dissmissTurnOnPrivacy();
        dismissAck();
    }

    @Test
    public void runWorkload() throws Exception {
    }

    @Test
    public void extractResults() throws Exception {
        dismissPopUp();
    }

    private void dismissSignIn() throws Exception {
        UiObject withoutAccountButton =
           mDevice.findObject(new UiSelector().textContains("Use without an account")
                                         .className("android.widget.Button"));
        if (!withoutAccountButton.waitForExists(WAIT_TIMEOUT_5SEC)) {
            return;
        }
        withoutAccountButton.click();
    }

    private void dissmissTurnOnPrivacy() throws Exception {
        UiObject noThanksButton =
           mDevice.findObject(new UiSelector().textContains("No Thanks")
                                         .className("android.widget.Button"));
        if (!noThanksButton.waitForExists(WAIT_TIMEOUT_5SEC)) {
            return;
        }
        noThanksButton.click();
    }

    private void dismissAck() throws Exception {
        UiObject ackButton =
           mDevice.findObject(new UiSelector().textContains("Got it")
                                         .className("android.widget.Button"));
        if (!ackButton.waitForExists(WAIT_TIMEOUT_5SEC)) {
            return;
        }
        ackButton.click();
    }

    private void dismissPopUp() throws Exception {
        UiObject noThanksButton =
           mDevice.findObject(new UiSelector().textContains("No Thanks")
                                         .className("android.widget.Button"));
        if (!noThanksButton.waitForExists(WAIT_TIMEOUT_5SEC)) {
            return;
        }
        noThanksButton.click();
    }
}