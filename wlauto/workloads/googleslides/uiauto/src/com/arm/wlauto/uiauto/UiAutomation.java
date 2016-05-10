package com.arm.wlauto.uiauto.googleslides;

import java.io.File;
import java.util.LinkedHashMap;
import java.util.Map;

import android.app.Activity;
import android.content.Context;
import android.net.wifi.WifiManager;
import android.os.Bundle;
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

    public static String TAG = "googleslides";
    public static final String PACKAGE = "com.google.android.apps.docs.editors.slides";
    public static final String PACKAGE_ID = PACKAGE + ":id/";

    public static final String CLASS_TEXT_VIEW = "android.widget.TextView";
    public static final String CLASS_IMAGE_VIEW = "android.widget.ImageView";
    public static final String CLASS_BUTTON = "android.widget.Button";
    public static final String CLASS_IMAGE_BUTTON = "android.widget.ImageButton";
    public static final String CLASS_TABLE_ROW = "android.widget.TableRow";

    public Bundle parameters;
    private Map<String, Timer> results = new LinkedHashMap<String, Timer>();
    private boolean dumpsysEnabled;
    private String outputDir;

    public static final int DOCTYPE_TEMPLATE = 1;
    public static final int DOCTYPE_PPT = 2;
    public static final int DOCTYPE_SLIDES = 3;

    public void runUiAutomation() throws Exception {
        parameters = getParams();
        parseParams(parameters);
        skipWelcomeScreen();
        enablePowerpointCompat();
        if (false) { // TODO currently unused
            openFromStorage();
        }
        createNewDoc(DOCTYPE_TEMPLATE);
        setWifiStatus(false);
        tapDisplayNormalised(0.99, 0.99);
        sleep(5);
        if (false) { // TODO currently unused
            writeResultsToFile(results, parameters.getString("results_file"));
        }
    }

    public void parseParams(Bundle parameters) throws Exception {
        dumpsysEnabled = Boolean.parseBoolean(parameters.getString("dumpsys_enabled"));
        outputDir = parameters.getString("output_dir", "/sdcard/wa-working");
    }

    private void skipWelcomeScreen() throws Exception {
        UiObject skipButton = getUiObjectByText("Skip", CLASS_BUTTON);
        skipButton.clickAndWaitForNewWindow();
        sleep(1);
    }

    private void enablePowerpointCompat() throws Exception {
        uiDeviceEdgeSwipeFromLeft(10);
        UiObject settings = getUiObjectByText("Settings", CLASS_TEXT_VIEW);
        settings.clickAndWaitForNewWindow();
        UiObject checkboxRow = getUiObjectByText("Create PowerPoint", CLASS_TEXT_VIEW);
        checkboxRow.click();
        getUiDevice().pressBack();
        sleep(1);
    }

    private void openFromStorage() throws Exception {
        // UiObject newButton = getUiObjectByResourceId(PACKAGE_ID + "menu_open_with_picker", CLASS_TEXT_VIEW);
        UiObject openButton = getUiObjectByDescription("Open presentation", CLASS_TEXT_VIEW);
        openButton.click();
        openButton = getUiObjectByText("Device storage", CLASS_TEXT_VIEW);
        openButton.clickAndWaitForNewWindow();
        getUiDevice().pressBack();
        sleep(1);
    }

    private void createNewDoc(int docType) throws Exception {
        // UiObject newButton = getUiObjectByResourceId(PACKAGE_ID + "fab_base_button", CLASS_IMAGE_BUTTON);
        UiObject newButton = getUiObjectByDescription("New presentation", CLASS_IMAGE_BUTTON);
        newButton.click();

        UiObject newPowerpoint = getUiObjectByDescription("New PowerPoint", CLASS_IMAGE_BUTTON);
        UiObject newSlidesFile = getUiObjectByDescription("New Slides", CLASS_IMAGE_BUTTON);
        UiObject fromTemplate = getUiObjectByDescription("Choose template", CLASS_IMAGE_BUTTON);
        // UiObject newPowerpoint = getUiObjectByText("New PowerPoint", CLASS_TEXT_VIEW);
        // UiObject newSlidesFile = getUiObjectByText("New Slides", CLASS_TEXT_VIEW);
        // UiObject fromTemplate = getUiObjectByText("Choose template", CLASS_TEXT_VIEW);

        switch (docType) {
            case DOCTYPE_TEMPLATE:
                fromTemplate.clickAndWaitForNewWindow();
                break;
            case DOCTYPE_PPT:
                newPowerpoint.clickAndWaitForNewWindow();
                break;
            case DOCTYPE_SLIDES:
            default:
                newSlidesFile.clickAndWaitForNewWindow();
                break;
        }
        sleep(1);
        getUiDevice().pressBack();
    }

    public void uiDeviceEdgeSwipeFromLeft(int steps) {
        int height = getDisplayHeight();
        int width = getDisplayWidth();
        getUiDevice().swipe(0, height/2, width/2, height/2, steps);
    }

    public void tapDisplayNormalised(double percentX, double percentY) {
        double x = Math.max(0, Math.min(1, percentX));
        double y = Math.max(0, Math.min(1, percentY));
        int tapX = (int) Math.floor(x * getDisplayWidth());
        int tapY = (int) Math.floor(y * getDisplayHeight());
        getUiDevice().click(tapX, tapY);
    }

    public void setWifiStatus(boolean flag) throws Exception {
        // To enable, check for "UninitializedState"
        String checkFor = flag ? "UninitializedState" : "ConnectedState";
        String adbCommand =
              "dumpsys wifi | grep curState=" + checkFor + ";"
            + "exit_code=$?;"
            + "if [ $exit_code = 0 ]; then"
            + "    am start -a android.intent.action.MAIN -n com.android.settings/.wifi.WifiSettings;"
            + "    input keyevent 20;"
            + "    input keyevent 23;"
            + "    sleep 1;"
            + "    input keyevent 4;"
            + "fi";
        // runShellCommand(adbCommand);
        runShellCommand("dumpsys wifi | grep curState=ConnectedState");
        sleep(1);
    }

    public void runShellCommand(String command) throws Exception {
        Process proc = Runtime.getRuntime().exec(command);
    }
}
