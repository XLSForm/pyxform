pyxform
=======
The primary goal of this Python library is to make authoring XForms
for ODK Collect easy.

pyxform is a major rewrite of
.. _xls2xform: http://github.com/mvpdev/xls2xform . A new user of
pyxform should look at the tutorial spreadsheet in the example_xls
directory.

For Developers
==============

Installation
------------
This project requires lxml.

> lxml is a Pythonic binding for the libxml2 and libxslt libraries. It
> is unique in that it combines the speed and feature completeness of
> these libraries with the simplicity of a native Python API, mostly
> compatible but superior to the well-known ElementTree API.

Having used xml.dom.minidom to construct XML documents in the past,
using lxml is a breath of fresh air. Unfortunately, the installation
of lxml takes a couple steps.

Here are the .. _installation instructions:
http://codespeak.net/lxml/installation.html#installation . On Ubuntu,
I had to install the following packages:
::
    sudo apt-get install libxml2 libxslt1.1 libxslt1-dev

Independent of Django
---------------------
We are using the Django testing framework with this library. Hence the
models.py file. Django is not a requirement to use this library, but
if you want to test it, we're using Django 1.2.

Implementation
--------------
To break our goal into small and easy problems we've created an object
oriented Python library with the following class structure:

* SurveyElement
  + Option
  + Question
    - InputQuestion
    - UploadQuestion
    - MultipleChoiceQuestion
  + Section
    - RepeatingSection
    - GroupedSection
    - Survey

To recreate the functionality of xls2xform we have broken that program
into two steps, xls2json and json2xform. Have a look around the code,
and feel free to ask questions.
