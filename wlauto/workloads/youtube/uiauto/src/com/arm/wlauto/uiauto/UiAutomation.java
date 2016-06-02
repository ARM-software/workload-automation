package com.arm.wlauto.uiauto.youtube;

import java.io.File;
import java.util.concurrent.TimeUnit;
import java.util.LinkedHashMap;
import java.util.Map;

import android.os.Bundle;
import android.os.SystemClock;
import android.util.Log;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_ID;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_TEXT;
import static com.arm.wlauto.uiauto.BaseUiAutomation.FindByCriteria.BY_DESC;

public class UiAutomation extends UxPerfUiAutomation {

    public static final String TAG = "youtube";
    public static final int WAIT_FOR_EXISTS_TIMEOUT = 1000;
    public static final int WAIT_OBJECT_TIMEOUT = 4; // in seconds
    public static final int VIDEO_SLEEP_SECONDS = 4;
    public static final String SOURCE_MY_VIDEOS = "my_videos";
    public static final String SOURCE_SEARCH = "search";
    public static final String SOURCE_TRENDING = "trending";
    public static final String[] STREAM_QUALITY = {
        "Auto", "144p", "240p", "360p", "480p", "720p", "1080p"
    };

    protected LinkedHashMap<String, Timer> results = new LinkedHashMap<String, Timer>();
    protected Bundle parameters;
    protected boolean dumpsysEnabled;
    protected String outputDir;
    protected String packageID;
    protected String searchTerm;

    public void runUiAutomation() throws Exception {
        parameters = getParams();
        packageID = parameters.getString("package") + ":id/";
        searchTerm = parameters.getString("search_term");
        if (searchTerm != null) {
            searchTerm = searchTerm.replaceAll("_", " ");
        }
        clearFirstRunDialogues();
        testPlayVideo(parameters.getString("video_source"), STREAM_QUALITY[1], searchTerm);
        if (false) {
            writeResultsToFile(results, parameters.getString("output_file"));
        }
    }

    public void clearFirstRunDialogues() throws Exception {
        UiObject laterButton = new UiObject(new UiSelector().textContains("Later").className("android.widget.TextView"));
        if (laterButton.waitForExists(WAIT_FOR_EXISTS_TIMEOUT)) {
           laterButton.click();
        }
        UiObject cancelButton = new UiObject(new UiSelector().textContains("Cancel").className("android.widget.Button"));
        if (cancelButton.waitForExists(WAIT_FOR_EXISTS_TIMEOUT)) {
            cancelButton.click();
        }
        UiObject skipButton = new UiObject(new UiSelector().textContains("Skip").className("android.widget.TextView"));
        if (skipButton.waitForExists(WAIT_FOR_EXISTS_TIMEOUT)) {
            skipButton.click();
        }
        UiObject gotItButton = new UiObject(new UiSelector().textContains("Got it").className("android.widget.Button"));
        if (gotItButton.waitForExists(WAIT_FOR_EXISTS_TIMEOUT)) {
            gotItButton.click();
        }
    }

    public void testPlayVideo(String source, String quality, String searchTerm) throws Exception {
        if (SOURCE_MY_VIDEOS.equalsIgnoreCase(source)) {
            clickUiObject(BY_DESC, "Account");
            clickUiObject(BY_TEXT, "My Videos", true);
            clickUiObject(BY_ID, packageID + "thumbnail", true);
        } else if (SOURCE_SEARCH.equalsIgnoreCase(source)) {
            clickUiObject(BY_DESC, "Search");
            UiObject textField = getUiObjectByResourceId(packageID + "search_edit_text");
            textField.setText(searchTerm);
            getUiDevice().pressEnter();
            clickUiObject(BY_ID, packageID + "thumbnail", true);
        } else { // trending videos
            clickUiObject(BY_DESC, "Trending");
            clickUiObject(BY_ID, packageID + "thumbnail", true);
        }
        seekForward();
        changeQuality(quality);
        makeFullscreen();
    }

    public void seekForward() throws Exception {
        clickUiObject(BY_ID, packageID + "player_fragment", "android.widget.FrameLayout");
        clickUiObject(BY_ID, packageID + "time_bar");
        sleep(VIDEO_SLEEP_SECONDS);
        // timebar.swipeRight(20);
        // sleep(VIDEO_SLEEP_SECONDS);
    }

    public void makeFullscreen() throws Exception {
        clickUiObject(BY_ID, packageID + "player_fragment", "android.widget.FrameLayout");
        clickUiObject(BY_ID, packageID + "fullscreen_button", true);
        sleep(VIDEO_SLEEP_SECONDS);
    }

    public void changeQuality(String quality) throws Exception {
        clickUiObject(BY_ID, packageID + "player_fragment", "android.widget.FrameLayout");
        clickUiObject(BY_DESC, "More options");
        clickUiObject(BY_ID, packageID + "quality_button", true);
        clickUiObject(BY_TEXT, "Auto");
        sleep(VIDEO_SLEEP_SECONDS);
        // UiCollection qualityList = new UiCollection(new UiSelector().resourceId(packageID + "select_dialog_listview"));
        // UiSelector qualitySelector = new UiSelector().className("android.widget.CheckedTextView").enabled(true);
        // qualityList.getChildByText(qualitySelector, quality);
    }

}
