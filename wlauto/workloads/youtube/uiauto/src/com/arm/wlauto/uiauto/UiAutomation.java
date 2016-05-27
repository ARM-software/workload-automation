package com.arm.wlauto.uiauto.youtube;

import android.os.Bundle;
import android.os.SystemClock;

// Import the uiautomator libraries
import com.android.uiautomator.core.UiObject;
import com.android.uiautomator.core.UiObjectNotFoundException;
import com.android.uiautomator.core.UiScrollable;
import com.android.uiautomator.core.UiSelector;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;

import android.util.Log;

import com.arm.wlauto.uiauto.UxPerfUiAutomation;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.util.concurrent.TimeUnit;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Map.Entry;

public class UiAutomation extends UxPerfUiAutomation {

    public static String TAG = "uxperf_youtube";

    private Bundle parameters;
    private long networkTimeout =  TimeUnit.SECONDS.toMillis(20);
    private LinkedHashMap<String, Timer> timingResults = new LinkedHashMap<String, Timer>();

    private String [] streamQuality = {"Auto", "144p", "240p", "360p", "480p", "720p", "1080p"};

    public void runUiAutomation() throws Exception {
        parameters = getParams();

        Timer result = new Timer();
        result.start();

        clearFirstRunDialogues();
        selectFirstVideo();
        seekForward();
        // changeQuality(streamQuality[1]);
        makeFullscreen();

        result.end();
        timingResults.put("Total", result);

        writeResultsToFile(timingResults, parameters.getString("output_file"));
    }

    public void clearFirstRunDialogues() throws Exception {
        UiObject laterButton = getUiObjectByResourceId("com.google.android.youtube:id/later_button",
                                                     "android.widget.TextView");
        if (laterButton.exists()) {
           clickUiObject(laterButton, timeout);
        }

        UiObject skipButton = new UiObject (new UiSelector().textContains("Skip")
                                                             .className("android.widget.TextView"));
        if (skipButton.exists()) {
          clickUiObject(skipButton, timeout);
        }

        UiObject gotItButton = new UiObject (new UiSelector().textContains("Got it")
                                                             .className("android.widget.Button"));
        gotItButton.waitForExists(timeout);
        if (gotItButton.exists()) {
            gotItButton.click();
        }

    }


    public void selectFirstVideo() throws Exception {

        UiObject navigateUpButton = new UiObject (new UiSelector().descriptionContains("Navigate up")
                                                                  .className("android.widget.ImageButton"));
        UiObject myAccount = new UiObject (new UiSelector().descriptionContains("Account")
                                                            .className("android.widget.Button"));

        if (navigateUpButton.exists()) {
            navigateUpButton.click();
            UiObject uploads = getUiObjectByText("Uploads", "android.widget.TextView");
            waitObject(uploads, 4);
            uploads.click();
            UiObject firstEntry = new UiObject (new UiSelector().resourceId("com.google.android.youtube:id/paged_list")
                                                                .className("android.widget.ListView")
                                                                .childSelector(new UiSelector()
                                                                .index(0).className("android.widget.LinearLayout")));
            waitObject(firstEntry, 4);
            firstEntry.click();
        } else {
            waitObject(myAccount, 4);
            myAccount.click();
            UiObject myVideos = getUiObjectByText("My videos", "android.widget.TextView");
            waitObject(myVideos, 4);
            myVideos.click();
            UiObject firstEntry = new UiObject (new UiSelector().resourceId("com.google.android.youtube:id/compact_video_item")
                                                                .className("android.widget.LinearLayout"));
            waitObject(firstEntry, 4);
            firstEntry.click();
        }

        sleep(4);
    }

    public void makeFullscreen() throws Exception {
        UiObject fullscreenButton = getUiObjectByResourceId("com.google.android.youtube:id/fullscreen_button",
                                                            "android.widget.ImageView");
        UiObject viewGroup =  new UiObject (new UiSelector().resourceId("com.google.android.youtube:id/player_fragment")
                                                            .className("android.widget.FrameLayout"));
        viewGroup.click();
        waitObject(fullscreenButton, 4);
        fullscreenButton.click();
        sleep(4);
    }

