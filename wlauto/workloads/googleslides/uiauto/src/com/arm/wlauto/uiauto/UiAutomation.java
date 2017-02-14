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

    public Bundle parameters;
    public String packageName;
    public String packageID;

    public static final int WAIT_TIMEOUT_1SEC = 1000;
    public static final int SLIDE_WAIT_TIME_MS = 200;
    public static final int DEFAULT_SWIPE_STEPS = 10;

    public void runUiAutomation() throws Exception {
        parameters = getParams();
        packageName = parameters.getString("package");
        packageID = packageName + ":id/";

        String newDocumentName = parameters.getString("new_doc_name").replace("0space0", " ");
        String pushedDocumentName = parameters.getString("test_file").replace("0space0", " ");
        int slideCount = Integer.parseInt(parameters.getString("slide_count"));
        boolean doTextEntry = Boolean.parseBoolean(parameters.getString("do_text_entry"));
        String workingDirectoryName = parameters.getString("workdir_name");

        setScreenOrientation(ScreenOrientation.NATURAL);
        changeAckTimeout(100);
        // UI automation begins here
        skipWelcomeScreen();
        sleep(1);
		dismissUpdateDialog();
		sleep(1);
        dismissWorkOfflineBanner();
        sleep(1);
        enablePowerpointCompat();
        sleep(1);
        testEditNewSlidesDocument(newDocumentName, workingDirectoryName, doTextEntry);
        sleep(1);
        // Open document
        openDocument(pushedDocumentName, workingDirectoryName);
        waitForProgress(WAIT_TIMEOUT_1SEC*30);
        testSlideshowFromStorage(slideCount);
        // UI automation ends here
        unsetScreenOrientation();
    }

    public void dismissWorkOfflineBanner() throws Exception {
        UiObject banner =
            new UiObject(new UiSelector().textContains("Work offline"));
        if (banner.waitForExists(WAIT_TIMEOUT_1SEC)) {
            clickUiObject(BY_TEXT, "Got it", "android.widget.Button");
        }
    }
	
	public void dismissUpdateDialog() throws Exception {
		UiObject update = 
			new UiObject(new UiSelector().textContains("App update recommended"));
		if (update.waitForExists(WAIT_TIMEOUT_1SEC)) {
			UiObject dismiss =
			    new UiObject(new UiSelector().textContains("Dismiss"));
			dismiss.click();			
		}
	}

    public void enterTextInSlide(String viewName, String textToEnter) throws Exception {
        UiObject view =
            new UiObject(new UiSelector().resourceId(packageID + "main_canvas")
                                         .childSelector(new UiSelector()
                                         .descriptionMatches(viewName)));
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

    public void insertImage(String workingDirectoryName) throws Exception {
        UiObject insertButton = new UiObject(new UiSelector().descriptionContains("Insert"));
        if (insertButton.exists()) {
            insertButton.click();
        } else {
            clickUiObject(BY_DESC, "More options");
            clickUiObject(BY_TEXT, "Insert");
        }
        clickUiObject(BY_TEXT, "Image", true);
        clickUiObject(BY_TEXT, "From photos");

        UiObject imagesFolder = new UiObject(new UiSelector().className("android.widget.TextView").textContains("Images"));
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
        String testTag = "shape_insert";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        UiObject insertButton =
            new UiObject(new UiSelector().descriptionContains("Insert"));
        logger.start();
        if (insertButton.exists()) {
            insertButton.click();
        } else {
            clickUiObject(BY_DESC, "More options");
            clickUiObject(BY_TEXT, "Insert");
        }
        clickUiObject(BY_TEXT, "Shape");
        clickUiObject(BY_DESC, shapeName);
        logger.stop();
    }

    public void modifyShape(String shapeName) throws Exception {
        String testTag = "shape_resize";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        UiObject resizeHandle =
            new UiObject(new UiSelector().descriptionMatches(".*Bottom[- ]right resize.*"));
        Rect bounds = resizeHandle.getVisibleBounds();
        int newX = bounds.left - 40;
        int newY = bounds.bottom - 40;
        logger.start();
        resizeHandle.dragTo(newX, newY, 40);
        logger.stop();

        testTag = "shape_drag";
        logger = new ActionLogger(testTag, parameters);

        UiObject shapeSelector =
            new UiObject(new UiSelector().resourceId(packageID + "main_canvas")
                                         .childSelector(new UiSelector()
                                         .descriptionContains(shapeName)));
        logger.start();
        shapeSelector.dragTo(newX, newY, 40);
        logger.stop();
    }

    public void openDocument(String docName, String workingDirectoryName) throws Exception {
        String testTag = "document_open";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        clickUiObject(BY_DESC, "Open presentation");
        clickUiObject(BY_TEXT, "Device storage", true);
        clickUiObject(BY_DESC, "Navigate up");
        UiScrollable list =
            new UiScrollable(new UiSelector().className("android.widget.ListView"));
        list.scrollIntoView(new UiSelector().textMatches(workingDirectoryName));
        clickUiObject(BY_TEXT, workingDirectoryName);
        list.scrollIntoView(new UiSelector().textContains(docName));

        logger.start();
        clickUiObject(BY_TEXT, docName);
        clickUiObject(BY_TEXT, "Open", "android.widget.Button", true);
        logger.stop();
    }

    public void newDocument() throws Exception {
        String testTag = "document_new";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        logger.start();
        clickUiObject(BY_DESC, "New presentation");
        clickUiObject(BY_TEXT, "New PowerPoint", true);
		dismissUpdateDialog();
        logger.stop();
    }

    public void saveDocument(String docName) throws Exception {
        String testTag = "document_save";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        UiObject saveActionButton =
            new UiObject(new UiSelector().text("save"));
        UiObject unsavedIndicator =
            new UiObject(new UiSelector().textContains("Unsaved changes"));
        logger.start();
        if (saveActionButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            saveActionButton.click();
        } else if (unsavedIndicator.waitForExists(WAIT_TIMEOUT_1SEC)) {
            unsavedIndicator.click();
        }
        clickUiObject(BY_TEXT, "Device");
        UiObject save = clickUiObject(BY_TEXT, "Save", "android.widget.Button");
        if (save.waitForExists(WAIT_TIMEOUT_1SEC)) {
            save.click();
        }
        logger.stop();

        // Overwrite if prompted
        // Should not happen under normal circumstances. But ensures test doesn't stop
        // if a previous iteration failed prematurely and was unable to delete the file.
        // Note that this file isn't removed during workload teardown as deleting it is
        // part of the UiAutomator test case.
        UiObject overwriteView =
            new UiObject(new UiSelector().textContains("already exists"));
        if (overwriteView.waitForExists(WAIT_TIMEOUT_1SEC)) {
            clickUiObject(BY_TEXT, "Overwrite");
        }
    }

    public void deleteDocument(String docName) throws Exception {
        String testTag = "document_delete";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        String filenameRegex = String.format(".*((%s)|([Uu]ntitled presentation)).pptx.*", docName);
        UiObject doc =
            new UiObject(new UiSelector().textMatches(filenameRegex));
        UiObject moreActions =
            doc.getFromParent(new UiSelector().descriptionContains("More actions"));
        
        logger.start();
        moreActions.click();

        UiObject deleteButton =
            new UiObject(new UiSelector().textMatches(".*([Dd]elete|[Rr]emove).*"));
        if (deleteButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            deleteButton.click();
        } else {
            // Delete button not found, try to scroll the view
            UiScrollable scrollable =
                new UiScrollable(new UiSelector().scrollable(true)
                                                 .childSelector(new UiSelector()
                                                 .textContains("Rename")));
            if (scrollable.exists()) {
                scrollable.scrollIntoView(deleteButton);
            } else {
                UiObject content =
                    new UiObject(new UiSelector().resourceId(packageID + "content"));
                int attemptsLeft = 10; // try a maximum of 10 swipe attempts
                while (!deleteButton.exists() && attemptsLeft > 0) {
                    content.swipeUp(DEFAULT_SWIPE_STEPS);
                    attemptsLeft--;
                }
            }
            deleteButton.click();
        }

        UiObject okButton =
            new UiObject(new UiSelector().textContains("OK")
                                         .className("android.widget.Button"));
        if (okButton.waitForExists(WAIT_TIMEOUT_1SEC)) {
            okButton.clickAndWaitForNewWindow();
        } else {
            clickUiObject(BY_TEXT, "Remove", "android.widget.Button", true);
        }
        logger.stop();
    }

    protected void skipWelcomeScreen() throws Exception {
        clickUiObject(BY_TEXT, "Skip", true);
    }

    protected void enablePowerpointCompat() throws Exception {
        String testTag = "enable_pptmode";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        logger.start();
        clickUiObject(BY_DESC, "drawer");
        clickUiObject(BY_TEXT, "Settings", true);
        clickUiObject(BY_TEXT, "Create PowerPoint");
        getUiDevice().pressBack();
        logger.stop();
    }

    protected void testEditNewSlidesDocument(String docName, String workingDirectoryName, boolean doTextEntry) throws Exception {
        // Init
        newDocument();
        waitForProgress(WAIT_TIMEOUT_1SEC * 30);

        // Slide 1 - Text
        if (doTextEntry) {
            enterTextInSlide(".*[Tt]itle.*", docName);
            windowApplication();
            // Save
            saveDocument(docName);
            sleep(1);
        }

        // Slide 2 - Image
        insertSlide("Title only");
        insertImage(workingDirectoryName);
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

    protected void testSlideshowFromStorage(int slideCount) throws Exception {
        String testTag = "slideshow";
        // Begin Slide show test

        // Note: Using coordinates slightly offset from the slide edges avoids accidentally
        // selecting any shapes or text boxes inside the slides while swiping, which may
        // cause the view to switch into edit mode and fail the test
        UiObject slideCanvas =
            new UiObject(new UiSelector().resourceId(packageID + "main_canvas"));
        Rect canvasBounds = slideCanvas.getVisibleBounds();
        int leftEdge = canvasBounds.left + 10;
        int rightEdge = canvasBounds.right - 10;
        int yCoordinate = canvasBounds.top + 5;
        int slideIndex = 0;

        // scroll forward in edit mode
        ActionLogger logger = new ActionLogger(testTag + "_editforward", parameters);
        logger.start();
        while (slideIndex++ < slideCount) {
            uiDeviceSwipeHorizontal(rightEdge, leftEdge, yCoordinate, DEFAULT_SWIPE_STEPS);
            waitForProgress(WAIT_TIMEOUT_1SEC*5);
        }
        logger.stop();
        sleep(1);

        // scroll backward in edit mode
        logger = new ActionLogger(testTag + "_editbackward", parameters);
        logger.start();
        while (slideIndex-- > 0) {
            uiDeviceSwipeHorizontal(leftEdge, rightEdge, yCoordinate, DEFAULT_SWIPE_STEPS);
            waitForProgress(WAIT_TIMEOUT_1SEC*5);
        }
        logger.stop();
        sleep(1);

        // run slideshow
        logger = new ActionLogger(testTag + "_run", parameters);
        logger.start();
        clickUiObject(BY_DESC, "Start slideshow", true);
        UiObject onDevice =
            new UiObject(new UiSelector().textContains("this device"));
        if (onDevice.waitForExists(WAIT_TIMEOUT_1SEC)) {
            onDevice.clickAndWaitForNewWindow();
            waitForProgress(WAIT_TIMEOUT_1SEC*30);
            UiObject presentation =
                new UiObject(new UiSelector().descriptionContains("Presentation Viewer"));
            presentation.waitForExists(WAIT_TIMEOUT_1SEC*30);
        }
        logger.stop();
        sleep(1);

        slideIndex = 0;
        
        // scroll forward in slideshow mode
        logger = new ActionLogger(testTag + "_playforward", parameters);
        logger.start();
        while (slideIndex++ < slideCount) {
            uiDeviceSwipeHorizontal(rightEdge, leftEdge, yCoordinate, DEFAULT_SWIPE_STEPS);
            waitForProgress(WAIT_TIMEOUT_1SEC*5);
        }
        logger.stop();
        sleep(1);

        // scroll backward in slideshow mode
        logger = new ActionLogger(testTag + "_playbackward", parameters);
        logger.start();
        while (slideIndex-- > 0) {
            uiDeviceSwipeHorizontal(leftEdge, rightEdge, yCoordinate, DEFAULT_SWIPE_STEPS);
            waitForProgress(WAIT_TIMEOUT_1SEC*5);
        }
        logger.stop();
        sleep(1);

        getUiDevice().pressBack();
        getUiDevice().pressBack();
    }

    protected boolean waitForProgress(int timeout) throws Exception {
        UiObject progress = new UiObject(new UiSelector().className("android.widget.ProgressBar"));
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
        UiObject openArea = getUiObjectByResourceId(packageID + "punch_view_pager");
        Rect bounds = openArea.getVisibleBounds();
        // 10px from top of view, 10px from the right edge
    }

    public void windowApplication() throws Exception {
        UiObject window =
                new UiObject(new UiSelector().resourceId("android:id/restore_window"));
        if (window.waitForExists(WAIT_TIMEOUT_1SEC)){
            window.click();
        }
    }
}
