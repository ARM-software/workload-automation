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

package com.arm.wlauto.uiauto.reader;

import android.graphics.Rect;
import android.os.Bundle;
import android.os.SystemClock;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.util.concurrent.TimeUnit;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Map.Entry;

public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "uxperf_reader";

    private Bundle parameters;
    private long networkTimeout =  TimeUnit.SECONDS.toMillis(20);
    private long searchTimeout =  TimeUnit.SECONDS.toMillis(20);
    private LinkedHashMap<String, Timer> timingResults = new LinkedHashMap<String, Timer>();

    public void runUiAutomation() throws Exception {
        parameters = getParams();
        String filename = parameters.getString("filename").replace("_", " ");
        String[] searchStrings = {parameters.getString("first_search_word"),
                                  parameters.getString("second_search_word")};

        setScreenOrientation(ScreenOrientation.NATURAL);

        dismissWelcomeView();

        confirmAccess();

        gesturesTest(filename);
        searchPdfTest(filename, searchStrings);

        unsetScreenOrientation();

        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    private void dismissWelcomeView() throws Exception {
        UiObject welcomeView = getUiObjectByResourceId("android:id/content",
                                                   "android.widget.FrameLayout");
        welcomeView.swipeLeft(10);
        welcomeView.swipeLeft(10);

        UiObject continueButton = getUiObjectByResourceId("com.adobe.reader:id/onboarding_finish_button",
                                                   "android.widget.Button");
        continueButton.click();

        // Deal with the annoying promotional Dropbox CoachMark popup
        UiObject dropBoxcoachMark = getUiObjectByDescription("CoachMark", "android.widget.LinearLayout");
        if (dropBoxcoachMark.exists()) {
            tapDisplayCentre();
        }

        UiObject actionBarTitle = getUiObjectByDescription("My Documents",
                                                     "android.widget.LinearLayout");
        actionBarTitle.waitForExists(uiAutoTimeout);
    }

    private void openFile(final String filename) throws Exception {

        String testTag = "openfile";

        // Replace whitespace and full stops within the filename
        String file = filename.replaceAll("\\.", "_").replaceAll("\\s+", "_");

        timingResults.put(String.format(testTag + "_" + "selectLocalFilesList" + "_" + file), selectLocalFilesList());

        // On some devices permissions to access local files occurs here rather than the earlier step
        confirmAccess();
        timingResults.put(String.format(testTag + "_" + "selectSearchDuration" + "_" + file), selectSearchFileButton());
        timingResults.put(String.format(testTag + "_" + "searchFileList" + "_" + file), searchFileList(filename));
        timingResults.put(String.format(testTag + "_" + "openFileFromList" + "_" + file), openFileFromList(filename));
    }

    private Timer selectLocalFilesList() throws Exception {
        // Select the local files list from the My Documents view
        UiObject localButton = getUiObjectByText("LOCAL", "android.widget.TextView");
        Timer result = new Timer();
        result.start();
        localButton.click();
        long finish = SystemClock.elapsedRealtime();
        result.end();
        return result;
    }

    private Timer selectSearchFileButton() throws Exception {
        // Click the button to search from the present file list view
        UiObject searchButton = getUiObjectByResourceId("com.adobe.reader:id/split_pane_search",
                                                        "android.widget.TextView",
                                                        TimeUnit.SECONDS.toMillis(10));

        Timer result = new Timer();
        result.start();
        searchButton.click();
        long finish = SystemClock.elapsedRealtime();
        result.end();
        return result;
    }

    private Timer searchFileList(final String searchText) throws Exception {
        // Enter search text into the file searchBox.  This will automatically filter the list.
        UiObject searchBox = getUiObjectByResourceId("android:id/search_src_text",
                                                     "android.widget.EditText");
        Timer result = new Timer();
        result.start();
        searchBox.setText(searchText);
        long finish = SystemClock.elapsedRealtime();
        result.end();
        return result;
    }

    private Timer openFileFromList(final String file) throws Exception {
        // Open a file from a file list view by searching for UiObjects containing the doc title.
        UiObject fileObject = getUiObjectByText(file, "android.widget.TextView");
        Timer result = new Timer();
        result.start();
        fileObject.clickAndWaitForNewWindow(uiAutoTimeout);
        result.end();

        // Wait for the doc to open by waiting for the viewPager UiObject to exist
        UiObject viewPager = new UiObject(new UiSelector().resourceId("com.adobe.reader:id/viewPager"));
        if (!viewPager.waitForExists(uiAutoTimeout)) {
            throw new UiObjectNotFoundException("Could not find \"viewPager\".");
        };
        return result;
    }

    private void gesturesTest(final String filename) throws Exception {

        String testTag = "gestures";

        // Perform a range of swipe tests at different speeds and on different views
        LinkedHashMap<String, GestureTestParams> testParams = new LinkedHashMap<String, GestureTestParams>();
        testParams.put("1", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.DOWN, 200));
        testParams.put("2", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.UP, 200));
        testParams.put("3", new GestureTestParams(GestureType.UIOBJECT_SWIPE, Direction.RIGHT, 50));
        testParams.put("4", new GestureTestParams(GestureType.UIOBJECT_SWIPE, Direction.LEFT, 50));
        testParams.put("5", new GestureTestParams(GestureType.PINCH, PinchType.OUT, 100, 50));
        testParams.put("6", new GestureTestParams(GestureType.PINCH, PinchType.IN, 100, 50));

        Iterator<Entry<String, GestureTestParams>> it = testParams.entrySet().iterator();

        openFile(filename);

        tapDisplayCentre();

        while (it.hasNext()) {
            Map.Entry<String, GestureTestParams> pair = it.next();
            GestureType type = pair.getValue().gestureType;
            Direction dir = pair.getValue().gestureDirection;
            PinchType pinch = pair.getValue().pinchType;
            int steps = pair.getValue().steps;
            int percent = pair.getValue().percent;

            UiObject view = new UiObject(new UiSelector().resourceId("com.adobe.reader:id/viewPager"));

            String runName = String.format(testTag + "_" + pair.getKey());
            SurfaceLogger logger = new SurfaceLogger(runName, parameters);
            logger.start();

            switch (type) {
                case UIDEVICE_SWIPE:
                    uiDeviceSwipe(dir, steps);
                    break;
                case UIOBJECT_SWIPE:
                    uiObjectSwipe(view, dir, steps);
                    break;
                case PINCH:
                    uiObjectVertPinch(view, pinch, steps, percent);
                    break;
                default:
                    break;
            }

            logger.stop();
            timingResults.put(runName, logger.result());
        }

        exitDocument();
    }

    private void searchPdfTest(final String filename, final String[] searchStrings) throws Exception {

        String testTag = "search";

        openFile(filename);

        // Get the page view for the opened document which we can use for pinch actions
        UiObject pageView = getUiObjectByResourceId("com.adobe.reader:id/pageView",
                                                    "android.widget.RelativeLayout");
        for (int i = 0; i < searchStrings.length; i++) {
            timingResults.put(String.format(testTag + "_" + i),
                                            searchTest(searchStrings[i]));
        }

        exitDocument();
    }

    private Timer searchTest(final String searchText) throws Exception {
        // Click on the search button icon and enter text in the box.  This closes the keyboad
        // so click the box again and press Enter to start the search.
        UiObject searchButton = getUiObjectByResourceId("com.adobe.reader:id/document_view_search_icon",
                                                        "android.widget.TextView");
        searchButton.clickAndWaitForNewWindow();
        UiObject searchBox = getUiObjectByResourceId("android:id/search_src_text",
                                                     "android.widget.EditText");
        searchBox.setText(searchText);
        getUiDevice().getInstance().pressSearch();
        Timer result = new Timer();
        result.start();

        // Deal with the Yoga Tab 3 special case which does not handle Enter keys in search boxes
        String productName = getUiDevice().getProductName();
        if (productName.equals("YT3_10_row_wifi")) {
            tapDisplay(2370, 1100);
        } else {
            getUiDevice().getInstance().pressEnter();
        }

        // Check the progress bar icon.  When this disappears the search is complete.
        UiObject progressBar = new UiObject(new UiSelector().resourceId("com.adobe.reader:id/searchProgress")
                                                            .className("android.widget.ProgressBar"));
        progressBar.waitForExists(uiAutoTimeout);
        progressBar.waitUntilGone(searchTimeout);
        result.end();

        // Get back to the main document view by clicking twice on the close button
        UiObject searchCloseButton = getUiObjectByResourceId("android:id/search_close_btn",
                                                             "android.widget.ImageView");
        searchCloseButton.clickAndWaitForNewWindow();
        searchCloseButton.clickAndWaitForNewWindow();

        return result;
    }

    private void exitDocument() throws Exception {
        // Return from the document view to the file list view by pressing home and my documents.
        UiObject homeButton = new UiObject(new UiSelector().resourceId("android:id/home")
                                                          .className("android.widget.ImageView"));
        if (!homeButton.waitForExists(uiAutoTimeout)) {
            tapDisplayCentre();
        }
        homeButton.clickAndWaitForNewWindow();
        UiObject myDocsButton = getUiObjectByDescription("My Documents", "android.widget.LinearLayout" );
        myDocsButton.clickAndWaitForNewWindow();
        UiObject upButton = getUiObjectByResourceId("android:id/up", "android.widget.ImageView" );
        upButton.clickAndWaitForNewWindow();
    }
}
