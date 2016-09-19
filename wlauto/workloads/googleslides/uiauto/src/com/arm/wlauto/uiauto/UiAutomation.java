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

import android.graphics.Rect;
import android.os.Bundle;
import android.os.SystemClock;

// Import the uiautomator libraries
import com.android.uiautomator.core.Configurator;
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_ID;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_TEXT;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_DESC;

public class UiAutomation extends UxPerfUiAutomation {

    public static final String ANDROID_WIDGET = "android.widget.";
    public static final String CLASS_TEXT_VIEW = ANDROID_WIDGET + "TextView";
    public static final String CLASS_IMAGE_VIEW = ANDROID_WIDGET + "ImageView";
    public static final String CLASS_BUTTON = ANDROID_WIDGET + "Button";
    public static final String CLASS_IMAGE_BUTTON = ANDROID_WIDGET + "ImageButton";
    public static final String CLASS_TABLE_ROW = ANDROID_WIDGET + "TableRow";
    public static final String CLASS_PROGRESS_BAR = ANDROID_WIDGET + "ProgressBar";
    public static final String CLASS_LIST_VIEW = ANDROID_WIDGET + "ListView";

    public static final int WAIT_TIMEOUT_1SEC = 1000;
    public static final int SLIDE_WAIT_TIME_MS = 200;
    public static final int DEFAULT_SWIPE_STEPS = 10;

    protected ActionLogger logger;
    protected String packageId;
    protected Bundle parameters;
    protected String newDocumentName;
    protected String pushedDocumentName;
    protected String workingDirectoryName;
    protected int slideCount;
    protected boolean doTextEntry;

    public void runUiAutomation() throws Exception {
        // Setup
        parameters = getParams();
        parseParams(parameters);
        setScreenOrientation(ScreenOrientation.NATURAL);
        changeAckTimeout(100);
        // UI automation begins here
        skipWelcomeScreen();
        sleep(1);
        dismissWorkOfflineBanner();
        sleep(1);
        enablePowerpointCompat();
        sleep(1);
        testEditNewSlidesDocument(newDocumentName);
        sleep(1);
        testSlideshowFromStorage(pushedDocumentName);
        // UI automation ends here
        unsetScreenOrientation();
    }

    public void parseParams(Bundle parameters) throws Exception {
        pushedDocumentName = parameters.getString("test_file").replaceAll("0space0", " ");
        newDocumentName = parameters.getString("new_doc_name").replaceAll("0space0", " ");
        slideCount = Integer.parseInt(parameters.getString("slide_count"));
        packageId = parameters.getString("package") + ":id/";
        workingDirectoryName = parameters.getString("workdir_name");
        doTextEntry = Boolean.parseBoolean(parameters.getString("do_text_entry"));
    }

    public void dismissWorkOfflineBanner() throws Exception {
        UiObject banner = new UiObject(new UiSelector().textContains("Work offline"));
        if (banner.waitForExists(WAIT_TIMEOUT_1SEC)) {
            clickUiObject(BY_TEXT, "Got it", CLASS_BUTTON);
        }
    }

    public void enterTextInSlide(String viewName, String textToEnter) throws Exception {
        UiSelector container = new UiSelector().resourceId(packageId + "main_canvas");
        UiObject view = new UiObject(container.childSelector(new UiSelector().descriptionMatches(viewName)));
        view.click();
        getUiDevice().pressEnter();
        view.setText(textToEnter);
        tapOpenArea();
        // On some devices, keyboard pops up when entering text, and takes a noticeable
        // amount of time (few milliseconds) to disappear after clicking Done.
        // In these cases, trying to find a view immediately after entering text leads
        // to an exception, so a short wait-time is added for stability.
        SystemClock.sleep(SLIDE_WAIT_TIME_MS);
    }

    public void insertSlide(String slideLayout) throws Exception {
        clickUiObject(BY_DESC, "Add slide", true);
        clickUiObject(BY_TEXT, slideLayout, true);
    }

