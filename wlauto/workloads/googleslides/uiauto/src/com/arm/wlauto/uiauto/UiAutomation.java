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

import android.os.Bundle;
import android.os.SystemClock;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import static com.arm.wlauto.uiauto.googleslides.UiAutomation.FindByCriteria.BY_ID;
import static com.arm.wlauto.uiauto.googleslides.UiAutomation.FindByCriteria.BY_TEXT;
import static com.arm.wlauto.uiauto.googleslides.UiAutomation.FindByCriteria.BY_DESC;

public class UiAutomation extends UxPerfUiAutomation {

    public static final String TAG = "googleslides";
    public static final String PACKAGE = "com.google.android.apps.docs.editors.slides";
    public static final String PACKAGE_ID = PACKAGE + ":id/";
    public static final String ACTIVITY_DOCLIST = "com.google.android.apps.docs.app.DocListActivity";
    public static final String ACTIVITY_SLIDES = "com.qo.android.quickpoint.Quickpoint";
    public static final String ACTIVITY_SETTINGS = "com.google.android.apps.docs.app.DocsPreferencesActivity";

    public static final String CLASS_TEXT_VIEW = "android.widget.TextView";
    public static final String CLASS_IMAGE_VIEW = "android.widget.ImageView";
    public static final String CLASS_BUTTON = "android.widget.Button";
    public static final String CLASS_IMAGE_BUTTON = "android.widget.ImageButton";
    public static final String CLASS_TABLE_ROW = "android.widget.TableRow";

    public enum FindByCriteria {
        BY_ID, BY_TEXT, BY_DESC;
    }

    public static final int DIALOG_WAIT_TIME_MS = 3000;
    public static final int SLIDE_WAIT_TIME_MS = 200;
    public static final int CLICK_REPEAT_INTERVAL_MS = 50;
    public static final int DEFAULT_SWIPE_STEPS = 10;

    public static final String NEW_DOC_FILENAME = "UX Perf Slides";

    public static final String SLIDE_TEXT_CONTENT =
        "class Workload(Extension):\n\tname = None\n\tdef init_resources(self, context):\n\t\tpass\n"
        + "\tdef validate(self):\n\t\tpass\n\tdef initialize(self, context):\n\t\tpass\n"
        + "\tdef setup(self, context):\n\t\tpass\n\tdef setup(self, context):\n\t\tpass\n"
        + "\tdef run(self, context):\n\t\tpass\n\tdef update_result(self, context):\n\t\tpass\n"
        + "\tdef teardown(self, context):\n\t\tpass\n\tdef finalize(self, context):\n\t\tpass\n";

    protected Map<String, Timer> results = new LinkedHashMap<String, Timer>();
    protected Timer timer = new Timer();

    protected Bundle parameters;
    protected boolean dumpsysEnabled;
    protected String outputDir;
    protected String localFile;
    protected int slideCount;
    protected boolean useLocalFile;

    public void parseParams(Bundle parameters) throws Exception {
        dumpsysEnabled = Boolean.parseBoolean(parameters.getString("dumpsys_enabled"));
        outputDir = parameters.getString("output_dir");
        localFile = parameters.getString("local_file");
        useLocalFile = localFile != null;
        if (useLocalFile) {
            slideCount = Integer.parseInt(parameters.getString("slide_count"));
        }
    }

    public void runUiAutomation() throws Exception {
        parameters = getParams();
        parseParams(parameters);
        skipWelcomeScreen();
        openAndCloseDrawer();
        enablePowerpointCompat();
        if (useLocalFile) {
            testSlideshowFromStorage(localFile);
        } else {
            testEditNewSlidesDocument(NEW_DOC_FILENAME);
        }
        writeResultsToFile(results, parameters.getString("results_file"));
    }

    protected void skipWelcomeScreen() throws Exception {
        timer = new Timer();
        timer.start();
        clickView(BY_TEXT, "Skip", true);
        timer.end();
        results.put("skip_welcome", timer);
        sleep(1);
    }

    protected void openAndCloseDrawer() throws Exception {
        startDumpsys(ACTIVITY_DOCLIST);
        timer = new Timer();
        timer.start();
        clickView(BY_DESC, "drawer");
        getUiDevice().pressBack();
        timer.end();
        results.put("open_drawer", timer);
        endDumpsys(ACTIVITY_DOCLIST, "open_drawer");
        sleep(1);
    }

    protected void enablePowerpointCompat() throws Exception {
        startDumpsys(ACTIVITY_SETTINGS);
        timer = new Timer();
        timer.start();
        clickView(BY_DESC, "drawer");
        clickView(BY_TEXT, "Settings", true);
        clickView(BY_TEXT, "Create PowerPoint");
        getUiDevice().pressBack();
        timer.end();
        results.put("enable_ppt_compat", timer);
        endDumpsys(ACTIVITY_SETTINGS, "enable_ppt_compat");
        sleep(1);
    }

