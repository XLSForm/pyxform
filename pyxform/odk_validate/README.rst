pyxform_validate
================
A Python Wrapper for ODK Validate 1.6.0

ODK_Validate.jar see sha256 signature `here <https://opendatakit.org/wp-content/uploads/sha256_signatures.txt>`_.

How to use:
-----------

  import odk_validate

  xform_warnings = odk_validate.check_xform("/path/to/xform.xml")

  if len(xform_warnings) == 0:
      print "Your XForm is valid with no warnings!"
  else:
      print "Your XForm is valid but has warnings"
      print xform_warnings