    public void insertImage() throws Exception {
        UiObject insertButton = new UiObject(new UiSelector().descriptionContains("Insert"));
        if (insertButton.exists()) {
            insertButton.click();
        } else {
            clickUiObject(BY_DESC, "More options");
            clickUiObject(BY_TEXT, "Insert");
        }
        clickUiObject(BY_TEXT, "Image", true);
        clickUiObject(BY_TEXT, "From photos");

        UiObject imagesFolder = new UiObject(new UiSelector().className(CLASS_TEXT_VIEW).textContains("Images"));
        if (!imagesFolder.waitForExists(WAIT_TIMEOUT_1SEC*10)) {
            clickUiObject(BY_DESC, "Show roots");
        }
        imagesFolder.click();

        UiObject folderEntry = new UiObject(new UiSelector().textContains(workingDirectoryName));
        UiScrollable list = new UiScrollable(new UiSelector().scrollable(true));
        if (!folderEntry.exists() && list.waitForExists(WAIT_TIMEOUT_1SEC)) {
            list.scrollIntoView(folderEntry);
        } else {
            folderEntry.waitForExists(WAIT_TIMEOUT_1SEC*10);
        }
        folderEntry.clickAndWaitForNewWindow();
        clickUiObject(BY_ID, "com.android.documentsui:id/date", true);
    }

    public void insertShape(String shapeName) throws Exception {
        startLogger("shape_insert");
        UiObject insertButton = new UiObject(new UiSelector().descriptionContains("Insert"));
        if (insertButton.exists()) {
            insertButton.click();
        } else {
            clickUiObject(BY_DESC, "More options");
            clickUiObject(BY_TEXT, "Insert");
        }
        clickUiObject(BY_TEXT, "Shape");
        clickUiObject(BY_DESC, shapeName);
        stopLogger("shape_insert");
    }

    public void modifyShape(String shapeName) throws Exception {
        UiObject resizeHandle = new UiObject(new UiSelector().descriptionMatches(".*Bottom[- ]right resize.*"));
        Rect bounds = resizeHandle.getVisibleBounds();
        int newX = bounds.left - 40;
        int newY = bounds.bottom - 40;
        startLogger("shape_resize");
        resizeHandle.dragTo(newX, newY, 40);
        stopLogger("shape_resize");

        UiSelector container = new UiSelector().resourceId(packageId + "main_canvas");
        UiSelector shapeSelector = container.childSelector(new UiSelector().descriptionContains(shapeName));
        startLogger("shape_drag");
        new UiObject(shapeSelector).dragTo(newX, newY, 40);
        stopLogger("shape_drag");
    }

    public void openDocument(String docName) throws Exception {
        clickUiObject(BY_DESC, "Open presentation");
        clickUiObject(BY_TEXT, "Device storage", true);
        clickUiObject(BY_DESC, "Navigate up");
        UiScrollable list = new UiScrollable(new UiSelector().className(CLASS_LIST_VIEW));
        list.scrollIntoView(new UiSelector().textMatches(workingDirectoryName));
        clickUiObject(BY_TEXT, workingDirectoryName);
        list.scrollIntoView(new UiSelector().textContains(docName));
        startLogger("document_open");
        clickUiObject(BY_TEXT, docName);
        clickUiObject(BY_TEXT, "Open", CLASS_BUTTON, true);
        stopLogger("document_open");
    }

    public void newDocument() throws Exception {
        startLogger("document_new");
        clickUiObject(BY_DESC, "New presentation");
        clickUiObject(BY_TEXT, "New PowerPoint", true);
        stopLogger("document_new");
    }

