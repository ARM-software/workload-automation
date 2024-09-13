/*    Copyright 2024 ARM Limited
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

package com.arm.wa.uiauto.jetnews;

import androidx.test.jank.GfxMonitor;
import androidx.test.jank.JankTest;
import androidx.test.jank.JankTestBase;
import android.os.Bundle;

// UiAutomator 1 imports.
import androidx.test.uiautomator.UiScrollable;
import androidx.test.uiautomator.UiSelector;
import androidx.test.uiautomator.UiObject;

// UiAutomator 2 imports.
import androidx.test.uiautomator.By;
import androidx.test.uiautomator.Direction;
import androidx.test.uiautomator.UiDevice;
import androidx.test.uiautomator.UiObject2;
import androidx.test.uiautomator.Until;

import androidx.test.espresso.matcher.ViewMatchers;
import org.hamcrest.CoreMatchers;

import android.util.Log;

import java.util.Arrays;

import com.arm.wa.uiauto.ActionLogger;

// This class is responsible for actually running the UiAutomation
// tests and measuring the frame metrics. It will be invoked directly
// by workload-automation. We use an instance of UiAutomation so
// things get setup properly (parameters, screen orientation etc).

public class UiAutomationJankTests extends JankTestBase {
    private static final int DEFAULT_BENCHMARK_REPEAT_COUNT = 1;
    private static final int DEFAULT_TIMEOUT = 1000;
    private static final int DEFAULT_BENCHMARK_FLING_SPEED = 5000;
    private static final String[] DEFAULT_BENCHMARK_TESTS
        = {"PortraitVerticalTest",
           "PortraitHorizontalTest",
           "LandscapeVerticalTest"};
    private static final String PACKAGE_NAME = "com.example.jetnews";
    private static final String LOG_TAG = "JetNewsJankTests: ";

    private static final String MAIN_VIEW = "ArticlesMainScrollView";
    private static final String TOP_ARTICLE = "TopStoriesForYou";
    private static final String BOTTOM_ARTICLE = "PostCardHistory19";
    private static final String POPULAR_LIST = "PopularOnJetnewsRow";
    private static final String ARTICLE_VIEW = "ArticleHomeScreenPreview0";

    private UiAutomation mUiAutomation;
    private int repeat;
    private int fling_speed;
    private String[] tests;
    private UiDevice mDevice;
    private boolean testPortraitVertical;
    private boolean testPortraitHorizontal;
    private boolean testLandscapeVertical;

    @JankTest(
        expectedFrames = 100,
        defaultIterationCount = 1
    )

    @GfxMonitor(processName = PACKAGE_NAME)
    public void test1() throws Exception {
        for (int i = 0; i < repeat; i++) {
            if (testPortraitVertical) {
                ActionLogger logger
                    = new ActionLogger("PortraitVerticalTest",
                                       mUiAutomation.getParams());
                logger.start();
                runPortraitVerticalTests();
                logger.stop();
            }

            if (testPortraitHorizontal) {
                ActionLogger logger
                    = new ActionLogger("PortraitHorizontalTest",
                                       mUiAutomation.getParams());
                logger.start();
                runPortraitHorizontalTests();
                logger.stop();
            }

            if (testLandscapeVertical) {
                ActionLogger logger
                    = new ActionLogger("LandscapeVerticalTest",
                                       mUiAutomation.getParams());
                logger.start();
                runLandscapeVerticalTests();
                logger.stop();
            }
        }
    }

    private void runPortraitVerticalTests() throws Exception {
        // Scroll to the first postcard in the list.
        mDevice.wait(Until.findObject(By.res(MAIN_VIEW)), DEFAULT_TIMEOUT);
        UiObject2 articles = mDevice.findObject(By.res(MAIN_VIEW));
        ViewMatchers.assertThat(articles, CoreMatchers.notNullValue());

        scrollTo(articles, BOTTOM_ARTICLE, true, TOP_ARTICLE,
                 BOTTOM_ARTICLE, false, true, fling_speed);
        scrollTo(articles, TOP_ARTICLE, false, TOP_ARTICLE,
                 BOTTOM_ARTICLE, false, true, fling_speed);

        mDevice.click(articles.getVisibleCenter().x,
                      articles.getVisibleCenter().y);

        // Fling the article back and forth.
        UiObject2 article = mDevice.findObject(By.scrollable(true));

        article.fling(Direction.DOWN, fling_speed);
        article.fling(Direction.UP, fling_speed);

        // Go back to the main screen.
        mDevice.pressBack();
    }

    private void runPortraitHorizontalTests() throws Exception {
        mDevice.wait(Until.findObject(By.res(MAIN_VIEW)), DEFAULT_TIMEOUT);
        UiObject2 articles = mDevice.findObject(By.res(MAIN_VIEW));
        ViewMatchers.assertThat(articles, CoreMatchers.notNullValue());
        
        scrollTo(articles, TOP_ARTICLE, false, TOP_ARTICLE,
                 BOTTOM_ARTICLE, false, true, fling_speed);
        scrollTo(articles, POPULAR_LIST, true, TOP_ARTICLE,
                 BOTTOM_ARTICLE, false, true, 5000);
        
        UiObject2 article = mDevice.findObject(By.res(POPULAR_LIST));
        article.fling(Direction.RIGHT,
                      fling_speed > 10000? 10000 : fling_speed);
        article.fling(Direction.LEFT, fling_speed);
        scrollTo(articles, BOTTOM_ARTICLE, true, TOP_ARTICLE,
                 BOTTOM_ARTICLE, false, true, fling_speed);
    }

    private void runLandscapeVerticalTests() throws Exception {
        // Flip the screen sideways to exercise the other layout
        // of the Jetnews app.
        mDevice.setOrientationLandscape();
        mDevice.wait(Until.findObject(By.res(MAIN_VIEW)), DEFAULT_TIMEOUT);

        UiObject2 articles = mDevice.findObject(By.res(MAIN_VIEW));
        ViewMatchers.assertThat(articles, CoreMatchers.notNullValue());

        scrollTo(articles, BOTTOM_ARTICLE, true, TOP_ARTICLE,
                                        BOTTOM_ARTICLE, false, true,
                                        fling_speed);
        scrollTo(articles, TOP_ARTICLE, false, TOP_ARTICLE,
                                        BOTTOM_ARTICLE, false, true,
                                        fling_speed);
        
        // Wait for the clicked article to appear.
        UiObject2 article = mDevice.wait(
            Until.findObject(By.res(ARTICLE_VIEW)),
            DEFAULT_TIMEOUT
        );

        article.fling(Direction.DOWN, fling_speed);
        article.fling(Direction.UP, fling_speed);

        mDevice.setOrientationPortrait();
        mDevice.pressBack();
    }

    private void scrollTo(UiObject2 element,
                          String resourceId, boolean downFirst,
                          String beginningId, String endId, boolean sideways,
                          boolean fling, int swipeSpeed) {
        // First check if the resource is in view. If it is, then just return.
        if (element.hasObject(By.res(resourceId))) {
            Log.d(LOG_TAG, "Object " + resourceId + " was already in view.");
            return;
        }

        Direction direction;
        String markerId = downFirst? endId:beginningId;

        if (sideways) {
            direction = downFirst? Direction.RIGHT:Direction.LEFT;
        }
        else {
            direction = downFirst? Direction.DOWN:Direction.UP;
        }

        for (int i = 0; i < 2; i++) {
            // Scroll to find the object.
            Log.d(LOG_TAG,
                  "Object " + resourceId + " is not in view. Scrolling.");
            do {
                if (fling)
                    element.fling(direction, swipeSpeed);
                else
                    element.scroll(direction, 0.3f);

                // If we found it, just return. Otherwise keep going.
                if (element.findObject(By.res(resourceId)) != null) {
                    Log.d(LOG_TAG,
                          "Object " + resourceId + " found while scrolling.");
                    return;
                }

            } while (!mDevice.hasObject(By.res(markerId)));

            if (direction == Direction.DOWN)
                direction = Direction.UP;
            else if (direction == Direction.UP)
                direction = Direction.DOWN;
            else if (direction == Direction.RIGHT)
                direction = Direction.LEFT;
            else
                direction = Direction.RIGHT;

            Log.d(LOG_TAG, "Reached the limit at " + markerId + ".");

            if (markerId == beginningId)
                markerId = endId;
            else
                markerId = beginningId;
        }
        // We should've found it. If it is not here, it doesn't exist.
        return;
    }

    @Override
    public void setUp() throws Exception {
        super.setUp();

        Log.d(LOG_TAG, "Initializing UiAutomation object.");
        mUiAutomation = new UiAutomation ();
        mUiAutomation.initialize_instrumentation();
        mUiAutomation.initialize();
        mUiAutomation.setup();

        // Check the parameters and set sane defaults.
        mDevice = mUiAutomation.mDevice;
        Bundle parameters = mUiAutomation.getParams();

        repeat = parameters.getInt("repeat");
        Log.d(LOG_TAG,"Argument \"repeat\": " + String.valueOf (repeat));
        if (repeat <= 0) {
            repeat = DEFAULT_BENCHMARK_REPEAT_COUNT;
            Log.d(LOG_TAG, "Argument \"repeat\" initialized to default: " +
                  String.valueOf (DEFAULT_BENCHMARK_REPEAT_COUNT));
        }

        fling_speed = parameters.getInt("flingspeed");
        Log.d(LOG_TAG,
              "Argument \"flingspeed\": " + String.valueOf (fling_speed));
        if (fling_speed <= 1000 || fling_speed >= 30000) {
            fling_speed = DEFAULT_BENCHMARK_FLING_SPEED;
            Log.d(LOG_TAG, "Argument \"flingspeed\" initialized to default: " +
                  String.valueOf (DEFAULT_BENCHMARK_FLING_SPEED));
        }

        String[] tests = parameters.getStringArray("tests");
        if (tests == null) {
            tests = DEFAULT_BENCHMARK_TESTS;
            Log.d(LOG_TAG, "Argument \"tests\" initialized to default: " +
                  String.valueOf (DEFAULT_BENCHMARK_TESTS));
        }

        Arrays.sort (tests);
        testPortraitVertical
            = Arrays.binarySearch(tests,
                                  "PortraitVerticalTest") >= 0? true : false;
        testPortraitHorizontal
            = Arrays.binarySearch(tests,
                                  "PortraitHorizontalTest") >= 0? true : false;
        testLandscapeVertical
            = Arrays.binarySearch(tests,
                                  "LandscapeVerticalTest") >= 0? true : false;

        if (testPortraitVertical)
            Log.d(LOG_TAG, "Found PortraitVerticalTest");
        if (testPortraitHorizontal)
            Log.d(LOG_TAG, "Found PortraitHorizontalTest");
        if (testLandscapeVertical)
            Log.d(LOG_TAG, "Found LandscapeVerticalTest");
    }
}
