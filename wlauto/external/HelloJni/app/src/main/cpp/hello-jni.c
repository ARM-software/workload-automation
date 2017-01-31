/*
 * Copyright (C) 2016 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */
#include <string.h>
#include <stdlib.h>

#include <jni.h>

#include <android/log.h>

/**
 * The native srand API takes an unsigned int.  The JNI interface takes
 * a long so, that it can hold the whole range of values (i.e. >= 2G).
 */
void Java_com_example_hellojni_HelloJni_nativeSrand(JNIEnv* env, jobject thiz, jlong seed) {
    unsigned int seed2 = (unsigned int) seed;

    __android_log_print(ANDROID_LOG_INFO, "hellojni", ">nativeSrand(0x%x)", seed2);
    srand(seed2);
    __android_log_print(ANDROID_LOG_INFO, "hellojni", "<nativeSrand");
}

jint Java_com_example_hellojni_HelloJni_nativeRand(JNIEnv* env, jobject thiz) {
    __android_log_print(ANDROID_LOG_INFO, "hellojni", ">nativeRand");
    jint val = rand();
    __android_log_print(ANDROID_LOG_INFO, "hellojni", "<nativeRand, %d", val);
    return val;
}

