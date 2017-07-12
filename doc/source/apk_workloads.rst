.. _apk_workload_settings:

APK Workloads
=============

APK resolution
--------------

WA has various resource getters that can be configured to locate APK files but for most people APK files
should be kept in the ``$WA_USER_DIRECTORY/dependencies/SOME_WORKLOAD/`` directory. (by default 
``~/.workload_automation/dependencies/SOME_WORKLOAD/``). The ``WA_USER_DIRECTORY`` enviroment variable can be used
to chnage the location of this folder. The APK files need to be put into the corresponding directories
for the workload they belong to. The name of the file can be anything but as explained below may need
to contain certain peices of information.

All ApkWorkloads have parameters that affect the way in which APK files are resolved, ``exact_abi``,
``force_install`` and ``check_apk``. Their exact behaviours are outlined below.

.. confval:: exact_abi

   If this setting is enabled WA's resource resolvers will look for the devices ABI with any native 
   code present in the apk. By default this setting is disabled since most apks will work across all
   devices. You may wish to enable this feature when working with devices that support multiple ABI's (like 
   64-bit devices that can run 32-bit APK files) and are specifically trying to test one or the other.

.. confval:: force_install

   If this setting is enabled WA will *always* use the APK file on the host, and re-install it on every
   iteration. If there is no APK on the host that is a suitable version and/or ABI for the workload WA
   will error when ``force_install`` is enabled.

.. confval:: check_apk

   This parameter is used to specify a preference over host or target versions of the app. When set to
   ``True`` WA will prefer the host side version of the APK. It will check if the host has the APK and
   if the host APK meets the version requirements of the workload. If does and the target already has
   same version nothing will be done, other wise it will overwrite the targets app with the host version.
   If the hosts is missing the APK or it does not meet version requirements WA will fall back to the app
   on the target if it has the app and it is of a suitable version. When this parameter is set to 
   ``false`` WA will prefer to use the version already on the target if it meets the workloads version
   requirements. If it does not it will fall back to search the host for the correct version. In both modes
   if neither the host nor target have a suitable version, WA will error and not run the workload.

Some workloads will also feature the follow parameters which will alter the way their APK files are resolved.

.. confval:: version

   This parameter is used to specify which version of uiautomation for the workload is used. In some workloads
   e.g. ``geekbench`` multiple versions with drastically different UI's are supported. When a workload uses a
   version it is required for the APK file to contain the uiautomation version in the file name. In the case
   of antutu the file names could be: ``geekbench_2.apk`` or ``geekbench_3.apk``.

.. confval:: variant_name

   Some workloads use variants of APK files, this is usually the case with web browser APK files, these work
   in exactly the same way as the version,  the variant of the apk 

