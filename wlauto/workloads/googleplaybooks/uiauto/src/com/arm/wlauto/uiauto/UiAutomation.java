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
import com.android.uiautomator.core.UiWatcher;
import com.android.uiautomator.core.UiScrollable;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.util.concurrent.TimeUnit;
import java.util.LinkedHashMap;
import java.util.Iterator;
import android.util.Log;
import java.util.Map;
import java.util.Map.Entry;

public class UiAutomation extends UxPerfUiAutomation {

    protected Bundle parameters;
    protected String packageName;
    protected String packageID;

    private int viewTimeoutSecs = 10;
    private long viewTimeout =  TimeUnit.SECONDS.toMillis(viewTimeoutSecs);

    public void runUiAutomation() throws Exception {
        this.uiAutoTimeout = TimeUnit.SECONDS.toMillis(8);

        parameters = getParams();
        packageName = parameters.getString("package");
        packageID = packageName + ":id/";

        String bookTitle = parameters.getString("book_title").replace("0space0", " ");
        String chapterPageNumber = parameters.getString("chapter_page_number");
        String searchWord = parameters.getString("search_word");
        String noteText = "This is a test note";

        setScreenOrientation(ScreenOrientation.NATURAL);
        clearFirstRunDialogues();
        dismissSync();

        searchForBook(bookTitle);
        addToLibrary();
        openMyLibrary();
        openBook(bookTitle);

        UiWatcher pageSyncPopUpWatcher = createPopUpWatcher();
        registerWatcher("pageSyncPopUp", pageSyncPopUpWatcher);
        runWatchers();

        selectChapter(chapterPageNumber);
        gesturesTest();
        addNote(noteText);
        removeNote();
        searchForWord(searchWord);
        switchPageStyles();
        aboutBook();

        removeWatcher("pageSyncPop");
        pressBack();
        unsetScreenOrientation();
    }

    // Creates a watcher for when a pop up warning appears when pages are out
    // of sync across multiple devices.
    private UiWatcher createPopUpWatcher() throws Exception {
        UiWatcher pageSyncPopUpWatcher = new UiWatcher() {

            @Override
            public boolean checkForCondition() {
                UiObject popUpDialogue =
                    new UiObject(new UiSelector().resourceId("android:id/message")
                                                 .textStartsWith("You're on page"));

                // Don't sync and stay on the current page
                if (popUpDialogue.exists()) {
                    try {
                        UiObject stayOnPage = new UiObject(new UiSelector()
                                .className("android.widget.Button")
                                .text("Yes"));
                        stayOnPage.click();
                    } catch (UiObjectNotFoundException e) {
                        e.printStackTrace();
                    }
                    return popUpDialogue.waitUntilGone(viewTimeout);
                }
                return false;
            }
        };

        return pageSyncPopUpWatcher;
    }

    private void dismissSync() throws Exception {
        UiObject keepSyncOff =
            new UiObject(new UiSelector().textContains("Keep sync off")
                                         .className("android.widget.Button"));
        if (keepSyncOff.exists()) {
            keepSyncOff.click();
        }
    }

