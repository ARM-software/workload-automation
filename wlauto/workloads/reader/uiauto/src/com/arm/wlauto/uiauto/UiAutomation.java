package com.arm.wlauto.uiauto.reader;

import android.graphics.Rect;
import android.os.Bundle;
import android.os.SystemClock;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.core.UiCollection;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.io.File;
import java.io.FileWriter;
import java.io.BufferedWriter;
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
        Timer result = new Timer();
        result.start();
        parameters = getParams();

        dismissWelcomeView();

        signInOnline(parameters);

        confirmLocalFileAccess();

        gesturesTest("Getting Started.pdf");

        String [] searchStrings = {"Glossary", "cortex"};
        searchPdfTest("cortex_m4", searchStrings);

        result.end();
        timingResults.put("Total", result);

        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    private void dismissWelcomeView() throws Exception {
        UiObject welcomeView = getUiObjectByDescription("Acrobat - First Time Experience",
                                                        "android.webkit.WebView");
        // Click through the first two pages and wait for pages to transition.
        // These pages are webkit views so clickAndWaitForNewWindow or waitForExists cannot be used
        tapDisplayCentre();
        sleep(1);
        tapDisplayCentre();
        sleep(1);

        // Get the box coords for the webView window
        Rect webViewCoords = welcomeView.getBounds();

        // Iterate up from the bottom middle of the webView until we hit these
        // Continue button and change view
        int i = 0;
        do {
            i += 10;
            tapDisplay(webViewCoords.centerX(), webViewCoords.centerY() + i);
        } while ( welcomeView.exists() || i < webViewCoords.top  );
    }

    private void signInOnline(Bundle parameters) throws Exception {
        String email = parameters.getString("email");
        String password = parameters.getString("password");

        UiObject homeButton = getUiObjectByResourceId("android:id/home", "android.widget.ImageView");
        homeButton.clickAndWaitForNewWindow();

        UiObject firstSignInButton = getUiObjectByResourceId("com.adobe.reader:id/user_info_title",
                                                             "android.widget.TextView");
        firstSignInButton.clickAndWaitForNewWindow();

        // resourceId cannot be trusted  across different devices in this view so use description
        // and indexes instead
        UiObject secondSignInButton = getUiObjectByDescription("Sign In", "android.view.View");
        secondSignInButton.clickAndWaitForNewWindow();

        UiObject emailBox = new UiObject(new UiSelector().className("android.webkit.WebView")
                                                .description("Sign in - Adobe ID")
                                                .childSelector(new UiSelector()
                                                .index(0).className("android.view.View")
                                                .childSelector(new UiSelector()
                                                .index(1).className("android.view.View")
                                                .childSelector(new UiSelector()
                                                .index(0).className("android.view.View")
                                                .childSelector(new UiSelector()
                                                .index(0).className("android.widget.EditText"))))));
        emailBox.setText(email);
        UiObject passwordBox = new UiObject(new UiSelector().className("android.webkit.WebView")
                                                .description("Sign in - Adobe ID")
                                                .childSelector(new UiSelector()
                                                .index(0).className("android.view.View")
                                                .childSelector(new UiSelector()
                                                .index(1).className("android.view.View")
                                                .childSelector(new UiSelector()
                                                .index(1).className("android.view.View")
                                                .childSelector(new UiSelector()
                                                .index(0).className("android.widget.EditText"))))));
        passwordBox.setText(password);
        UiObject lastSignInButton = new UiObject(new UiSelector().className("android.webkit.WebView")
                                                .description("Sign in - Adobe ID")
                                                .childSelector(new UiSelector()
                                                .index(0).className("android.view.View")
                                                .childSelector(new UiSelector()
                                                .index(1).className("android.view.View")
                                                .childSelector(new UiSelector()
                                                .index(3).className("android.view.View")
                                                .childSelector(new UiSelector()
                                                .index(0).className("android.widget.Button"))))));
        lastSignInButton.clickAndWaitForNewWindow();

        UiObject upButton = new UiObject(new UiSelector().resourceId("android:id/up")
                                                         .className("android.widget.ImageView"));
        if (upButton.waitForExists(TimeUnit.SECONDS.toMillis(networkTimeout))) {
            upButton.clickAndWaitForNewWindow();
        }
    }

    private void confirmLocalFileAccess() throws Exception {
        // First time run requires confirmation to allow access to local files
        UiObject allowButton = new UiObject(new UiSelector().textContains("Allow")
                                                            .className("android.widget.Button"));
        if (allowButton.waitForExists(timeout)) {
            allowButton.clickAndWaitForNewWindow(timeout);
        };
    }

    private void openFile(String filename) throws Exception {

        String TestTag = "openfile";

        // Replace whitespace and full stops within the filename
        String file = filename.replaceAll("\\.", "_").replaceAll("\\s+", "_");

        timingResults.put(String.format(TestTag + "_" + "selectLocalFilesList" + "_" + file), selectLocalFilesList());
        timingResults.put(String.format(TestTag + "_" + "selectSearchDuration" + "_" + file), selectSearchFileButton());
        timingResults.put(String.format(TestTag + "_" + "searchFileList" + "_" + file), searchFileList(filename));
        timingResults.put(String.format(TestTag + "_" + "openFileFromList" + "_" + file), openFileFromList(filename));

        // Cludge to get rid of the first time run help dialogue boxes
        tapDisplayCentre();
        sleep(1);
        tapDisplayCentre();
        sleep(1);
    }

    private Timer selectLocalFilesList() throws Exception {
        // Select the local files list from the My Documents view
        UiObject localButton = getUiObjectByText("LOCAL", "android.widget.TextView");
        Timer result = new Timer();
        result.start();
        localButton.clickAndWaitForNewWindow(timeout);
        long finish = SystemClock.elapsedRealtime();
        result.end();
        return result;
    }

    private Timer selectSearchFileButton() throws Exception {
        // Click the button to search from the present file list view
        UiObject searchButton = getUiObjectByResourceId("com.adobe.reader:id/split_pane_search",
                                                        "android.widget.TextView");
        Timer result = new Timer();
        result.start();
        searchButton.click();
        long finish = SystemClock.elapsedRealtime();
        result.end();
        return result;
    }

    private Timer searchFileList(String searchText) throws Exception {
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

    private Timer openFileFromList(String file) throws Exception {
        // Open a file from a file list view by searching for UiObjects containing the doc title.
        UiObject fileObject = getUiObjectByText(file, "android.widget.TextView");
        Timer result = new Timer();
        result.start();
        fileObject.clickAndWaitForNewWindow(timeout);
        result.end();

        // Wait for the doc to open by waiting for the viewPager UiObject to exist
        UiObject viewPager = new UiObject(new UiSelector().resourceId("com.adobe.reader:id/viewPager"));
        if (!viewPager.waitForExists(timeout)) {
            throw new UiObjectNotFoundException("Could not find \"viewPager\".");
        };
        return result;
    }

    private class GestureTestParams {
        GestureType gestureType;
        Direction gestureDirection;
        PinchType pinchType;
        int percent;
        int steps;

        GestureTestParams(GestureType gesture, Direction direction, int steps) {
            this.gestureType = gesture;
            this.gestureDirection = direction;
            this.pinchType = PinchType.NULL;
            this.steps = steps;
            this.percent = 0;
        }

        GestureTestParams(GestureType gesture, PinchType pinchType, int steps, int percent) {
            this.gestureType = gesture;
            this.gestureDirection = Direction.NULL;
            this.pinchType = pinchType;
            this.steps = steps;
            this.percent = percent;
        }
    }

    private void gesturesTest (String filename) throws Exception {

        String TestTag = "gestures";

        // Perform a range of swipe tests at different speeds and on different views
        LinkedHashMap<String, GestureTestParams> testParams = new LinkedHashMap<String, GestureTestParams>();
        testParams.put("1", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.DOWN, 100));
        testParams.put("2", new GestureTestParams(GestureType.UIDEVICE_SWIPE, Direction.UP, 100));
        testParams.put("3", new GestureTestParams(GestureType.UIOBJECT_SWIPE, Direction.RIGHT, 50));
        testParams.put("4", new GestureTestParams(GestureType.UIOBJECT_SWIPE, Direction.LEFT, 50));
        testParams.put("5", new GestureTestParams(GestureType.PINCH, PinchType.OUT, 100, 200));
        testParams.put("6", new GestureTestParams(GestureType.PINCH, PinchType.IN, 100, 50));

        Iterator<Entry<String, GestureTestParams>> it = testParams.entrySet().iterator();

        openFile(filename);

        while (it.hasNext()) {
            Map.Entry<String, GestureTestParams> pair = it.next();
            GestureType type = pair.getValue().gestureType;
            Direction dir = pair.getValue().gestureDirection;
            PinchType pinch = pair.getValue().pinchType;
            int steps = pair.getValue().steps;
            int percent = pair.getValue().percent;

            String runName = String.format(TestTag + "_" + pair.getKey());
            String gfxInfologName =  String.format(TAG + "_" + runName + "_gfxInfo.log");
            String surfFlingerlogName =  String.format(runName + "_surfFlinger.log");
            String viewName = new String("com.adobe.reader.viewer.ARViewerActivity");

            UiObject view = new UiObject(new UiSelector().resourceId("com.adobe.reader:id/viewPager"));

            startDumpsysGfxInfo();
            startDumpsysSurfaceFlinger(viewName);

            Timer results = new Timer();

            switch (type) {
                case UIDEVICE_SWIPE:
                    results = uiDeviceSwipeTest(dir, steps);
                    break;
                case UIOBJECT_SWIPE:
                    results = uiObjectSwipeTest(view, dir, steps);
                    break;
                case PINCH:
                    results = uiObjectPinchTest(view, pinch, steps, percent);
                    break;
                default:
                    break;
            }

            stopDumpsysSurfaceFlinger(viewName, surfFlingerlogName);
            stopDumpsysGfxInfo(gfxInfologName);

            timingResults.put(runName, results);
        }

        exitDocument();
    }

    private void searchPdfTest (String filename, String [] searchStrings) throws Exception {

        String TestTag = "search";

        openFile(filename);

        // Get the page view for the opened document which we can use for pinch actions
        UiObject pageView = getUiObjectByResourceId("com.adobe.reader:id/pageView",
                                                    "android.widget.RelativeLayout");
        for ( int i=0; i < searchStrings.length; i++) {
            timingResults.put(String.format(TestTag + "_" + i),
                                            searchTest(searchStrings[i]));
        }

        exitDocument();
    }

    private Timer searchTest(String searchText) throws Exception {
        // Click on the search button icon and enter text in the box.  This closes the keyboad
        // so click the box again and press Enter to start the search.
        UiObject searchButton = getUiObjectByResourceId("com.adobe.reader:id/document_view_search_icon",
                                                        "android.widget.TextView");
        searchButton.clickAndWaitForNewWindow();
        UiObject searchBox = getUiObjectByResourceId("android:id/search_src_text",
                                                     "android.widget.EditText");
        searchBox.setText(searchText);
        searchBox.click();
        Timer result = new Timer();
        result.start();
        getUiDevice().getInstance().pressEnter();

        // Check the progress bar icon.  When this disappears the search is complete.
        UiObject progressBar = new UiObject(new UiSelector().resourceId("com.adobe.reader:id/searchProgress")
                                                            .className("android.widget.ProgressBar"));
        progressBar.waitForExists(timeout);
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
        if (!homeButton.waitForExists(timeout)) {
            tapDisplayCentre();
        }
        homeButton.clickAndWaitForNewWindow();
        UiObject myDocsButton = getUiObjectByDescription("My Documents", "android.widget.LinearLayout" );
        myDocsButton.clickAndWaitForNewWindow();
        UiObject upButton = getUiObjectByResourceId("android:id/up", "android.widget.ImageView" );
        upButton.clickAndWaitForNewWindow();
    }

    private void writeResultsToFile(LinkedHashMap timingResults, String file) throws Exception {
        // Write out the key/value pairs to the instrumentation log file
        FileWriter fstream = new FileWriter(file);
        BufferedWriter out = new BufferedWriter(fstream);
        Iterator<Entry<String, Timer>> it = timingResults.entrySet().iterator();

        while (it.hasNext()) {
            Map.Entry<String, Timer> pairs = it.next();
            Timer results = pairs.getValue();
            long start = results.getStart();
            long finish = results.getFinish();
            long duration = results.getDuration();
            out.write(String.format(pairs.getKey() + " " + start + " " + finish + " " + duration + "\n"));
        }
        out.close();
    }

    private void startDumpsysSurfaceFlinger(String view) {
        if (Boolean.parseBoolean(parameters.getString("dumpsys_enabled"))) {
            initDumpsysSurfaceFlinger(parameters.getString("package"), view);
        }
    }

    private void stopDumpsysSurfaceFlinger(String view, String filename) throws Exception {
        if (Boolean.parseBoolean(parameters.getString("dumpsys_enabled"))) {
            File out_file = new File(parameters.getString("output_dir"), filename);
            exitDumpsysSurfaceFlinger(parameters.getString("package"), view, out_file);
          }
    }

    private void startDumpsysGfxInfo() {
        if (Boolean.parseBoolean(parameters.getString("dumpsys_enabled"))) {
            initDumpsysGfxInfo(parameters.getString("package"));
          }
    }

    private void stopDumpsysGfxInfo(String filename) throws Exception {
      if (Boolean.parseBoolean(parameters.getString("dumpsys_enabled"))) {
            File out_file = new File(parameters.getString("output_dir"), filename);
            exitDumpsysGfxInfo(parameters.getString("package"), out_file);
          }
    }
}
