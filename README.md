# PEPYSCOPE
##A simple and fast panadapter for your HF radio using an RTL-SDR USB dongle.

This panadapter has been developed to achieve several goals:
1. fast performance on light hardware;
2. ability to exploit the direct sampling (0-14MHz) of the RTL-SDR V3 dongle;
3. be easy to understand (Python, Numpy, PyQTGraph, etc) and to maintain (~250 lines of code);
4. to be open source (GPLv3);
5. to start directly at the frequency of interest (IF output of a classic HF radio);
6. produce high resolution waterfalls;
7. to be used directly with no UPCONVERTER.


![pypanadapter on 20m at night](https://github.com/mcogoni/pypanadapter/blob/master/pypanadapter.png)

To run it, you need a Linux PC and a few libraries such as numpy, scipy, pyqtgraph, pyqt, etc (I'll try to document the requirements better in the future).

All experiments so far have been conducted with a KENWOOD TS-180S (single conversion with IF at 8.83 MHz) and a RTL-SDR v3. So the hardware requirements are minimal.

In the future I'll try to add a spectrum graph to the waterfall.

73,
marco / IS0KYB
