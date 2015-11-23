============
Installation
============

.. module:: wlauto

This page describes how to install Workload Automation 2.


Prerequisites
=============

Operating System
----------------

WA runs on a native Linux install. It was tested with Ubuntu 12.04,
but any recent Linux distribution should work. It should run on either
32bit or 64bit OS, provided the correct version of Android (see below)
was installed. Officially, **other environments are not supported**. WA
has been known to run on Linux Virtual machines and in Cygwin environments,
though additional configuration maybe required in both cases (known issues
include makings sure USB/serial connections are passed to the VM, and wrong
python/pip binaries being picked up in Cygwin). WA *should* work on other
Unix-based systems such as BSD or Mac OS X, but it has not been tested
in those environments. WA *does not* run on Windows (though it should be
possible to get limited functionality with minimal porting effort).


Android SDK
-----------

You need to have the Android SDK with at least one platform installed.
To install it, download the ADT Bundle from here_.  Extract it
and add ``<path_to_android_sdk>/sdk/platform-tools`` and ``<path_to_android_sdk>/sdk/tools``
to your ``PATH``.  To test that you've installed it properly run ``adb
version``, the output should be similar to this::

        $ adb version
        Android Debug Bridge version 1.0.31
        $

.. _here: https://developer.android.com/sdk/index.html

Once that is working, run ::

        android update sdk

This will open up a dialog box listing available android platforms and
corresponding API levels, e.g. ``Android 4.3 (API 18)``. For WA, you will need
at least API level 18 (i.e. Android 4.3), though installing the latest is
usually the best bet.

Once the SDK is installed, you should set ``ANDROID_HOME`` to point to
the install location of the SDK (i.e. ``<path_to_android_sdk>/sdk``).


Python
------

Workload Automation 2 requires Python 2.7 (Python 3 is not supported, at the moment).


pip
---

pip is the recommended package manager for Python. It is not part of standard
Python distribution and would need to be installed separately. On Ubuntu and
similar distributions, this may be done with APT::

        sudo apt-get install python-pip

Versions in OS packages tend to be pretty old, so you should immediately update
pip from PyPI::

        sudo -H pip install --upgrade pip


Python Packages
---------------

.. note:: pip should automatically download and install missing dependencies,
          so if you're using pip, you can skip this section.

Workload Automation 2 depends on the following additional libraries:

  * pexpect
  * docutils
  * pySerial
  * pyYAML
  * python-dateutil

You can install these with pip::

        sudo -H pip install pexpect
        sudo -H pip install pyserial
        sudo -H pip install pyyaml
        sudo -H pip install docutils
        sudo -H pip install python-dateutil

Some of these may also be available in your distro's repositories, e.g. ::

        sudo apt-get install python-serial

Distro package versions tend to be older, so pip installation is recommended.
However, pip will always download and try to build the source, so in some
situations distro binaries may provide an easier fall back. Please also note that
distro package names may differ from pip packages.


Optional Python Packages
------------------------

.. note:: unlike the mandatory dependencies in the previous section,
          pip will *not* install these automatically, so you will have
          to explicitly install them if/when you need them.

In addition to the mandatory packages listed in the previous sections, some WA
functionality (e.g. certain extensions) may have additional dependencies. Since
they are not necessary to be able to use most of WA, they are not made mandatory
to simplify initial WA installation. If you try to use an extension that has
additional, unmet dependencies, WA will tell you before starting the run, and
you can install it then. They are listed here for those that would rather
install them upfront (e.g. if you're planning to use WA to an environment that
may not always have Internet access).

  * nose
  * pandas
  * PyDAQmx
  * pymongo
  * jinja2


.. note:: Some packages have C extensions and will require Python development
          headers to install. You can get those by installing ``python-dev``
          package in apt on Ubuntu (or the equivalent for your distribution).


Installing
==========

Installing the latest released version from PyPI (Python Package Index)::

       sudo -H pip install wlauto

This will install WA along with its mandatory dependencies. If you would like to 
install all optional dependencies at the same time, do the following instead::

       sudo -H pip install wlauto[all]
       
Alternatively, you can also install the latest development version from GitHub
(you will need git installed for this to work)::

        git clone git@github.com:ARM-software/workload-automation.git workload-automation
        sudo -H pip install ./workload-automation


(Optional) Verify installation
-------------------------------

Once the tarball has been installed, try executing ::

        wa -h

You should see a help message outlining available subcommands.


(Optional) APK files
--------------------

A large number of WA workloads are installed as APK files. These cannot be
distributed with WA and so you will need to obtain those separately. 