    public void seekForward() throws Exception {
        UiObject timebar = new UiObject (new UiSelector().resourceId("com.google.android.youtube:id/time_bar")
                                                         .className("android.view.View"));
        UiObject viewGroup =  new UiObject (new UiSelector().resourceId("com.google.android.youtube:id/player_fragment")
                                                            .className("android.widget.FrameLayout"));
        viewGroup.click();
        waitObject(timebar, 4);
        timebar.click();
        sleep(4);
        // timebar.swipeRight(20);
        // sleep(2);
    }

    public void changeQuality(String quality) throws Exception {
        UiObject viewGroup =  new UiObject (new UiSelector().resourceId("com.google.android.youtube:id/player_fragment")
                                                     .className("android.widget.FrameLayout"));
        viewGroup.click();

        UiObject moreOptions =  new UiObject (new UiSelector().resourceId("com.google.android.youtube:id/player_overflow_button")
                                                     .className("android.widget.ImageView"));

        UiObject miniPlayerViewGroup =  new UiObject (new UiSelector().resourceId("com.google.android.youtube:id/watch_player")
                                                    .className("android.view.ViewGroup"));
        UiObject miniPlayerViewLayout =  new UiObject (new UiSelector().resourceId("com.google.android.youtube:id/watch_player")
                                                     .className("android.widget.FrameLayout"));

        // UiObject qualityButton =  new UiObject (new UiSelector().resourceId("com.google.android.youtube:id/quality_button_text")
        //                                              .className("android.widget.TextView"));

        // UiObject qualityButton =  new UiObject (new UiSelector().resourceId("com.google.android.youtube:id/watch_player")
        //                                              .className("android.view.ViewGroup")
        //                                                 .childSelector(new UiSelector()
        //                                                 .index(1).className("android.widget.FrameLayout")
        //                                                 .childSelector(new UiSelector()
        //                                                 .index(0).className("android.widget.FrameLayout")
        //                                                 .childSelector(new UiSelector()
        //                                                 .index(0).className("android.widget.RelativeLayout")
        //                                                 .childSelector(new UiSelector()
        //                                                 .index(1).className("android.widget.RelativeLayout")
        //                                                 .childSelector(new UiSelector()
        //                                                 .index(1).className("android.widget.ImageView")))))));


        UiObject qualityButton =  new UiObject (new UiSelector().descriptionContains("Show video quality menu"));


        UiObject qualitySetting =  new UiObject (new UiSelector().resourceId(quality)
                                                     .className("android.widget.CheckedTextView"));

        Log.v(TAG, String.format("MADE IT HERE"));

        waitObject(moreOptions, 4);
        moreOptions.click();


        if (miniPlayerViewGroup.exists()) {
            // MATE 8
            // miniPlayerViewGroup.click();
            UiObject frameLayout =  miniPlayerViewGroup.getChild(new UiSelector()
                                                            .index(1).className("android.widget.FrameLayout")
                                                            .childSelector(new UiSelector()
                                                            ));
        } else {
            // ZENFONE

            if (qualityButton.exists()) {
                qualityButton.click();
            }

            UiObject frameLayout =  miniPlayerViewLayout.getChild(new UiSelector()
                                                            .index(1).className("android.widget.FrameLayout")
                                                            .childSelector(new UiSelector()
                                                            ));
            int count = frameLayout.getChildCount();
            Log.v(TAG, String.format("ChildCount: %s", count));

            for (int i = 0; i < count ; i++) {
                String className = frameLayout.getChild(new UiSelector().index(i)).getClassName();
                String description = frameLayout.getChild(new UiSelector().index(i)).getContentDescription();
                Log.v(TAG, String.format("Child %s ClassName: %s %s", i, className, description));
            }
            throw new UiObjectNotFoundException(String.format("child count: %s", count));
        }

        // waitObject(qualityButton, 4);
        // qualityButton.click();
        // waitObject(qualitySetting, 4);
        // qualitySetting.click();

        // seekForward();
    }

}