    public void saveDocument(String docName) throws Exception {
        UiObject saveActionButton = new UiObject(new UiSelector().resourceId(packageId + "action"));
        UiObject unsavedIndicator = new UiObject(new UiSelector().textContains("Not saved"));
        startLogger("document_save");
        if (saveActionButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            saveActionButton.click();
        } else if (unsavedIndicator.waitForExists(WAIT_TIMEOUT_1SEC)) {
            unsavedIndicator.click();
        }
        clickUiObject(BY_TEXT, "Device");
        UiObject save = clickUiObject(BY_TEXT, "Save", CLASS_BUTTON);
        if (save.waitForExists(WAIT_TIMEOUT_1SEC)) {
            save.click();
        }
        stopLogger("document_save");

        // Overwrite if prompted
        // Should not happen under normal circumstances. But ensures test doesn't stop
        // if a previous iteration failed prematurely and was unable to delete the file.
        // Note that this file isn't removed during workload teardown as deleting it is
        // part of the UiAutomator test case.
        UiObject overwriteView = new UiObject(new UiSelector().textContains("already exists"));
        if (overwriteView.waitForExists(WAIT_TIMEOUT_1SEC)) {
            clickUiObject(BY_TEXT, "Overwrite");
        }
    }

    public void deleteDocument(String docName) throws Exception {
        String filenameRegex = String.format(".*((%s)|([Uu]ntitled presentation)).pptx.*", docName);
        UiObject doc = new UiObject(new UiSelector().textMatches(filenameRegex));
        UiObject moreActions = doc.getFromParent(new UiSelector().descriptionContains("More actions"));
        startLogger("document_delete");
        moreActions.click();

        UiObject deleteButton = new UiObject(new UiSelector().textMatches(".*([Dd]elete|[Rr]emove).*"));
        if (deleteButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            deleteButton.click();
        } else {
            // Delete button not found, try to scroll the view
            UiScrollable scrollable = new UiScrollable(new UiSelector().scrollable(true)
                    .childSelector(new UiSelector().textContains("Rename")));
            if (scrollable.exists()) {
                scrollable.scrollIntoView(deleteButton);
            } else {
                UiObject content = new UiObject(new UiSelector().resourceId(packageId + "content"));
                int attemptsLeft = 10; // try a maximum of 10 swipe attempts
                while (!deleteButton.exists() && attemptsLeft > 0) {
                    content.swipeUp(DEFAULT_SWIPE_STEPS);
                    attemptsLeft--;
                }
            }
            deleteButton.click();
        }

        UiObject okButton = new UiObject(new UiSelector().className(CLASS_BUTTON).textContains("OK"));
        if (okButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            okButton.clickAndWaitForNewWindow();
        } else {
            clickUiObject(BY_TEXT, "Remove", CLASS_BUTTON, true);
        }
        stopLogger("document_delete");
    }


    protected void skipWelcomeScreen() throws Exception {
        clickUiObject(BY_TEXT, "Skip", true);
    }

    protected void enablePowerpointCompat() throws Exception {
        startLogger("enable_pptmode");
        clickUiObject(BY_DESC, "drawer");
        clickUiObject(BY_TEXT, "Settings", true);
        clickUiObject(BY_TEXT, "Create PowerPoint");
        getUiDevice().pressBack();
        stopLogger("enable_pptmode");
    }

    protected void testEditNewSlidesDocument(String docName) throws Exception {
        // Init
        newDocument();
        waitForProgress(WAIT_TIMEOUT_1SEC * 30);

        // Slide 1 - Text
        if (doTextEntry) {
            enterTextInSlide(".*[Tt]itle.*", docName);
            // Save
            saveDocument(docName);
            sleep(1);
        }

        // Slide 2 - Image
        insertSlide("Title only");
        insertImage();
        sleep(1);

        // If text wasn't entered in first slide, save prompt will appear here
        if (!doTextEntry) {
            // Save
            saveDocument(docName);
            sleep(1);
        }

        // Slide 3 - Shape
        insertSlide("Title slide");
        String shapeName = "Rounded rectangle";
        insertShape(shapeName);
        modifyShape(shapeName);
        getUiDevice().pressBack();
        sleep(1);

        // Tidy up
        getUiDevice().pressBack();
        dismissWorkOfflineBanner(); // if it appears on the homescreen

        // Note: Currently disabled because it fails on Samsung devices
        // deleteDocument(docName);
    }

