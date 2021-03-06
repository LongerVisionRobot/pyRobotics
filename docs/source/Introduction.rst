==================
  Introduction
==================

-------------------------
Overview of BlackBoard
-------------------------

BlackBoard is our "home-made" message-passing and shared variables hub... somewhat equivalent to `ROS <http://www.ros.org>`_.

.. note::

  Note this is different from the traditionally understood concept of a `blackboard <http://en.wikipedia.org/wiki/Blackboard_system>`_.

It is a message forwarding module that enables communication between different programs through the Resquest-Response schema
as Remote Procedure Calls.
It is also a repository of shared variables that can be read and written by any module (program) connected to it.

We use this for our service robots at the Bio-Robotics laboratory, at UNAM, Mexico.

The way it works is:

  With the robotics API, a module is created that would function as a server in a client-server architecture.

  A configuration file is read by BlackBoard to know to which modules it should connect,
  and how to connect to them (e. g. ip address and port), as well as a list of commands those modules can handle.

This way, we can have separate programs for our vision system, navigation system, action planner, etc.

It is written in C#, although with the use of `mono <http://www.mono-project.com/>`_ it runs in linux too! (tested on ubuntu)
Even better, you could have computers with different operating systems and have your modules distributed,
making the best out of both worlds!

We currently have APIs to easily build modules with C#, C++ and python. This documents refer to the python API.

-------------------------
Overview of pyRobotics
-------------------------
pyRobotics is **NOT** based on the C# or C++ APIs, so its use is different.

A module made with pyRobotics to connect with BlackBoard should have 2 basic parts:

  #. An initialization routine, where it:

      - Sets the configuration needed to connect to BlackBoard and respond to the appropriate commands.
      - Gets everything else ready to start processing commands.
      - Start communications with BlackBoard.
      - Optionally create and subscribe to any shared variables it will use.
      - Let BlackBoard know this module is ready to start receiving commands.

  #. A main loop that can do whatever it needs to do. If the module is only supposed to respond when commands are received,
     use the function BB.Wait() to keep an idle loop to prevent the main program
     (and thus the ConnectionManager and CommandParser threads) to terminate.

The initialization routine must include calls to the functions: BB.Initialize, BB.Start and BB.SetReady.
BB.Initialize takes basically a port number and a function map that defines which function will handle which command,
BB.Start has no parameters and BB.SetReady can receive a ``boolean`` value, default is ``True``, indicating that the module
is ready to start receiving commands.