    // If there is no sample book in My library we are prompted to choose a
    // book the first time application is run. Try to skip the screen or
    // pick a random sample book.
    private void clearFirstRunDialogues() throws Exception {
        UiObject startButton =
            new UiObject(new UiSelector().resourceId(packageID + "start_button"));

        // First try and skip the sample book selection
        if (startButton.exists()) {
            startButton.click();
        }

        UiObject endButton =
            new UiObject(new UiSelector().resourceId(packageID + "end_button"));

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

    // Searches for a "free" or "purchased" book title in Google play
    private void searchForBook(final String bookTitle) throws Exception {
        UiObject search =
            new UiObject(new UiSelector().resourceId(packageID + "menu_search"));
        search.click();

        UiObject searchText = new UiObject(new UiSelector().textContains("Search")
                                                           .className("android.widget.EditText"));
        searchText.setText(bookTitle);
        pressEnter();

        UiObject resultList =
            new UiObject(new UiSelector().resourceId("com.android.vending:id/search_results_list"));

        if (!resultList.waitForExists(viewTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"search results list view\".");
        }

        String desc = String.format("Book: " + bookTitle);

        // Create a selector so that we can search for siblings of the desired
        // book that contains a "free" or "purchased" book identifier
        UiSelector bookSelector = new UiSelector().description(desc).className("android.widget.TextView");

        UiObject label =
            new UiObject(new UiSelector().fromParent(bookSelector)
                                         .resourceId("com.android.vending:id/li_label")
                                         .descriptionMatches("^(Purchased|Free)$"));

        UiScrollable searchResultsList =
            new UiScrollable(new UiSelector().resourceId("com.android.vending:id/search_results_list"));

        final int maxSearchTime = 30;
        int searchTime = maxSearchTime;

        while (!label.exists()) {
            if (searchTime <= 0) {
                throw new UiObjectNotFoundException(
                        "Exceeded maximum search time (" + maxSearchTime  + " seconds) to find book \"" + bookTitle + "\"");
            } else {
                uiDeviceSwipeDown(100);
                sleep(1);
                searchTime--;
            }
        }

        // Click on either the first "free" or "purchased" book found that
        // matches the book title
        label.click();
    }

    private void addToLibrary() throws Exception {
        UiObject add = new UiObject(new UiSelector().textContains("ADD TO LIBRARY")
                                                    .className("android.widget.Button"));
        if (add.exists()) {
            add.click(); // add to My Library and opens book by default
        } else {
            UiObject read = getUiObjectByText("READ", "android.widget.Button");
            read.click(); // opens book
        }

        waitForPage();

        UiObject navigationButton = new UiObject(new UiSelector().description("Navigate up"));

        // Return to main app window
        pressBack();

        // On some devices screen ordering is not preserved so check for
        // navigation button to determine current screen
        if (navigationButton.exists()) {
            pressBack();
            pressBack();
        }
    }

    private void openMyLibrary() throws Exception {
        String testTag = "open_library";
        ActionLogger logger = new ActionLogger(testTag, parameters);
        logger.start();

        UiObject openDrawer = getUiObjectByDescription("Show navigation drawer");
        openDrawer.click();

        // To correctly find the UiObject we need to specify the index also here
        UiObject myLibrary =
            new UiObject(new UiSelector().className("android.widget.TextView")
                                         .text("My library").index(3));
        myLibrary.clickAndWaitForNewWindow(uiAutoTimeout);
        logger.stop();
    }

    private void openBook(final String bookTitle) throws Exception {
        String testTag = "open_book";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        UiScrollable cardsGrid =
            new UiScrollable(new UiSelector().resourceId(packageID + "cards_grid"));

        UiSelector bookSelector = new UiSelector().text(bookTitle).className("android.widget.TextView");
        UiObject book = new UiObject(bookSelector);

        // Check that books are sorted by time added to library. This way we
        // can assume any newly downloaded books will be visible on the first
        // screen.
        UiObject menuSort =
            getUiObjectByResourceId(packageID + "menu_sort", "android.widget.TextView");
        menuSort.click();

        UiObject sortByRecent = getUiObjectByText("Recent", "android.widget.TextView");
        sortByRecent.click();

        // When the book is first added to library it may not appear in
        // cardsGrid until it has been fully downloaded. Wait for fully
        // downloaded books
        UiObject downloadComplete =
            new UiObject(new UiSelector().fromParent(bookSelector).description("100% downloaded"));

        long maxWaitTimeSeconds = 120;
        long maxWaitTime = TimeUnit.SECONDS.toMillis(maxWaitTimeSeconds);

        if (!downloadComplete.waitForExists(maxWaitTime)) {
                throw new UiObjectNotFoundException(
                        "Exceeded maximum wait time (" + maxWaitTimeSeconds  + " seconds) to download book \"" + bookTitle + "\"");
        }

        logger.start();
        book.click();
        waitForPage();
        logger.stop();
    }

    private void gesturesTest() throws Exception {
        String testTag = "gesture";

        // Perform a range of swipe tests while browsing home photoplaybooks gallery
        LinkedHashMap<String, GestureTestParams> testParams = new LinkedHashMap<String, GestureTestParams>();
        testParams.put("swipe_left", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.LEFT, 20));
        testParams.put("swipe_right", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.RIGHT, 20));
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
            ActionLogger logger = new ActionLogger(runName, parameters);

