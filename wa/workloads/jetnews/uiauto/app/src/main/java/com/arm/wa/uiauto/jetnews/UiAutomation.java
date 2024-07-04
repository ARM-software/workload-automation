/*    Copyright 2014-2024 ARM Limited
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

import androidx.test.uiautomator.UiObject;
import androidx.test.uiautomator.UiSelector;

import android.os.Bundle;

import com.arm.wa.uiauto.ApplaunchInterface;
import com.arm.wa.uiauto.BaseUiAutomation;
import com.arm.wa.uiauto.UiAutoUtils;

import org.junit.Test;

// Dummy workload for jetnews. We need to use JankTestBasem but we
// can't inherit from that class as we already inherit BaseUiAutomation.
// Therefore we have another class (UiAutomationJankTests) that uses
// this class instead.

public class UiAutomation extends BaseUiAutomation implements ApplaunchInterface {

    protected Bundle parameters;
    protected String packageID;

    public void initialize() {
        parameters = getParams();
        packageID = getPackageID(parameters);
    }

    @Test
    public void setup() throws Exception {
        setScreenOrientation(ScreenOrientation.NATURAL);
    }

    @Test
    public void runWorkload() {
        // Intentionally empty, not used.
    }

    @Test
    public void teardown() throws Exception {
        unsetScreenOrientation();
    }

    public void runApplicationSetup() throws Exception {
        // Intentionally empty, not used.
    }

    // Sets the UiObject that marks the end of the application launch.
    public UiObject getLaunchEndObject() {
        // Intentionally empty, not used.
        return null;
    }

    // Returns the launch command for the application.
    public String getLaunchCommand() {
        // Intentionally empty, not used.
        return "";
    }

    // Pass the workload parameters, used for applaunch
    public void setWorkloadParameters(Bundle workload_parameters) {
        // Intentionally empty, not used.
    }
}