    protected void testSlideshowFromStorage(String docName) throws Exception {
        // Open document
        openDocument(docName);
        waitForProgress(WAIT_TIMEOUT_1SEC*30);

        // Begin Slide show test

        // Note: Using coordinates slightly offset from the slide edges avoids accidentally
        // selecting any shapes or text boxes inside the slides while swiping, which may
        // cause the view to switch into edit mode and fail the test
        UiObject slideCanvas = new UiObject(new UiSelector().resourceId(packageId + "main_canvas"));
        Rect canvasBounds = slideCanvas.getVisibleBounds();
        int leftEdge = canvasBounds.left + 10;
        int rightEdge = canvasBounds.right - 10;
        int yCoordinate = canvasBounds.top + 5;
        int slideIndex = 0;

        // scroll forward in edit mode
        startLogger("slideshow_editforward");
        while (slideIndex++ < slideCount) {
            uiDeviceSwipeHorizontal(rightEdge, leftEdge, yCoordinate, DEFAULT_SWIPE_STEPS);
            waitForProgress(WAIT_TIMEOUT_1SEC*5);
        }
        stopLogger("slideshow_editforward");
        sleep(1);

        // scroll backward in edit mode
        startLogger("slideshow_editbackward");
        while (slideIndex-- > 0) {
            uiDeviceSwipeHorizontal(leftEdge, rightEdge, yCoordinate, DEFAULT_SWIPE_STEPS);
            waitForProgress(WAIT_TIMEOUT_1SEC*5);
        }
        stopLogger("slideshow_editbackward");
        sleep(1);

        // run slideshow
        startLogger("slideshow_run");
        clickUiObject(BY_DESC, "Start slideshow", true);
        UiObject onDevice = new UiObject(new UiSelector().textContains("this device"));
        if (onDevice.waitForExists(WAIT_TIMEOUT_1SEC)) {
            onDevice.clickAndWaitForNewWindow();
            waitForProgress(WAIT_TIMEOUT_1SEC*30);
            UiObject presentation = new UiObject(new UiSelector().descriptionContains("Presentation Viewer"));
            presentation.waitForExists(WAIT_TIMEOUT_1SEC*30);
        }
        stopLogger("slideshow_run");
        sleep(1);

        slideIndex = 0;
        
        // scroll forward in slideshow mode
        startLogger("slideshow_playforward");
        while (slideIndex++ < slideCount) {
            uiDeviceSwipeHorizontal(rightEdge, leftEdge, yCoordinate, DEFAULT_SWIPE_STEPS);
            waitForProgress(WAIT_TIMEOUT_1SEC*5);
        }
        stopLogger("slideshow_playforward");
        sleep(1);

        // scroll backward in slideshow mode
        startLogger("slideshow_playbackward");
        while (slideIndex-- > 0) {
            uiDeviceSwipeHorizontal(leftEdge, rightEdge, yCoordinate, DEFAULT_SWIPE_STEPS);
            waitForProgress(WAIT_TIMEOUT_1SEC*5);
        }
        stopLogger("slideshow_playbackward");
        sleep(1);

        getUiDevice().pressBack();
        getUiDevice().pressBack();
    }

    protected void startLogger(String name) throws Exception {
        logger = new ActionLogger(name, parameters);
        logger.start();
    }

    protected void stopLogger(String name) throws Exception {
        logger.stop();
    }

    protected boolean waitForProgress(int timeout) throws Exception {
        UiObject progress = new UiObject(new UiSelector().className(CLASS_PROGRESS_BAR));
        if (progress.waitForExists(WAIT_TIMEOUT_1SEC)) {
            return progress.waitUntilGone(timeout);
        } else {
            return false;
        }
    }

    private long changeAckTimeout(long newTimeout) {
        Configurator config = Configurator.getInstance();
        long oldTimeout = config.getActionAcknowledgmentTimeout();
        config.setActionAcknowledgmentTimeout(newTimeout);
        return oldTimeout;
    }

    private void tapOpenArea() throws Exception {
        UiObject openArea = getUiObjectByResourceId(packageId + "punch_view_pager");
        Rect bounds = openArea.getVisibleBounds();
        // 10px from top of view, 10px from the right edge
        tapDisplay(bounds.right - 10, bounds.top + 10);
    }

}
