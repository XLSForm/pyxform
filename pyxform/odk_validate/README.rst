pyxform_validate
================
A Python Wrapper for ODK Validate 1.5.0

How to use:
-----------

  import odk_validate
  
  xform_warnings = odk_validate.check_xform("/path/to/xform.xml")
  
  if len(xform_warnings) == 0:
      print "Your XForm is valid with no warnings!"
  else:
      print "Your XForm is valid but has warnings"
      print xform_warnings