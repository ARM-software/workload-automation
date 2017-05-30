package ${package_name};

import android.app.Activity;
import android.os.Bundle;
import org.junit.Test;
import org.junit.runner.RunWith;
import android.support.test.runner.AndroidJUnit4;

import android.util.Log;
import android.view.KeyEvent;

// Import the uiautomator libraries
import android.support.test.uiautomator.UiObject;
import android.support.test.uiautomator.UiObjectNotFoundException;
import android.support.test.uiautomator.UiScrollable;
import android.support.test.uiautomator.UiSelector;


import com.arm.wlauto.uiauto.BaseUiAutomation;

@RunWith(AndroidJUnit4.class)
public class UiAutomation extends BaseUiAutomation {

    public static String TAG = "${name}";

@Test
public void runUiAutomation() throws Exception {
    initialize_instrumentation();
	// UI Automation code goes here
    }

}
