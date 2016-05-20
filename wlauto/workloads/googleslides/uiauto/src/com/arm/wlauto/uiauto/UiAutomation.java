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

    public static final int ONE_SECOND_IN_MS = 1000;
    public static final int DEFAULT_SWIPE_STEPS = 20;

    public static final String NEW_DOC_FILENAME = "UX Perf Slides";

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
    protected String localFile;
    protected int slideCount;
    protected boolean useLocalFile;
    protected String resultsFile;

    public void parseParams(Bundle parameters) throws Exception {
        dumpsysEnabled = Boolean.parseBoolean(parameters.getString("dumpsys_enabled"));
        outputDir = parameters.getString("output_dir");
        resultsFile = parameters.getString("results_file");
        localFile = parameters.getString("local_file", "");
        slideCount = Integer.parseInt(parameters.getString("slide_count"));
        useLocalFile = localFile != null;
    }

    public void runUiAutomation() throws Exception {
        parameters = getParams();
        parseParams(parameters);
        skipWelcomeScreen();
        enablePowerpointCompat();
        if (useLocalFile) {
            testSlideshowFromStorage(localFile);
        } else {
            testEditNewSlidesDocument(NEW_DOC_FILENAME);
        }
        if (false) { // TODO currently unused
            writeResultsToFile(results, parameters.getString("results_file"));
        }
    }

    protected void skipWelcomeScreen() throws Exception {
        clickView(BY_TEXT, "Skip", true);
        sleep(1);
    }

    protected void enablePowerpointCompat() throws Exception {
        uiDeviceSwipeHorizontal(0, getDisplayWidth()/2, getDisplayHeight()/2);
        clickView(BY_TEXT, "Settings", true);
        clickView(BY_TEXT, "Create PowerPoint");
        getUiDevice().pressBack();
        sleep(1);
    }

    protected void testSlideshowFromStorage(String docName) throws Exception {
        // Sometimes docs deleted in __init__.py falsely appear on the app's home
        // For robustness, it's nice to remove these placeholders
        // However, the test should not crash because of it, so a silent catch is used
        UiObject docView = new UiObject(new UiSelector().textContains(docName));
        if (docView.waitForExists(ONE_SECOND_IN_MS)) {
            try {
                deleteDocument(docName);
            } catch (Exception e) {
                // do nothing
            }
        }
        clickView(BY_DESC, "Open presentation");
        clickView(BY_TEXT, "Device storage", true);
        // Allow SD card access if requested
        UiObject permissionView = new UiObject(new UiSelector().textContains("Allow Slides"));
        if (permissionView.waitForExists(ONE_SECOND_IN_MS)) {
            clickView(BY_TEXT, "Allow");
        }
        // Scroll through document list if necessary
        UiScrollable list = new UiScrollable(new UiSelector().className("android.widget.ListView"));
        list.scrollIntoView(new UiSelector().textContains(docName));
        clickView(BY_TEXT, docName);
        clickView(BY_TEXT, "Open", CLASS_BUTTON, true);
        sleep(5);

        int centerY = getUiDevice().getDisplayHeight() / 2;
        int centerX = getUiDevice().getDisplayWidth() / 2;
        int slidesLeft = slideCount - 1;
        // scroll forward in edit mode
        while (slidesLeft-- > 0) {
            uiDeviceSwipeHorizontal(centerX + centerX/2, centerX - centerX/2, centerY);
            sleep(1);
        }
        sleep(1);
        // scroll backward in edit mode
        while (++slidesLeft < slideCount - 1) {
            uiDeviceSwipeHorizontal(centerX - centerX/2, centerX + centerX/2, centerY);
            sleep(1);
        }
        // scroll forward in slideshow mode
        clickView(BY_DESC, "Start slideshow", true);
        while (--slidesLeft > 0) {
            uiDeviceSwipeHorizontal(centerX + centerX/2, centerX - centerX/2, centerY);
            sleep(1);
        }
        getUiDevice().pressBack();
        getUiDevice().pressBack();
    }

    protected void testEditNewSlidesDocument(String docName) throws Exception {
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

    public void saveDocument(String docName) throws Exception {
        clickView(BY_TEXT, "SAVE");
        clickView(BY_TEXT, "Device");
        // Allow SD card access if requested
        UiObject permissionView = new UiObject(new UiSelector().textContains("Allow Slides"));
        if (permissionView.waitForExists(ONE_SECOND_IN_MS)) {
            clickView(BY_TEXT, "Allow");
        }
        UiObject filename = getViewById(PACKAGE_ID + "file_name_edit_text");
        filename.clearTextField();
        filename.setText(docName);
        clickView(BY_TEXT, "Save");
        // Overwrite if prompted
        UiObject overwriteView = new UiObject(new UiSelector().textContains("already exists"));
        if (overwriteView.waitForExists(ONE_SECOND_IN_MS)) {
            clickView(BY_TEXT, "Overwrite");
        }
        sleep(1);
    }

    public void deleteDocument(String docName) throws Exception {
        UiObject doc = getViewByText(docName);
        doc.longClick();
        clickView(BY_TEXT, "Remove");
        UiObject deleteButton;
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
            sleepMicro(100); // in order to register as separate click
        }
    }

    public UiObject clickView(int criteria, String matching) throws Exception {
        return clickView(criteria, matching, null, false);
    }

    public UiObject clickView(int criteria, String matching, boolean wait) throws Exception {
        return clickView(criteria, matching, null, wait);
    }

    public UiObject clickView(int criteria, String matching, String clazz) throws Exception {
        return clickView(criteria, matching, clazz, false);
    }

    public UiObject clickView(int criteria, String matching, String clazz, boolean wait) throws Exception {
        UiObject view;
        switch (criteria) {
            case BY_ID:
                view =  clazz == null ? getViewById(matching) : getUiObjectByResourceId(matching, clazz);
                break;
            case BY_DESC:
                view =  clazz == null ? getViewByDesc(matching) : getUiObjectByDescription(matching, clazz);
                break;
            case BY_TEXT:
            default:
                view = clazz == null ? getViewByText(matching) : getUiObjectByText(matching, clazz);
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

    public void uiDeviceSwipeHorizontal(int startX, int endX, int height) {
        uiDeviceSwipeHorizontal(startX, endX, height, DEFAULT_SWIPE_STEPS);
    }

    public void uiDeviceSwipeHorizontal(int startX, int endX, int height, int steps) {
        getUiDevice().swipe(startX, height, endX, height, steps);
    }
}
