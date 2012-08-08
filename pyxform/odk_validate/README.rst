pyxform_validate
================
A Python Wrapper for ODK Validate 1.2.2

How to use:
-----------

  import pyxform_validate

  xform_status = pyxform_validate.check_xform("/path/to/xform.xml")

  if xform_status.valid:
	  print "Your XForm is valid!"
  else:
      print "Your XForm is not valid"
      print status