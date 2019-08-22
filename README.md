# PEPYSCOPE
##A simple and fast panadapter for your HF radio using an RTL-SDR USB dongle.

This panadapter has been developed to achieve several goals:
1. fast performance on light hardware;
2. ability to exploit the direct sampling (0-14MHz) of the RTL-SDR V3 dongle;
3. be easy to understand (Python, Numpy, PyQTGraph, etc) and to maintain (~250 lines of code);
4. to be open source (GPLv3);
5. no setup time: start directly at the frequency of interest (IF output of a classic HF radio);
6. produce high resolution waterfalls very efficiently by means of Zoom FFT transform;
7. to be used directly with no UPCONVERTER;
8. synchronized waterfall and spectrum plots;
9. ...

![pypanadapter on 20m at night](https://github.com/mcogoni/pypanadapter/blob/master/pypanadapter.png)

Watch it in action: https://www.youtube.com/watch?v=Z9mr08ou5NI

To run it, you need a Linux PC and a few libraries such as numpy, scipy, pyqtgraph, pyqt, etc (I'll try to document the requirements better in the future).

All experiments so far have been conducted with a KENWOOD TS-180S (single conversion with IF at 8.83 MHz) and a RTL-SDR v3. So the hardware requirements are minimal.

73,
marco / IS0KYB