    protected void testSlideshowFromStorage(String docName) throws Exception {
        // Sometimes docs deleted in __init__.py falsely appear on the app's home
        // For robustness, it's nice to remove these placeholders
        // However, the test should not crash because of it, so a silent catch is used
        UiObject docView = new UiObject(new UiSelector().textContains(docName));
        if (docView.waitForExists(1000)) {
            try {
                deleteDocument(docName);
            } catch (Exception e) {
                // do nothing
            }
        }

        // Open document
        timer = new Timer();
        timer.start();
        clickView(BY_DESC, "Open presentation");
        clickView(BY_TEXT, "Device storage", true);
        timer.end();
        results.put("open_file_picker", timer);

        // Scroll through document list if necessary
        UiScrollable list = new UiScrollable(new UiSelector().className("android.widget.ListView"));
        list.scrollIntoView(new UiSelector().textContains(docName));
        timer = new Timer();
        timer.start();
        clickView(BY_TEXT, docName);
        clickView(BY_TEXT, "Open", CLASS_BUTTON, true);
        timer.end();
        results.put("open_document", timer);
        sleep(5);

        // Begin Slide show test
        // Note: A short wait-time is introduced before transition to the next slide to simulate
        // a real user's behaviour. Otherwise the test swipes through the slides too quickly.
        // These waits are not measured in the per-slide timings, and introduce a systematic
        // error in the overall slideshow timings.
        int centerY = getUiDevice().getDisplayHeight() / 2;
        int centerX = getUiDevice().getDisplayWidth() / 2;
        int slideIndex = 0;
        String testTag;
        Timer slideTimer;

        // scroll forward in edit mode
        startDumpsys(ACTIVITY_SLIDES);
        timer = new Timer();
        timer.start();
        while (++slideIndex < slideCount) {
            testTag = "slides_next_" + slideIndex;
            startDumpsys(ACTIVITY_SLIDES);
            slideTimer = new Timer();
            slideTimer.start();
            uiDeviceSwipeHorizontal(centerX + centerX/2, centerX - centerX/2, centerY);
            slideTimer.end();
            results.put(testTag, slideTimer);
            endDumpsys(ACTIVITY_SLIDES, testTag);
            SystemClock.sleep(SLIDE_WAIT_TIME_MS);
        }
        timer.end();
        results.put("slides_forward", timer);
        endDumpsys(ACTIVITY_SLIDES, "slides_forward");
        sleep(1);

        // scroll backward in edit mode
        startDumpsys(ACTIVITY_SLIDES);
        timer = new Timer();
        timer.start();
        while (--slideIndex > 0) {
            testTag = "slides_previous_" + slideIndex;
            startDumpsys(ACTIVITY_SLIDES);
            slideTimer = new Timer();
            slideTimer.start();
            uiDeviceSwipeHorizontal(centerX - centerX/2, centerX + centerX/2, centerY);
            slideTimer.end();
            results.put(testTag, slideTimer);
            endDumpsys(ACTIVITY_SLIDES, testTag);
            SystemClock.sleep(SLIDE_WAIT_TIME_MS);
        }
        timer.end();
        results.put("slides_reverse", timer);
        endDumpsys(ACTIVITY_SLIDES, "slides_reverse");
        sleep(1);

        // scroll forward in slideshow mode
        timer = new Timer();
        timer.start();
        clickView(BY_DESC, "Start slideshow", true);
        timer.end();
        results.put("open_slideshow", timer);

        startDumpsys(ACTIVITY_SLIDES);
        timer = new Timer();
        timer.start();
        while (++slideIndex < slideCount) {
            testTag = "slideshow_next_" + slideIndex;
            startDumpsys(ACTIVITY_SLIDES);
            slideTimer = new Timer();
            slideTimer.start();
            uiDeviceSwipeHorizontal(centerX + centerX/2, centerX - centerX/2, centerY);
            slideTimer.end();
            results.put(testTag, slideTimer);
            endDumpsys(ACTIVITY_SLIDES, testTag);
            SystemClock.sleep(SLIDE_WAIT_TIME_MS);
        }
        timer.end();
        results.put("play_slideshow", timer);
        endDumpsys(ACTIVITY_SLIDES, "play_slideshow");
        sleep(1);

        getUiDevice().pressBack();
        getUiDevice().pressBack();
    }

