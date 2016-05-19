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

package com.arm.wlauto.uiauto.googleslides;

import java.io.File;
import java.util.LinkedHashMap;
import java.util.Map;

import android.app.Activity;
import android.content.Context;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.os.SystemClock;
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

    public static final String TAG = "googleslides";
    public static final String PACKAGE = "com.google.android.apps.docs.editors.slides";
    public static final String PACKAGE_ID = PACKAGE + ":id/";

    public static final String CLASS_TEXT_VIEW = "android.widget.TextView";
    public static final String CLASS_IMAGE_VIEW = "android.widget.ImageView";
    public static final String CLASS_BUTTON = "android.widget.Button";
    public static final String CLASS_IMAGE_BUTTON = "android.widget.ImageButton";
    public static final String CLASS_TABLE_ROW = "android.widget.TableRow";

    public static final int BY_ID = 1;
    public static final int BY_TEXT = 2;
    public static final int BY_DESC = 3;

    public static final String DOC_FILENAME = "UX Perf Slides";

    public static final String DOCUMENTATION_WORKLOADS =
        "class Workload(Extension):\n\tname = None\n\tdef init_resources(self, context):\n\t\tpass\n"
        + "\tdef validate(self):\n\t\tpass\n\tdef initialize(self, context):\n\t\tpass\n"
        + "\tdef setup(self, context):\n\t\tpass\n\tdef setup(self, context):\n\t\tpass\n"
        + "\tdef run(self, context):\n\t\tpass\n\tdef update_result(self, context):\n\t\tpass\n"
        + "\tdef teardown(self, context):\n\t\tpass\n\tdef finalize(self, context):\n\t\tpass\n";

    public static final String DOCUMENTATION_AGENDAS_1 = "An agenda specifies what is to be done during a Workload Automation run, "
        + "including which workloads will be run, with what configuration, which instruments and result processors will be enabled, etc. "
        + "Agenda syntax is designed to be both succinct and expressive. Agendas are specified using YAML notation.";

    public static final String DOCUMENTATION_AGENDAS_2 =
        "Use agendas for:\n\tSpecifying which workloads to run\n\t\t- Multiple iterations\n\t\t- Configuring workloads\n\t"
        + "\t- IDs and Labels\n\tResult Processors and Instrumentation\n\t\t- Result Processors\n\t\t- Instrumentation\n\t"
        + "\t- Disabling result processors and instrumentation\n\tOther Configuration (via config.py)\n";

    protected Map<String, Timer> results = new LinkedHashMap<String, Timer>();

    protected Bundle parameters;
    protected boolean dumpsysEnabled;
    protected String outputDir;
    protected String[] documents;
    protected boolean useLocalFiles;
    protected String resultsFile;

    public void parseParams(Bundle parameters) throws Exception {
        dumpsysEnabled = Boolean.parseBoolean(parameters.getString("dumpsys_enabled"));
        outputDir = parameters.getString("output_dir");
        resultsFile = parameters.getString("results_file");
        documents = parameters.getString("local_files", "::").split("::");
        useLocalFiles = documents.length != 0;
    }

    public void runUiAutomation() throws Exception {
        parameters = getParams();
        parseParams(parameters);
        skipWelcomeScreen();
        enablePowerpointCompat();
        if (useLocalFiles) {
            testEditFileFromStorage(documents[0]);
        } else {
            testEditNewSlidesDoc(DOC_FILENAME);
        }

        if (false) { // TODO currently unused
            writeResultsToFile(results, parameters.getString("results_file"));
        }
    }

    protected void skipWelcomeScreen() throws Exception {
        UiObject skipButton = getUiObjectByText("Skip", CLASS_BUTTON);
        skipButton.clickAndWaitForNewWindow();
        sleep(1);
    }

    protected void enablePowerpointCompat() throws Exception {
        uiDeviceEdgeSwipeFromLeft(10);
        UiObject settings = getUiObjectByText("Settings", CLASS_TEXT_VIEW);
        settings.clickAndWaitForNewWindow();
        UiObject checkboxRow = getUiObjectByText("Create PowerPoint", CLASS_TEXT_VIEW);
        checkboxRow.click();
        getUiDevice().pressBack();
        sleep(1);
    }

    protected void testEditFileFromStorage(String document) throws Exception {
        UiObject openButton = getUiObjectByDescription("Open presentation", CLASS_TEXT_VIEW);
        openButton.click();
        openButton = getUiObjectByText("Device storage", CLASS_TEXT_VIEW);
        openButton.clickAndWaitForNewWindow();

        UiObject selectDoc = getUiObjectByText(document, CLASS_TEXT_VIEW);
        selectDoc.click();
        openButton = getUiObjectByText("Open", CLASS_BUTTON);
        openButton.clickAndWaitForNewWindow();

        sleep(1);
        getUiDevice().pressBack();
        deleteDocument(document);
    }

    protected void testEditNewSlidesDoc(String docName) throws Exception {
        // create new file
        clickView(BY_DESC, "New presentation");
        clickView(BY_TEXT, "New PowerPoint", true);
        // first slide
        enterTextInSlide("Title", "WORKLOAD AUTOMATION");
        enterTextInSlide("Subtitle", "Measuring perfomance of different productivity apps on Android OS");
        saveDocument(docName);

        insertSlide("Title and Content");
        enterTextInSlide("title", "Introduction");
        enterTextInSlide("Text placeholder", "Welcome to Documentation for Workload Automation");
        clickView(BY_DESC, "Undo");
        enterTextInSlide("Text placeholder", "Workload Automation (WA) is a framework for running workloads on real hardware devices. "
            + "WA supports a number of output formats as well as additional instrumentation "
            + "(such as Streamline traces). A number of workloads are included with the framework.");

        insertSlide("Title and Content");
        enterTextInSlide("title", "Extensions - Workloads");
        enterTextInSlide("Text placeholder", DOCUMENTATION_WORKLOADS);
        clickView(BY_DESC, "Text placeholder");
        clickView(BY_DESC, "Format");
        clickView(BY_TEXT, "Droid Sans");
        clickView(BY_TEXT, "Droid Sans Mono");
        clickView(BY_ID, PACKAGE_ID + "palette_back_button");
        UiObject decreaseFont = getViewByDesc("Decrease text");
        repeatClickView(decreaseFont, 20);
        getUiDevice().pressBack();

        insertSlide("Title and Content");
        enterTextInSlide("title", "Agendas - 1");
        enterTextInSlide("Text placeholder", DOCUMENTATION_AGENDAS_1);

        insertSlide("Title and Content");
        enterTextInSlide("title", "Agendas - 2");
        enterTextInSlide("Text placeholder", DOCUMENTATION_AGENDAS_2);

        // get first image in gallery and insert
        insertSlide("Title Only");
        clickView(BY_DESC, "Insert");
        clickView(BY_TEXT, "Image", true);
        clickView(BY_TEXT, "Recent");
        clickView(BY_ID, "com.android.documentsui:id/date", true);

        // last slide
        insertSlide("Title Slide");
        // insert "?" shape
        clickView(BY_DESC, "Insert");
        clickView(BY_TEXT, "Shape");
        clickView(BY_TEXT, "Buttons");
        clickView(BY_DESC, "actionButtonHelp");
        UiObject resize = getViewByDesc("Bottom-left resize");
        UiObject shape = getViewByDesc("actionButtonHelp");
        UiObject subtitle = getViewByDesc("subTitle");
        resize.dragTo(subtitle, 40);
        shape.dragTo(subtitle, 40);
        enterTextInSlide("title", "THE END. QUESTIONS?");

        sleep(1);
        getUiDevice().pressBack();
        deleteDocument(docName);
    }

    public void insertSlide(String slideLayout) throws Exception {
        UiObject view = getViewByDesc("Insert slide");
        view.clickAndWaitForNewWindow();
        view = getViewByText(slideLayout);
        view.clickAndWaitForNewWindow();
    }

    public void saveDocument(String docName) throws Exception {
        clickView(BY_TEXT, "SAVE");
        clickView(BY_TEXT, "Device");
        // Allow SD card access if requested
        UiObject permissionView = new UiObject(new UiSelector().textContains("Allow Slides"));
        if (permissionView.waitForExists(1000)) {
            clickView(BY_TEXT, "Allow");
        }
        UiObject filename = getViewById(PACKAGE_ID + "file_name_edit_text");
        filename.clearTextField();
        filename.setText(docName);
        UiObject saveButton = getUiObjectByText("Save", CLASS_BUTTON);
        saveButton.click();
        // Overwrite if prompted
        UiObject overwriteView = new UiObject(new UiSelector().textContains("already exists"));
        if (overwriteView.waitForExists(1000)) {
            clickView(BY_TEXT, "Overwrite");
        }
        sleep(1);
    }

    public UiObject enterTextInSlide(String viewName, String textToEnter) throws Exception {
        UiObject view = getViewByDesc(viewName);
        view.click();
        sleepMicro(100);
        view.click(); // double click
        view.setText(textToEnter);
        getUiDevice().pressBack();
        sleepMicro(200);
        return view;
    }

    public void deleteDocument(String docName) throws Exception {
        UiObject doc = getViewByText(docName);
        doc.longClick();
        UiObject deleteButton = getUiObjectByText("Remove", CLASS_TEXT_VIEW);
        deleteButton.click();
        try {
            deleteButton = getUiObjectByText("Remove", CLASS_BUTTON);
        } catch (UiObjectNotFoundException e) {
            deleteButton = getUiObjectByText("Ok", CLASS_BUTTON);
        }
        deleteButton.clickAndWaitForNewWindow();
        sleep(1);
    }

    public void sleepMicro(int microseconds) {
        SystemClock.sleep(microseconds);
    }

    public void repeatClickView(UiObject view, int repeat) throws Exception {
        if (repeat < 1 || !view.isClickable()) return;
        while (repeat-- > 0) {
            view.click();
            sleepMicro(10); // in order to register as separate
        }
    }

    public UiObject clickView(int criteria, String matching) throws Exception {
        return clickView(criteria, matching, false);
    }

    public UiObject clickView(int criteria, String matching, boolean wait) throws Exception {
        UiObject view;
        switch (criteria) {
            case BY_ID:
                view = getViewById(matching);
                break;
            case BY_DESC:
                view = getViewByDesc(matching);
                break;
            case BY_TEXT:
            default:
                view = getViewByText(matching);
                break;
        }
        if (wait) {
            view.clickAndWaitForNewWindow();
        } else {
            view.click();
        }
        return view;
    }

    public UiObject getViewByText(String text) throws Exception {
        UiObject object = new UiObject(new UiSelector().textContains(text));
        if (!object.waitForExists(waitTimeout)) {
           throw new UiObjectNotFoundException("Could not find view with text: " + text);
        };
        return object;
    }

    public UiObject getViewByDesc(String desc) throws Exception {
        UiObject object = new UiObject(new UiSelector().descriptionContains(desc));
        if (!object.waitForExists(waitTimeout)) {
           throw new UiObjectNotFoundException("Could not find view with description: " + desc);
        };
        return object;
    }

    public UiObject getViewById(String id) throws Exception {
        UiObject object = new UiObject(new UiSelector().resourceId(id));
        if (!object.waitForExists(waitTimeout)) {
           throw new UiObjectNotFoundException("Could not find view with resource ID: " + id);
        };
        return object;
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

    public void toggleWifiState(boolean flag) throws Exception {
        int exitValue = -1;
        // To enable, check for "UninitializedState"
        // String checkFor = flag ? "UninitializedState" : "ConnectedState";
        // exitValue = runShellCommand("dumpsys wifi | grep curState=" + checkFor);
        // if (0 == exitValue) { // toggle state
        String statusString = flag ? "ConnectedState" : "UninitializedState";
        exitValue = runShellCommand("dumpsys wifi | grep curState=" + statusString);
        if (0 != exitValue) { // not in the expected so toggle it
            String[] adbCommands = {
                "am start -a android.intent.action.MAIN -n com.android.settings/.wifi.WifiSettings;",
                "input keyevent 20;",
                "input keyevent 23;",
                "sleep 1;",
                "input keyevent 4;",
            };
            for (String command : adbCommands) {
                exitValue = runShellCommand(command);
            }
        }
        sleep(1);
    }

    public int runShellCommand(String command) throws Exception {
        Process proc = Runtime.getRuntime().exec(command);
        Log.d(TAG, String.format("Command:\n%s\nExit value:%d\n", command, proc.exitValue()));
        proc.waitFor();
        return proc.exitValue();
    }
}
