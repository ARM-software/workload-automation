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

package com.arm.wlauto.uiauto.excel;

import android.os.Bundle;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.util.concurrent.TimeUnit;
import java.util.LinkedHashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Map.Entry;


public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "uxperf_excel";

    public Bundle parameters;
    private int viewTimeoutSecs = 10;
    private long viewTimeout =  TimeUnit.SECONDS.toMillis(viewTimeoutSecs);
    private LinkedHashMap<String, Timer> timingResults = new LinkedHashMap<String, Timer>();

    public void runUiAutomation() throws Exception {
        parameters = getParams();

        setScreenOrientation(ScreenOrientation.NATURAL);
        confirmAccess();
        skipSignInView();

        newFile();
        createInTestFolder();
        selectBlankWorkbook();
        dismissToolTip();
        createTable();
        gesturesTest();
        searchTable();
        nameWorkbook();

        unsetScreenOrientation();
        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    private void skipSignInView() throws Exception {
        UiObject skipSignIn = getUiObjectByText("Skip", "android.widget.TextView");
        skipSignIn.click();
    }

    private void newFile() throws Exception {
        UiObject newButton = getUiObjectByText("New", "android.widget.Button");
        newButton.click();
    }

    private void createInTestFolder() throws Exception {
        UiObject docLocation =
            getUiObjectByText("This device > Documents", "android.widget.ToggleButton");
        docLocation.click();

        UiObject selectLocation =
            getUiObjectByText("Select a different location...", "android.widget.TextView");
        selectLocation.click();

        UiObject deviceLocation = getUiObjectByText("This device", "android.widget.TextView");
        deviceLocation.click();

        UiObject storageLocation =
            new UiObject(new UiSelector().resourceId(parameters.getString("package") + ":id/list_entry_title")
                                         .text("Storage"));
        storageLocation.click();

        UiScrollable scrollView =
            new UiScrollable(new UiSelector().className("android.widget.ScrollView"));

        UiObject folderName =
            new UiObject(new UiSelector().className("android.widget.TextView").text("wa-working"));

        while (!folderName.exists()) {
            scrollView.scrollForward();
        }

        folderName.click();

        UiObject selectButton = getUiObjectByText("Select", "android.widget.Button");
        selectButton.click();
    }

    private void selectBlankWorkbook() throws Exception {
        UiObject blankWorkBook = getUiObjectByText("Blank workbook", "android.widget.TextView");
        blankWorkBook.click();
    }

    private void dismissToolTip() throws Exception {
        UiObject gotItButton = getUiObjectByText("Got it!", "android.widget.Button");
        gotItButton.click();
    }

    private void createTable() throws Exception {

        String testTag = "create_table";
        SurfaceLogger logger = new SurfaceLogger(testTag, parameters);
        logger.start();

        String[] columnNames = {"Item", "Net", "Gross"};
        String[] rowValues   = {"Potatoes", "0.40", "0.48", "Onions", "0.90", "1.08"};

        final int nColumns = columnNames.length;
        final int nRows = rowValues.length / nColumns;

        // Create the header
        for (String columnName : columnNames) {
            setCell(columnName);
            pressDPadRight();
        }

        formatHeader();
        resetColumnPosition(nColumns);

        // Create the rows
        for (int i = 0; i < nRows; ++i) {
            for (int j = 0; j < nColumns; ++j) {
                setCell(rowValues[(i * nColumns) + j]);
                pressDPadRight();
            }
            resetColumnPosition(nColumns);
        }

        // Calculate the column totals
        setCell("TOTAL");
        pressDPadRight();
        setCell("=SUM(B2, B3)");
        pressDPadRight();
        setCell("=SUM(C2, C3)");

        formatTotal();
        resetColumnPosition(nColumns);

        logger.stop();
        timingResults.put(testTag, logger.result());
    }

    private void formatHeader() throws Exception {
        String testTag = "format_header";
        SurfaceLogger logger = new SurfaceLogger(testTag, parameters);

        highlightRow();

        logger.start();

        UiObject boldButton = getUiObjectByDescription("Bold", "android.widget.ToggleButton");
        boldButton.click();

        UiObject borderButton = getUiObjectByText("Borders", "android.widget.ToggleButton");
        borderButton.click();

        UiObject borderStyle = getUiObjectByDescription("Top and Thick Bottom Border", "android.widget.Button");
        borderStyle.click();

        pressBack();

        logger.stop();
        timingResults.put(testTag, logger.result());
    }

    private void formatTotal() throws Exception {
        String testTag = "format_header";
        SurfaceLogger logger = new SurfaceLogger(testTag, parameters);

        highlightRow();

        logger.start();

        UiObject fontColorButton = getUiObjectByText("Font Colour", "android.widget.Button");
        fontColorButton.click();
        pressBack();

        logger.stop();
        timingResults.put(testTag, logger.result());
    }

    private void gesturesTest() throws Exception {
        String testTag = "gestures";

        // Perform a range of swipe tests while browsing photo gallery
        LinkedHashMap<String, GestureTestParams> testParams = new LinkedHashMap<String, GestureTestParams>();
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

            UiObject view = new UiObject(new UiSelector().enabled(true));

            if (!view.waitForExists(viewTimeout)) {
                throw new UiObjectNotFoundException("Could not find \"table view\".");
            }

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
    }

    private void searchTable() throws Exception {
        UiObject findButton = getUiObjectByDescription("Find", "android.widget.Button");
        findButton.click();

        UiObject editText = new UiObject(new UiSelector().className("android.widget.EditText"));
        editText.setText("Onions");
        pressEnter();
    }

    private void nameWorkbook() throws Exception {
        UiObject docTitleName = getUiObjectByResourceId("com.microsoft.office.excel:id/DocTitlePortrait",
                                                        "android.widget.TextView");
        docTitleName.setText("WA_Test_Book");

        pressEnter();
        pressBack();
    }

    // Helper method for setting the currently selected cell's text content
    private void setCell(final String value) throws Exception {
        UiObject cellBox =
            new UiObject(new UiSelector().resourceId("com.microsoft.office.excel:id/mainCanvas")
                                         .childSelector(new UiSelector().index(0)
                                         .childSelector(new UiSelector().index(0)
                                         .childSelector(new UiSelector().index(1)
                                         .childSelector(new UiSelector().index(0)
                                         .childSelector(new UiSelector().index(2)
                                         .childSelector(new UiSelector().index(2))))))));
        cellBox.setText(value);
        getUiDevice().pressDPadCenter();
    }

    // Helper method for resetting the current cell position to the first column
    private void resetColumnPosition(final int nColumns) throws Exception {
        pressDPadDown();

        for (int i = 0; i < nColumns; ++i) {
            pressDPadLeft();
        }
    }

    // Helper method for highlighting the current cell's row and bringing up the format palette
    private void highlightRow() throws Exception {
        UiObject row = new UiObject(new UiSelector().resourceId("com.microsoft.office.excel:id/mainCanvas")
                                                    .childSelector(new UiSelector().index(0)
                                                    .childSelector(new UiSelector().index(0)
                                                    .childSelector(new UiSelector().index(0)
                                                    .childSelector(new UiSelector().index(2)
                                                    .childSelector(new UiSelector().index(0)))))));
        row.click();

        UiObject paletteToggleButton = getUiObjectByResourceId("com.microsoft.office.excel:id/paletteToggleButton",
                                                               "android.widget.Button");
        paletteToggleButton.click();
    }
}