    protected void testEditNewSlidesDocument(String docName) throws Exception {
        startDumpsys(ACTIVITY_DOCLIST);
        // create new file
        timer = new Timer();
        timer.start();
        clickView(BY_DESC, "New presentation");
        clickView(BY_TEXT, "New PowerPoint", true);
        timer.end();
        results.put("create_document", timer);
        endDumpsys(ACTIVITY_DOCLIST, "create_document");

        // first slide
        enterTextInSlide("Title", "WORKLOAD AUTOMATION");
        enterTextInSlide("Subtitle", "Measuring perfomance of different productivity apps on Android OS");
        saveDocument(docName);

        insertSlide("Title and Content");
        enterTextInSlide("title", "Extensions - Workloads");
        enterTextInSlide("Text placeholder", SLIDE_TEXT_CONTENT);
        clickView(BY_DESC, "Text placeholder");
        clickView(BY_DESC, "Format");
        clickView(BY_TEXT, "Droid Sans");
        clickView(BY_TEXT, "Droid Sans Mono");
        clickView(BY_ID, PACKAGE_ID + "palette_back_button");
        UiObject decreaseFont = getViewByDesc("Decrease text");
        repeatClickView(decreaseFont, 20);
        getUiDevice().pressBack();

        // get image from gallery and insert
        // To keep the test simple just select the most recent image regardless of what
        // folder it's in. More reliable than trying to find a pushed image in the file
        // picker, and fails gracefully in the rare case that no images exist.
        insertSlide("Title Only");
        clickView(BY_DESC, "Insert");
        clickView(BY_TEXT, "Image", true);
        clickView(BY_TEXT, "Recent");
        try {
            UiObject image = new UiObject(new UiSelector().resourceId("com.android.documentsui:id/date").instance(2));
            image.clickAndWaitForNewWindow();
        } catch (UiObjectNotFoundException e) {
            clickView(BY_ID, "com.android.documentsui:id/date", true);
        }

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
        sleep(1); // a bit of time to see previous slide
        UiObject view = getViewByDesc("Insert slide");
        view.clickAndWaitForNewWindow();
        view = getViewByText(slideLayout);
        view.clickAndWaitForNewWindow();
    }

    public void enterTextInSlide(String viewName, String textToEnter) throws Exception {
        UiObject view = getViewByDesc(viewName);
        view.click();
        view.setText(textToEnter);
        try {
            clickView(BY_DESC, "Done");
        } catch (UiObjectNotFoundException e) {
            clickView(BY_ID, "android:id/action_mode_close_button");
        }
        // On some devices, keyboard pops up when entering text, and takes a noticeable
        // amount of time (few milliseconds) to disappear after clicking Done.
        // In these cases, trying to find a view immediately after entering text leads
        // to an exception, so a short wait-time is added for stability.
        SystemClock.sleep(SLIDE_WAIT_TIME_MS);
    }

    public void saveDocument(String docName) throws Exception {
        timer = new Timer();
        timer.start();
        clickView(BY_TEXT, "SAVE");
        clickView(BY_TEXT, "Device");
        timer.end();
        results.put("save_dialog_1", timer);

        timer = new Timer();
        timer.start();
        UiObject filename = getViewById(PACKAGE_ID + "file_name_edit_text");
        filename.clearTextField();
        filename.setText(docName);
        clickView(BY_TEXT, "Save", CLASS_BUTTON);
        timer.end();
        results.put("save_dialog_2", timer);

        // Overwrite if prompted
        // Should not happen under normal circumstances. But ensures test doesn't stop
        // if a previous iteration failed prematurely and was unable to delete the file.
        // Note that this file isn't removed during workload teardown as deleting it is
        // part of the UiAutomator test case.
        UiObject overwriteView = new UiObject(new UiSelector().textContains("already exists"));
        if (overwriteView.waitForExists(DIALOG_WAIT_TIME_MS)) {
            clickView(BY_TEXT, "Overwrite");
        }
        sleep(1);
    }

    public void deleteDocument(String docName) throws Exception {
        timer = new Timer();
        timer.start();
        UiObject doc = getViewByText(docName);
        doc.longClick();
        clickView(BY_TEXT, "Remove");
        timer.end();
        results.put("delete_dialog_1", timer);

        timer = new Timer();
        timer.start();
        UiObject deleteButton;
        try {
            deleteButton = getUiObjectByText("Remove", CLASS_BUTTON);
        } catch (UiObjectNotFoundException e) {
            deleteButton = getUiObjectByText("Ok", CLASS_BUTTON);
        }
        deleteButton.clickAndWaitForNewWindow();
        timer.end();
        results.put("delete_dialog_2", timer);
        sleep(1);
    }

    public void repeatClickView(UiObject view, int repeat) throws Exception {
        if (repeat < 1 || !view.isClickable()) return;
        while (repeat-- > 0) {
            view.click();
            SystemClock.sleep(CLICK_REPEAT_INTERVAL_MS); // in order to register as separate click
        }
    }

    public UiObject clickView(FindByCriteria criteria, String matching) throws Exception {
        return clickView(criteria, matching, null, false);
    }

    public UiObject clickView(FindByCriteria criteria, String matching, boolean wait) throws Exception {
        return clickView(criteria, matching, null, wait);
    }

    public UiObject clickView(FindByCriteria criteria, String matching, String clazz) throws Exception {
        return clickView(criteria, matching, clazz, false);
    }

    public UiObject clickView(FindByCriteria criteria, String matching, String clazz, boolean wait) throws Exception {
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

    public void startDumpsys(String viewName) throws Exception {
        if (!dumpsysEnabled)
            return;
        initDumpsysSurfaceFlinger(PACKAGE);
        initDumpsysGfxInfo(PACKAGE);
    }

    public void endDumpsys(String viewName, String testTag) throws Exception {
        if (!dumpsysEnabled)
            return;
        String dumpsysTag = TAG + "_" + testTag;
        exitDumpsysSurfaceFlinger(PACKAGE, new File(outputDir, dumpsysTag + "_surfFlinger.log"));
        exitDumpsysGfxInfo(PACKAGE, new File(outputDir, dumpsysTag + "_gfxInfo.log"));
    }
}
