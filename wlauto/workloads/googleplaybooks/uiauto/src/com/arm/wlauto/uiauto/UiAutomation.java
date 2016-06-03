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

package com.arm.wlauto.uiauto.googleplaybooks;

import android.os.Bundle;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.util.concurrent.TimeUnit;
import java.util.LinkedHashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Map.Entry;

public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "uxperf_googleplaybooks";

    public Bundle parameters;
    private int viewTimeoutSecs = 10;
    private long viewTimeout =  TimeUnit.SECONDS.toMillis(viewTimeoutSecs);
    private LinkedHashMap<String, Timer> timingResults = new LinkedHashMap<String, Timer>();

    public void runUiAutomation() throws Exception {
        this.timeout = TimeUnit.SECONDS.toMillis(8);

        parameters = getParams();

        String bookTitle = parameters.getString("book_title").replace("_", " ");
        String searchWord = parameters.getString("search_word");
        String noteText = "This is a test note";

        setScreenOrientation(ScreenOrientation.NATURAL);
        clearFirstRunDialogues();
        dismissSync();

        openMyLibrary();
        searchForBook(bookTitle);

        selectBook(0); // Select the first book
        gesturesTest();
        selectRandomChapter();
        addNote(noteText);
        removeNote();
        searchForWord(searchWord);
        switchPageStyles();
        aboutBook();

        pressBack();
        unsetScreenOrientation();

        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    private void dismissSync() throws Exception {
        UiObject keepSyncOff =
            new UiObject(new UiSelector().textContains("Keep sync off")
                                         .className("android.widget.Button"));
        if (keepSyncOff.exists()) {
            keepSyncOff.click();
        }
    }

    // If there is no sample book in My library we must choose a book the first
    // time application is run
    private void clearFirstRunDialogues() throws Exception {
        UiObject endButton =
            new UiObject(new UiSelector().resourceId("com.google.android.apps.books:id/end_button"));

        // Click next button if it exists
        if (endButton.exists()) {
            endButton.click();

            // Select a random sample book to add to My library
            sleep(1);
            tapDisplayCentre();
            sleep(1);

            // Click done button (uses same resource-id)
            endButton.click();
        }
    }

    private void openMyLibrary() throws Exception {
        Timer result = new Timer();
        result.start();

        UiObject openDrawer = getUiObjectByDescription("Show navigation drawer",
                                                       "android.widget.ImageButton");
        openDrawer.click();

        // To correctly find the UiObject we need to specify the index also here
        UiObject myLibrary =
            new UiObject(new UiSelector().className("android.widget.TextView")
                                         .text("My library").index(3));
        myLibrary.clickAndWaitForNewWindow(timeout);

        result.end();

        timingResults.put("open_library", result);
    }

    private void searchForBook(final String text) throws Exception {
        Timer result = new Timer();
        result.start();
        UiObject search =
            new UiObject(new UiSelector().resourceId("com.google.android.apps.books:id/menu_search"));
        search.click();

        UiObject searchText = new UiObject(new UiSelector().textContains("Search")
                                                           .className("android.widget.EditText"));
        searchText.setText(text);
        pressEnter();

        UiObject resultList =
            new UiObject(new UiSelector().resourceId("com.android.vending:id/search_results_list"));

        if (!resultList.waitForExists(viewTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"search results list view\".");
        }

        result.end();
        timingResults.put("search_for_book", result);
        pressBack();
    }


    private void gesturesTest() throws Exception {
        String testTag = "gestures";

        // Perform a range of swipe tests while browsing home photoplaybooks gallery
        LinkedHashMap<String, GestureTestParams> testParams = new LinkedHashMap<String, GestureTestParams>();
        testParams.put("swipe_left", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.LEFT, 10));
        testParams.put("swipe_right", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.RIGHT, 10));
        testParams.put("pinch_out", new GestureTestParams(GestureType.PINCH, PinchType.OUT, 100, 50));
        testParams.put("pinch_in", new GestureTestParams(GestureType.PINCH, PinchType.IN, 100, 50));

        Iterator<Entry<String, GestureTestParams>> it = testParams.entrySet().iterator();

        while (it.hasNext()) {
            Map.Entry<String, GestureTestParams> pair = it.next();
            GestureType type = pair.getValue().gestureType;
            Direction dir = pair.getValue().gestureDirection;
            PinchType pinch = pair.getValue().pinchType;
            int steps = pair.getValue().steps;
            int percent = pair.getValue().percent;

            String runName = String.format(testTag + "_" + pair.getKey());
            SurfaceLogger logger = new SurfaceLogger(runName, parameters);

            UiObject pageView = getPageView();

            if (!pageView.waitForExists(viewTimeout)) {
                throw new UiObjectNotFoundException("Could not find \"page view\".");
            }

            logger.start();

            switch (type) {
                case UIDEVICE_SWIPE:
                    uiDeviceSwipe(dir, steps);
                    break;
                case UIOBJECT_SWIPE:
                    uiObjectSwipe(pageView, dir, steps);
                    break;
                case PINCH:
                    uiObjectVertPinch(pageView, pinch, steps, percent);
                    break;
                default:
                    break;
            }

            logger.stop();
            timingResults.put(runName, logger.result());
        }

        if (!getPageView().waitForExists(viewTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"page view\".");
        }
    }

    private void selectRandomChapter() throws Exception {
        String testTag = "select_random_chapter";
        SurfaceLogger logger = new SurfaceLogger(testTag, parameters);

        getDropdownMenu();

        UiObject contents = getUiObjectByResourceId("com.google.android.apps.books:id/menu_reader_toc",
                                                    "android.widget.TextView");
        contents.clickAndWaitForNewWindow(timeout);

        UiObject toChapterView = getUiObjectByResourceId("com.google.android.apps.books:id/toc_list_view",
                                                         "android.widget.ExpandableListView");

        logger.start();
        toChapterView.swipeUp(100);
        tapDisplayCentre();
        logger.stop();

        waitForPage();

        timingResults.put(testTag, logger.result());
    }

    private void addNote(final String text) throws Exception {
        Timer result = new Timer();
        result.start();

        UiObject clickable = new UiObject(new UiSelector().longClickable(true));
        uiDevicePerformLongClick(clickable, 100);
        UiObject addNoteButton = getUiObjectByResourceId("com.google.android.apps.books:id/add_note_button",
                                                        "android.widget.ImageButton");
        addNoteButton.click();

        UiObject noteEditText = getUiObjectByResourceId("com.google.android.apps.books:id/note_edit_text",
                                                        "android.widget.EditText");
        noteEditText.setText(text);

        UiObject noteMenuButton = getUiObjectByResourceId("com.google.android.apps.books:id/note_menu_button",
                                                          "android.widget.ImageButton");
        noteMenuButton.click();

        UiObject saveButton = getUiObjectByText("Save", "android.widget.TextView");
        saveButton.click();

        waitForPage();

        result.end();
        timingResults.put("add_note", result);
    }

    private void removeNote() throws Exception {
        Timer result = new Timer();
        result.start();
        UiObject clickable = new UiObject(new UiSelector().longClickable(true));
        uiDevicePerformLongClick(clickable, 100);

        UiObject removeButton = getUiObjectByResourceId("com.google.android.apps.books:id/remove_highlight_button",
                                                        "android.widget.ImageButton");
        removeButton.click();

        UiObject confirmRemove = getUiObjectByText("Remove", "android.widget.Button");
        confirmRemove.click();

        waitForPage();

        result.end();
        timingResults.put("remove_note", result);
    }

    private void searchForWord(final String text) throws Exception {
        getDropdownMenu();
        Timer result = new Timer();
        result.start();
        UiObject search = new UiObject(
                new UiSelector().resourceId("com.google.android.apps.books:id/menu_search"));
        search.click();



        UiObject searchText = new UiObject(
                new UiSelector().resourceId("com.google.android.apps.books:id/search_src_text"));
        searchText.setText(text);
        pressEnter();

        UiObject resultList = new UiObject(
                new UiSelector().resourceId("com.google.android.apps.books:id/search_results_list"));

        // Allow extra time for search queries involing high freqency words
        final long searchTimeout =  TimeUnit.SECONDS.toMillis(20);

        if (!resultList.waitForExists(searchTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"search results list view\".");
        }

        UiObject searchWeb =
            new UiObject(new UiSelector().text("Search web")
                                         .className("android.widget.TextView"));

        if (!searchWeb.waitForExists(searchTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"Search web view\".");
        }

        result.end();
        timingResults.put("search_for_word", result);

        pressBack();
    }

    private void switchPageStyles() throws Exception {

        String testTag = "switch_page_style";

        getDropdownMenu();
        UiObject readerSettings = getUiObjectByResourceId("com.google.android.apps.books:id/menu_reader_settings",
                                                          "android.widget.TextView");
        readerSettings.click();

        // Check for lighting option button on newer versions
        UiObject lightingOptionsButton =
            new UiObject(new UiSelector().resourceId("com.google.android.apps.books:id/lighting_options_button"));

        if (lightingOptionsButton.exists()) {
            lightingOptionsButton.click();
        }

        String[] styles = {"Night", "Sepia", "Day"};

        for (String style : styles) {
            SurfaceLogger logger = new SurfaceLogger(testTag + "_" + style, parameters);
            logger.start();
            UiObject pageStyle = new UiObject(new UiSelector().description(style));
            pageStyle.clickAndWaitForNewWindow(viewTimeout);
            logger.stop();
            timingResults.put(String.format(testTag + "_" + style), logger.result());
        }

        pressBack();
    }

    private void aboutBook() throws Exception {
        getDropdownMenu();
        Timer result = new Timer();
        result.start();

        UiObject moreOptions = getUiObjectByDescription("More options", "android.widget.ImageView");
        moreOptions.click();

        UiObject bookInfo = getUiObjectByText("About this book", "android.widget.TextView");
        bookInfo.clickAndWaitForNewWindow(timeout);

        UiObject detailsPanel =
            new UiObject(new UiSelector().resourceId("com.android.vending:id/item_details_panel"));
        waitObject(detailsPanel, viewTimeoutSecs);
        result.end();

        timingResults.put("about_book", result);
        pressBack();
    }

    // Helper to click on an individual book based on index in My library gallery.
    private void selectBook(final int index) throws Exception {

        UiObject book =
            new UiObject(new UiSelector().resourceId("com.google.android.apps.books:id/cards_grid")
                                         .childSelector(new UiSelector()
                                         .index(index + 1) // adjust for zero index
                                         .className("android.widget.FrameLayout")
                                         .clickable(true)));
        book.clickAndWaitForNewWindow();

        if (!getPageView().waitForExists(viewTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"page view\".");
        }
    }

    // Helper for accessing the drop down menu
    private void getDropdownMenu() throws Exception {
        sleep(1); // Allow previous views to settle
        int height = getDisplayHeight();
        int width = getDisplayCentreWidth();
        getUiDevice().swipe(width, 5, width, height / 10, 20);
    }

    // Helper for returning common UiObject page view
    private UiObject getPageView() {
        return new UiObject(new UiSelector().resourceId("com.google.android.apps.books:id/book_view")
                                            .childSelector(new UiSelector()
                                            .focusable(true)));
    }

    // Helper for waiting on a page between actions
    private void waitForPage() throws Exception {
        UiObject activityReader =
            new UiObject(new UiSelector().resourceId("com.google.android.apps.books:id/activity_reader")
                                         .childSelector(new UiSelector().focusable(true)));

        if (!activityReader.waitForExists(viewTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"activity reader view\".");
        }
    }
}