            UiObject pageView = waitForPage();

            logger.start();

            switch (type) {
                case UIDEVICE_SWIPE:
                    uiDeviceSwipe(dir, steps);
                    break;
                case PINCH:
                    uiObjectVertPinch(pageView, pinch, steps, percent);
                    break;
                default:
                    break;
            }

            logger.stop();
        }

        waitForPage();
    }

    private UiObject searchPage(final UiObject view, final String pagenum, final Direction updown,
                                final int attempts) throws Exception {
        if (attempts <= 0) {
            throw new UiObjectNotFoundException("Could not find \"page number\" after several attempts.");
        }

        String search = String.format("page " + pagenum);
        UiObject page = new UiObject(new UiSelector().description(search)
                                                    .className("android.widget.TextView"));
        if (!page.exists()) {
            // Scroll up by swiping down
            if (updown == Direction.UP) {
                view.swipeDown(200);
            // Default case is to scroll down (swipe up)
            } else {
                view.swipeUp(200);
            }
            searchPage(view, pagenum, updown, attempts - 1);
        }
        return page;
    }

    private void selectChapter(final String chapterPageNumber) throws Exception {
        getDropdownMenu();

        UiObject contents = getUiObjectByResourceId(packageID + "menu_reader_toc");
        contents.clickAndWaitForNewWindow(uiAutoTimeout);

        UiObject toChapterView = getUiObjectByResourceId(packageID + "toc_list_view",
                                                         "android.widget.ExpandableListView");

        // Navigate to top of chapter view
        searchPage(toChapterView, "1", Direction.UP, 10);

        UiObject page = searchPage(toChapterView, chapterPageNumber, Direction.DOWN, 10);

        page.clickAndWaitForNewWindow(viewTimeout);

        waitForPage();
    }

    private void addNote(final String text) throws Exception {
        String testTag = "note_add";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        hideDropDownMenu();

        logger.start();

        UiObject clickable = new UiObject(new UiSelector().longClickable(true));
        uiObjectPerformLongClick(clickable, 100);

        UiObject addNoteButton = new UiObject(
                new UiSelector().resourceId(packageID + "add_note_button"));
        addNoteButton.click();

        UiObject noteEditText = getUiObjectByResourceId(packageID + "note_edit_text",
                                                        "android.widget.EditText");
        noteEditText.setText(text);

        UiObject noteMenuButton = getUiObjectByResourceId(packageID + "note_menu_button",
                                                          "android.widget.ImageButton");
        noteMenuButton.click();

        UiObject saveButton = getUiObjectByText("Save", "android.widget.TextView");
        saveButton.click();

        logger.stop();

        waitForPage();
    }

    private void removeNote() throws Exception {
        String testTag = "note_remove";
        ActionLogger logger = new ActionLogger(testTag, parameters);
        logger.start();

        UiObject clickable = new UiObject(new UiSelector().longClickable(true));
        uiObjectPerformLongClick(clickable, 100);

        UiObject removeButton = new UiObject(
                new UiSelector().resourceId(packageID + "remove_highlight_button"));
        removeButton.click();

        UiObject confirmRemove = getUiObjectByText("Remove", "android.widget.Button");
        confirmRemove.click();

        logger.stop();

        waitForPage();
    }

    private void searchForWord(final String text) throws Exception {
        String testTag = "search_word";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        getDropdownMenu();

        UiObject search = new UiObject(
                new UiSelector().resourceId(packageID + "menu_search"));
        search.click();

        UiObject searchText = new UiObject(
                new UiSelector().resourceId(packageID + "search_src_text"));

        logger.start();

        searchText.setText(text);
        pressEnter();

        UiObject resultList = new UiObject(
                new UiSelector().resourceId(packageID + "search_results_list"));

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

        logger.stop();

        pressBack();
    }

    private void switchPageStyles() throws Exception {
        String testTag = "style";

        getDropdownMenu();
        UiObject readerSettings = getUiObjectByResourceId(packageID + "menu_reader_settings",
                                                          "android.widget.TextView");
        readerSettings.click();

        // Check for lighting option button on newer versions
        UiObject lightingOptionsButton =
            new UiObject(new UiSelector().resourceId(packageID + "lighting_options_button"));

        if (lightingOptionsButton.exists()) {
            lightingOptionsButton.click();
        }

        String[] styles = {"Night", "Sepia", "Day"};

        for (String style : styles) {
            try {
                ActionLogger logger = new ActionLogger(testTag + "_" + style, parameters);
                UiObject pageStyle = new UiObject(new UiSelector().description(style));
                logger.start();
                pageStyle.clickAndWaitForNewWindow(viewTimeout);
                logger.stop();
            } catch (UiObjectNotFoundException e) {
                // On some devices the lighting options menu disappears
                // between clicks. Searching for the menu again would affect
                // the logger timings so log a message and continue
                Log.e("GooglePlayBooks", "Could not find pageStyle \"" + style + "\"");
            }
        }

        sleep(2);
        tapDisplayCentre(); // exit reader settings dialog
        waitForPage();
    }

    private void aboutBook() throws Exception {
        String testTag = "open_about";
        ActionLogger logger = new ActionLogger(testTag, parameters);

        getDropdownMenu();

        UiObject moreOptions = getUiObjectByDescription("More options", "android.widget.ImageView");
        moreOptions.click();

        UiObject bookInfo = getUiObjectByText("About this book", "android.widget.TextView");

        logger.start();

        bookInfo.clickAndWaitForNewWindow(uiAutoTimeout);

        UiObject detailsPanel =
            new UiObject(new UiSelector().resourceId("com.android.vending:id/item_details_panel"));
        waitObject(detailsPanel, viewTimeoutSecs);
        
        logger.stop();

        pressBack();
    }

    // Helper for accessing the drop down menu
    private void getDropdownMenu() throws Exception {
        UiObject actionBar =
            new UiObject(new UiSelector().resourceId(packageID + "action_bar"));

        if (!actionBar.exists()) {
            tapDisplayCentre();
            sleep(1); // Allow previous views to settle
        }

        if (!actionBar.exists()) {
            throw new UiObjectNotFoundException("Could not find \"action bar\".");
        }
    }

    private void hideDropDownMenu() throws Exception {
        UiObject actionBar =
            new UiObject(new UiSelector().resourceId(packageID + "action_bar"));

        if (actionBar.exists()) {
            tapDisplayCentre();
            sleep(1); // Allow previous views to settle
        }

        if (actionBar.exists()) {
            throw new UiObjectNotFoundException("Could not close \"action bar\".");
        }
    }

    // Helper for waiting on a page between actions
    private UiObject waitForPage() throws Exception {
        UiObject activityReader =
            new UiObject(new UiSelector().resourceId(packageID + "activity_reader")
                                         .childSelector(new UiSelector().focusable(true)));

        // On some devices the object in the view hierarchy is found before it
        // becomes visible on the screen. Therefore add pause instead.
        sleep(3);

        if (!activityReader.waitForExists(viewTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"activity reader view\".");
        }

        return activityReader;
    }
}
