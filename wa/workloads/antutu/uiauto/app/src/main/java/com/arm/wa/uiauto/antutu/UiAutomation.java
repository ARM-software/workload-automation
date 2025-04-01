/*    Copyright 2013-2018 ARM Limited
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


package com.arm.wa.uiauto.antutu;

import android.app.Activity;
import android.os.Bundle;
import android.support.test.runner.AndroidJUnit4;
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;
import android.util.Log;

import com.arm.wa.uiauto.BaseUiAutomation;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.TimeUnit;

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends BaseUiAutomation {

    public static String TAG = "UXPERF";
    public static String TestButton5 = "com.antutu.ABenchMark:id/start_test_region";
    public static String TestButton6 = "com.antutu.ABenchMark:id/start_test_text";
    private static int initialTimeoutSeconds = 20;
    protected Bundle parameters;
    protected String version;

    @Before
    public void initialize(){
        parameters = getParams();
        version = parameters.getString("version");
    }

    @Test
    public void setup() throws Exception {
       dismissAndroidVersionPopup();
       clearPopups();
    }

    @Test
    public void runWorkload() throws Exception{
        hitTest();
        waitforCompletion();
    }

    @Test
    public void extractResults() throws Exception{
        if (version.startsWith("10")){
            getScoresv10();
        } else if (version.startsWith("9")){
            getScoresv9();
        } else if (version.startsWith("8")){
            getScoresv8();
        } else {
            getScoresv7();
        }
    }

    public void hitTest() throws Exception {
        UiObject testbutton =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/main_test_start_title"));
        testbutton.click();
        sleep(1);
    }

    public void clearPopups() throws Exception {
        //Refuse the first popup and accept the second as the first accept does not work
        UiObject refuse = 
            mDevice.findObject(new UiSelector().textContains("Refuse"));
        if (refuse.exists()){
            refuse.click();
        }
        UiObject accept = 
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/start_privacy_policy_preview_ok"));
        if (accept.exists()){
            Log.d(TAG, "Accept exists");
            accept.click();
            Log.d(TAG, "Accept clicked");
        }

        //Some devices present a whitelist - allow the benchmark to use the network
        UiObject whitelist =
            mDevice.findObject(new UiSelector().text("ALLOW"));
        if (whitelist.exists()){
            whitelist.click();
        }

        UiObject agreement = 
            mDevice.findObject(new UiSelector().textContains("NEXT"));
        agreement.waitForExists(5000);
        if (agreement.exists()){
            agreement.click();
        }

        UiObject cancel =
            mDevice.findObject(new UiSelector().textContains("CANCEL"));
        cancel.waitForExists(5000);
        if (cancel.exists()){
            cancel.click();
        }
    }

    public void clearChainStartPopup() throws Exception {
        UiObject accept =
            mDevice.findObject(new UiSelector().textContains("Accept"));
        accept.waitForExists(5000);
        if (accept.exists()){
            accept.click();
        }
    }

    public void waitforCompletion() throws Exception {
        clearChainStartPopup();
        //Wait up to twenty minutes for the benchmark to complete
        if (version.startsWith("10")){
            UiObject totalScore =
                mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/TextViewScoreValue"));
            totalScore.waitForExists(12000000);
        } else {
            UiObject totalScore =
                mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/textViewTotalScore"));
            totalScore.waitForExists(12000000);
	}
    }

    public void getScoresv7() throws Exception {
        //Expand, Extract and Close CPU sub scores
        UiObject cpuscores =
            mDevice.findObject(new UiSelector().text("CPU"));
        cpuscores.click();
        UiObject cpumaths =
            mDevice.findObject(new UiSelector().text("CPU Mathematics Score").fromParent(new UiSelector().index(3)));
        UiObject cpucommon =
            mDevice.findObject(new UiSelector().text("CPU Common Use Score").fromParent(new UiSelector().index(3)));
        UiObject cpumulti =
            mDevice.findObject(new UiSelector().text("CPU Multi-Core Score").fromParent(new UiSelector().index(3)));
        Log.d(TAG, "CPU Maths Score " + cpumaths.getText());
        Log.d(TAG, "CPU Common Score " + cpucommon.getText());
        Log.d(TAG, "CPU Multi Score " + cpumulti.getText());
        cpuscores.click();

        //Expand, Extract and Close GPU sub scores
        UiObject gpuscores =
            mDevice.findObject(new UiSelector().text("GPU"));
        gpuscores.click();
        UiObject gpumaroon =
            mDevice.findObject(new UiSelector().text("3D [Marooned] Score").fromParent(new UiSelector().index(3)));
        UiObject gpucoast =
            mDevice.findObject(new UiSelector().text("3D [Coastline] Score").fromParent(new UiSelector().index(3)));
        UiObject gpurefinery =
            mDevice.findObject(new UiSelector().text("3D [Refinery] Score").fromParent(new UiSelector().index(3)));
        Log.d(TAG, "GPU Marooned Score " + gpumaroon.getText());
        Log.d(TAG, "GPU Coastline Score " + gpucoast.getText());
        Log.d(TAG, "GPU Refinery Score " + gpurefinery.getText());
        gpuscores.click();

        //Expand, Extract and Close UX sub scores
        UiObject uxscores =
            mDevice.findObject(new UiSelector().text("UX"));
        uxscores.click();
        UiObject security =
            mDevice.findObject(new UiSelector().text("Data Security Score").fromParent(new UiSelector().index(3)));
        UiObject dataprocessing =
            mDevice.findObject(new UiSelector().text("Data Processing Score").fromParent(new UiSelector().index(3)));
        UiObject imageprocessing =
            mDevice.findObject(new UiSelector().text("Image Processing Score").fromParent(new UiSelector().index(3)));
        UiObject uxscore =
            mDevice.findObject(new UiSelector().text("User Experience Score").fromParent(new UiSelector().index(3)));
        Log.d(TAG, "Data Security Score " + security.getText());
        Log.d(TAG, "Data Processing Score " + dataprocessing.getText());
        Log.d(TAG, "Image Processing Score " + imageprocessing.getText());
        Log.d(TAG, "User Experience Score " + uxscore.getText());
        uxscores.click();

        //Expand, Extract and Close MEM sub scores
        UiObject memscores =
            mDevice.findObject(new UiSelector().text("MEM"));
        memscores.click();
        UiObject ramscore =
            mDevice.findObject(new UiSelector().text("RAM Score").fromParent(new UiSelector().index(3)));
        UiObject romscore =
            mDevice.findObject(new UiSelector().text("ROM Score").fromParent(new UiSelector().index(3)));
        Log.d(TAG, "RAM Score " + ramscore.getText());
        Log.d(TAG, "ROM Score " + romscore.getText());
        memscores.click();
    }

    public void getScoresv8() throws Exception {
        UiScrollable list = new UiScrollable(new UiSelector().scrollable(true));

        //Expand, Extract and Close CPU sub scores
        UiObject cpuscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/result_details_recyclerView"))
            .getChild(new UiSelector().index(2))
            .getChild(new UiSelector().index(4));
        cpuscores.click();
        UiObject cpumaths =
            mDevice.findObject(new UiSelector().text("CPU Mathematical Operations").fromParent(new UiSelector().index(1)));
        UiObject cpucommon =
            mDevice.findObject(new UiSelector().text("CPU Common Algorithms").fromParent(new UiSelector().index(1)));
        UiObject cpumulti =
            mDevice.findObject(new UiSelector().text("CPU Multi-Core").fromParent(new UiSelector().index(1)));
        Log.d(TAG, "CPU Mathematical Operations Score " + cpumaths.getText());
        Log.d(TAG, "CPU Common Algorithms Score " + cpucommon.getText());
        Log.d(TAG, "CPU Multi-Core Score " + cpumulti.getText());
        cpuscores.click();

        //Expand, Extract and Close GPU sub scores
        UiObject gpuscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/result_details_recyclerView"))
            .getChild(new UiSelector().index(3))
            .getChild(new UiSelector().index(4));
        gpuscores.click();
        UiObject gputerracotta =
            mDevice.findObject(new UiSelector().text("Terracotta - Vulkan").fromParent(new UiSelector().index(1)));
        UiObject gpucoast =
            mDevice.findObject(new UiSelector().text("Coastline - Vulkan").fromParent(new UiSelector().index(1)));
        UiObject gpurefinery =
            mDevice.findObject(new UiSelector().text("Refinery - OpenGL ES3.1+AEP").fromParent(new UiSelector().index(1)));
        Log.d(TAG, "GPU Terracotta Score " + gputerracotta.getText());
        Log.d(TAG, "GPU Coastline Score " + gpucoast.getText());
        Log.d(TAG, "GPU Refinery Score " + gpurefinery.getText());
        gpuscores.click();

        //Expand, Extract and Close UX sub scores
        UiObject uxscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/result_details_recyclerView"))
            .getChild(new UiSelector().index(5))
            .getChild(new UiSelector().index(4));
        uxscores.click();
        UiObject security =
            mDevice.findObject(new UiSelector().text("Data Security").fromParent(new UiSelector().index(1)));
        UiObject dataprocessing =
            mDevice.findObject(new UiSelector().text("Data Processing").fromParent(new UiSelector().index(1)));
        UiObject imageprocessing =
            mDevice.findObject(new UiSelector().text("Image Processing").fromParent(new UiSelector().index(1)));
        UiObject uxscore =
            mDevice.findObject(new UiSelector().text("User Experience").fromParent(new UiSelector().index(1)));
        if (!security.exists() && list.waitForExists(60)) {
            list.scrollIntoView(security);
        }
        Log.d(TAG, "Data Security Score " + security.getText());
        if (!dataprocessing.exists() && list.waitForExists(60)) {
            list.scrollIntoView(dataprocessing);
        }
        Log.d(TAG, "Data Processing Score " + dataprocessing.getText());
        if (!imageprocessing.exists() && list.waitForExists(60)) {
            list.scrollIntoView(imageprocessing);
        }
        Log.d(TAG, "Image Processing Score " + imageprocessing.getText());
        if (!uxscore.exists() && list.waitForExists(60)) {
            list.scrollIntoView(uxscore);
        }
        Log.d(TAG, "User Experience Score " + uxscore.getText());
        list.scrollToBeginning(10);
        uxscores.click();

        //Expand, Extract and Close MEM sub scores
        UiObject memscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/result_details_recyclerView"))
            .getChild(new UiSelector().index(4))
            .getChild(new UiSelector().index(4));
        memscores.click();
        UiObject ramaccess =
            mDevice.findObject(new UiSelector().text("RAM Access").fromParent(new UiSelector().index(1)));
        UiObject romapp =
            mDevice.findObject(new UiSelector().text("ROM APP IO").fromParent(new UiSelector().index(1)));
        UiObject romread =
            mDevice.findObject(new UiSelector().text("ROM Sequential Read").fromParent(new UiSelector().index(1)));
        UiObject romwrite =
            mDevice.findObject(new UiSelector().text("ROM Sequential Write").fromParent(new UiSelector().index(1)));
        UiObject romaccess =
            mDevice.findObject(new UiSelector().text("ROM Random Access").fromParent(new UiSelector().index(1)));
       if (!ramaccess.exists() && list.waitForExists(60)) {
            list.scrollIntoView(ramaccess);
        }
        Log.d(TAG, "RAM Access Score " + ramaccess.getText());
       if (!romapp.exists() && list.waitForExists(60)) {
            list.scrollIntoView(romapp);
        }
        Log.d(TAG, "ROM APP IO Score " + romapp.getText());
        if (!romread.exists() && list.waitForExists(60)) {
            list.scrollIntoView(romread);
        }
        Log.d(TAG, "ROM Sequential Read Score " + romread.getText());
        if (!romwrite.exists() && list.waitForExists(60)) {
            list.scrollIntoView(romwrite);
        }
        Log.d(TAG, "ROM Sequential Write Score " + romwrite.getText());
        if (!romaccess.exists() && list.waitForExists(60)) {
            list.scrollIntoView(romaccess);
        }
        Log.d(TAG, "ROM Random Access Score " + romaccess.getText());
        list.scrollToBeginning(10);        
        memscores.click();
    }

    public void getScoresv9() throws Exception {
        UiScrollable list = new UiScrollable(new UiSelector().scrollable(true));

        //Expand, Extract and Close CPU sub scores
        UiObject cpuscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/result_details_recyclerView"))
            .getChild(new UiSelector().index(2))
            .getChild(new UiSelector().index(4));
        cpuscores.click();
        UiObject cpumaths =
            mDevice.findObject(new UiSelector().text("CPU Mathematical Operations").fromParent(new UiSelector().index(1)));
        UiObject cpucommon =
            mDevice.findObject(new UiSelector().text("CPU Common Algorithms").fromParent(new UiSelector().index(1)));
        UiObject cpumulti =
            mDevice.findObject(new UiSelector().text("CPU Multi-Core").fromParent(new UiSelector().index(1)));
        Log.d(TAG, "CPU Mathematical Operations Score " + cpumaths.getText());
        Log.d(TAG, "CPU Common Algorithms Score " + cpucommon.getText());
        Log.d(TAG, "CPU Multi-Core Score " + cpumulti.getText());
        cpuscores.click();

        //Expand, Extract and Close GPU sub scores
        UiObject gpuscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/result_details_recyclerView"))
            .getChild(new UiSelector().index(3))
            .getChild(new UiSelector().index(4));
        gpuscores.click();
        UiObject gputerracotta =
            mDevice.findObject(new UiSelector().text("Terracotta - Vulkan").fromParent(new UiSelector().index(1)));
        UiObject gpuswordsman =
            mDevice.findObject(new UiSelector().text("Swordsman - Vulkan").fromParent(new UiSelector().index(1)));
        UiObject gpurefinery =
            mDevice.findObject(new UiSelector().text("Refinery - OpenGL ES3.1+AEP").fromParent(new UiSelector().index(1)));
        Log.d(TAG, "GPU Terracotta Score " + gputerracotta.getText());
        Log.d(TAG, "GPU Swordsman Score " + gpuswordsman.getText());
        Log.d(TAG, "GPU Refinery Score " + gpurefinery.getText());
        gpuscores.click();

        //Expand, Extract and Close UX sub scores
        UiObject uxscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/result_details_recyclerView"))
            .getChild(new UiSelector().index(5))
            .getChild(new UiSelector().index(4));
        uxscores.click();
        UiObject security =
            mDevice.findObject(new UiSelector().text("Data Security").fromParent(new UiSelector().index(1)));
        UiObject dataprocessing =
            mDevice.findObject(new UiSelector().text("Data Processing").fromParent(new UiSelector().index(1)));
        UiObject imageprocessing =
            mDevice.findObject(new UiSelector().text("Image Processing").fromParent(new UiSelector().index(1)));
        UiObject uxscore =
            mDevice.findObject(new UiSelector().text("User Experience").fromParent(new UiSelector().index(1)));
        UiObject videocts =
            mDevice.findObject(new UiSelector().text("Video CTS").fromParent(new UiSelector().index(1)));
        UiObject videodecode =
            mDevice.findObject(new UiSelector().text("Video Decode").fromParent(new UiSelector().index(1)));
        if (!security.exists() && list.waitForExists(60)) {
            list.scrollIntoView(security);
        }
        Log.d(TAG, "Data Security Score " + security.getText());
        if (!dataprocessing.exists() && list.waitForExists(60)) {
            list.scrollIntoView(dataprocessing);
        }
        Log.d(TAG, "Data Processing Score " + dataprocessing.getText());
        if (!imageprocessing.exists() && list.waitForExists(60)) {
            list.scrollIntoView(imageprocessing);
        }
        Log.d(TAG, "Image Processing Score " + imageprocessing.getText());
        if (!uxscore.exists() && list.waitForExists(60)) {
            list.scrollIntoView(uxscore);
        }
        Log.d(TAG, "User Experience Score " + uxscore.getText());
        if (!videocts.exists() && list.waitForExists(60)) {
            list.scrollIntoView(videocts);
        }
        Log.d(TAG, "Video CTS Score " + videocts.getText());
        if (!videodecode.exists() && list.waitForExists(60)) {
            list.scrollIntoView(videodecode);
        }
        Log.d(TAG, "Video Decode Score " + videodecode.getText());
        list.scrollToBeginning(10);
        uxscores.click();

        //Expand, Extract and Close MEM sub scores
        UiObject memscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/result_details_recyclerView"))
            .getChild(new UiSelector().index(4))
            .getChild(new UiSelector().index(4));
        memscores.click();
        UiObject ramaccess =
            mDevice.findObject(new UiSelector().text("RAM Access").fromParent(new UiSelector().index(1)));
        UiObject romapp =
            mDevice.findObject(new UiSelector().text("ROM APP IO").fromParent(new UiSelector().index(1)));
        UiObject romread =
            mDevice.findObject(new UiSelector().text("ROM Sequential Read").fromParent(new UiSelector().index(1)));
        UiObject romwrite =
            mDevice.findObject(new UiSelector().text("ROM Sequential Write").fromParent(new UiSelector().index(1)));
        UiObject romaccess =
            mDevice.findObject(new UiSelector().text("ROM Random Access").fromParent(new UiSelector().index(1)));
       if (!ramaccess.exists() && list.waitForExists(60)) {
            list.scrollIntoView(ramaccess);
        }
        Log.d(TAG, "RAM Access Score " + ramaccess.getText());
       if (!romapp.exists() && list.waitForExists(60)) {
            list.scrollIntoView(romapp);
        }
        Log.d(TAG, "ROM APP IO Score " + romapp.getText());
        if (!romread.exists() && list.waitForExists(60)) {
            list.scrollIntoView(romread);
        }
        Log.d(TAG, "ROM Sequential Read Score " + romread.getText());
        if (!romwrite.exists() && list.waitForExists(60)) {
            list.scrollIntoView(romwrite);
        }
        Log.d(TAG, "ROM Sequential Write Score " + romwrite.getText());
        if (!romaccess.exists() && list.waitForExists(60)) {
            list.scrollIntoView(romaccess);
        }
        Log.d(TAG, "ROM Random Access Score " + romaccess.getText());
        list.scrollToBeginning(10);
        memscores.click();
    }

    public void getScoresv10() throws Exception {
        UiScrollable list = new UiScrollable(new UiSelector().scrollable(true));
        UiObject endlist = mDevice.findObject(new UiSelector().text("Controllable Area Test"));
        UiObject root = mDevice.findObject(new UiSelector().text("This device may be rooted"));
        UiObject storage = mDevice.findObject(new UiSelector().text("Storage performance will degrade when available storage is less than 25%"));
	    UiObject verification = mDevice.findObject(new UiSelector().text("This score has not been verified online"));

        int offset = 0;
        int indexvalue = 0;
        if (verification.exists() || storage.exists()) {
            offset += 1;
        }
        //Set the value for the index value which differs if the root warning is present
        if (root.exists()) {
            offset += 1;
        }
        Log.d(TAG, "offset: " + offset);

        //Expand, Extract and Close GPU sub scores
        indexvalue = 2;
        UiObject gpuscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/RecyclerView"))
            .getChild(new UiSelector().index(indexvalue + offset))
            .getChild(new UiSelector().index(2));
        gpuscores.click();
        sleep(3);
        UiObject gpuseasons =
            mDevice.findObject(new UiSelector().text("Seasons - Vulkan").fromParent(new UiSelector().index(1)));
        UiObject gpucoastline =
            mDevice.findObject(new UiSelector().text("Coastline2 - Vulkan").fromParent(new UiSelector().index(1)));
        Log.d(TAG, "GPU Seasons Score " + gpuseasons.getText());
        Log.d(TAG, "GPU Coastline2 Score " + gpucoastline.getText());
        gpuscores.click();

        //Expand, Extract and Close CPU sub scores
        indexvalue = 1;
        UiObject cpuscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/RecyclerView"))
            .getChild(new UiSelector().index(indexvalue + offset))
            .getChild(new UiSelector().index(2));
        cpuscores.click();
        sleep(3);
	    Log.d(TAG, "indexvalue:" + indexvalue);
	    Log.d(TAG, "cpuscores clicked");
        UiObject cpumaths =
            mDevice.findObject(new UiSelector().text("CPU Mathematical Operations").fromParent(new UiSelector().index(1)));
        UiObject cpucommon =
            mDevice.findObject(new UiSelector().text("CPU Common Algorithms").fromParent(new UiSelector().index(1)));
        UiObject cpumulti =
            mDevice.findObject(new UiSelector().text("CPU Multi-Core").fromParent(new UiSelector().index(1)));
        Log.d(TAG, "CPU Mathematical Operations Score " + cpumaths.getText());
        Log.d(TAG, "CPU Common Algorithms Score " + cpucommon.getText());
        Log.d(TAG, "CPU Multi-Core Score " + cpumulti.getText());
        cpuscores.click();

        //Expand, Extract and Close MEM sub scores
        indexvalue = 3;
        UiObject memscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/RecyclerView"))
            .getChild(new UiSelector().index(indexvalue + offset))
            .getChild(new UiSelector().index(2));
        memscores.click();
        UiObject rambw =
            mDevice.findObject(new UiSelector().text("RAM BandWidth").fromParent(new UiSelector().index(1)));
        UiObject ramlat =
            mDevice.findObject(new UiSelector().text("RAM Latency").fromParent(new UiSelector().index(1)));
        UiObject romapp =
            mDevice.findObject(new UiSelector().text("ROM APP IO").fromParent(new UiSelector().index(1)));
        UiObject romread =
            mDevice.findObject(new UiSelector().text("ROM Sequential Read").fromParent(new UiSelector().index(1)));
        UiObject romwrite =
            mDevice.findObject(new UiSelector().text("ROM Sequential Write").fromParent(new UiSelector().index(1)));
        UiObject romaccess =
            mDevice.findObject(new UiSelector().text("ROM Random Access").fromParent(new UiSelector().index(1)));
       if (!rambw.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding RAM Bandwidth");
            list.scrollIntoView(rambw);
        }
        Log.d(TAG, "RAM Bandwidth Score " + rambw.getText());
       if (!ramlat.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding RAM Latency");
            list.scrollToBeginning(5);
            list.scrollIntoView(ramlat);
            if (endlist.exists()) {
                list.scrollBackward();
            }
        }
        Log.d(TAG, "RAM Latency Score " + ramlat.getText());
        if (!romapp.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding ROM App");
            list.scrollToBeginning(5);
            list.scrollIntoView(romapp);
            if (endlist.exists()) {
                list.scrollBackward();
            }
        }
        Log.d(TAG, "ROM APP IO Score " + romapp.getText());
        if (!romread.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding ROM Read");
            list.scrollToBeginning(5);
            list.scrollIntoView(romread);
            if (endlist.exists()) {
                list.scrollBackward();
            }
        }
        Log.d(TAG, "ROM Sequential Read Score " + romread.getText());
        if (!romwrite.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding ROM Write");
            list.scrollToBeginning(5);
            list.scrollIntoView(romwrite);
            if (endlist.exists()) {
                list.scrollBackward();
            }
        }
        Log.d(TAG, "ROM Sequential Write Score " + romwrite.getText());
        if (!romaccess.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding ROM Access");
            list.scrollToBeginning(5);
            list.scrollIntoView(romaccess);
            if (endlist.exists()) {
                list.scrollBackward(50);
            }
        }
        Log.d(TAG, "ROM Random Access Score " + romaccess.getText());
        list.flingToBeginning(10);
        memscores.click();

        //Expand, Extract and Close UX sub scores
        indexvalue = 4;
        UiObject uxscores =
            mDevice.findObject(new UiSelector().resourceId("com.antutu.ABenchMark:id/RecyclerView"))
            .getChild(new UiSelector().index(indexvalue + offset))
            .getChild(new UiSelector().index(2));
        uxscores.click();
        UiObject security =
            mDevice.findObject(new UiSelector().text("Data Security").fromParent(new UiSelector().index(1)));
        UiObject dataprocessing =
            mDevice.findObject(new UiSelector().text("Data Processing").fromParent(new UiSelector().index(1)));
        UiObject docprocessing =
            mDevice.findObject(new UiSelector().text("Document Processing").fromParent(new UiSelector().index(1)));
        UiObject imagedecoding =
            mDevice.findObject(new UiSelector().text("Image Decoding").fromParent(new UiSelector().index(1)));
        UiObject imageprocessing =
            mDevice.findObject(new UiSelector().text("Image Processing").fromParent(new UiSelector().index(1)));
        UiObject uxscore =
            mDevice.findObject(new UiSelector().text("User Experience").fromParent(new UiSelector().index(1)));
        UiObject videocts =
            mDevice.findObject(new UiSelector().text("Video CTS").fromParent(new UiSelector().index(1)));
        UiObject videodecode =
            mDevice.findObject(new UiSelector().text("Video Decoding").fromParent(new UiSelector().index(1)));
        UiObject videoedit =
            mDevice.findObject(new UiSelector().text("Video Editing").fromParent(new UiSelector().index(1)));
        if (!security.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding Data Security");
            list.scrollIntoView(security);
        }
        Log.d(TAG, "Data Security Score " + security.getText());
        if (!dataprocessing.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding Data Security");
            list.scrollToBeginning(5);
            list.scrollIntoView(dataprocessing);
        }
        Log.d(TAG, "Data Processing Score " + dataprocessing.getText());
        if (!docprocessing.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding Data Processing");
            list.scrollToBeginning(5);
            list.scrollIntoView(docprocessing);
        }
        Log.d(TAG, "Document Processing Score " + docprocessing.getText());
        if (!imagedecoding.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding Image Decoding");
            list.scrollToBeginning(5);
            list.scrollIntoView(imagedecoding);
        }
        Log.d(TAG, "Image Decoding Score " + imagedecoding.getText());

        if (!imageprocessing.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding Image Processing");
            list.scrollToBeginning(5);
            list.scrollIntoView(imageprocessing);
            if (endlist.exists()) {
                list.scrollBackward();
            }
        }
        Log.d(TAG, "Image Processing Score " + imageprocessing.getText());
        if (!uxscore.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding UXScore");
            list.scrollToBeginning(5);
            list.scrollIntoView(uxscore);
            if (endlist.exists()) {
                list.scrollBackward();
            }
        }
        Log.d(TAG, "User Experience Score " + uxscore.getText());
        if (!videocts.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding Video CTS");
            list.scrollToBeginning(5);
            list.scrollIntoView(videocts);
            if (endlist.exists()) {
                list.scrollBackward();
            }
        }
        Log.d(TAG, "Video CTS Score " + videocts.getText());
        if (!videodecode.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding Video Decode");
            list.scrollToBeginning(5);
            list.scrollIntoView(videodecode);
            if (endlist.exists()) {
                list.scrollBackward();
            }
        }
        Log.d(TAG, "Video Decoding Score " + videodecode.getText());
        if (!videoedit.exists() && list.waitForExists(60)) {
            Log.d(TAG, "Finding Video Edit");
            list.scrollToBeginning(5);
            list.scrollIntoView(videoedit);
            if (endlist.exists()) {
                list.scrollBackward();
            }
        }
        Log.d(TAG, "Video Editing Score " + videoedit.getText());
        list.scrollToBeginning(10);
        uxscores.click();
    }
}
