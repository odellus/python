# This script generates a Python interface for an Apple Macintosh Manager.
# It uses the "bgen" package to generate C code.
# The function specifications are generated by scanning the mamager's header file,
# using the "scantools" package (customized for this particular manager).

import string

# Declarations that change for each manager
MACHEADERFILE = 'TextEdit.h'		# The Apple header file
MODNAME = '_TE'				# The name of the module
OBJECTNAME = 'TE'			# The basic name of the objects used here
KIND = 'Handle'				# Usually 'Ptr' or 'Handle'

# The following is *usually* unchanged but may still require tuning
MODPREFIX = 'TE'			# The prefix for module-wide routines
OBJECTTYPE = "TEHandle"		# The C type used to represent them
OBJECTPREFIX = MODPREFIX + 'Obj'	# The prefix for object methods
INPUTFILE = string.lower(MODPREFIX) + 'gen.py' # The file generated by the scanner
OUTPUTFILE = MODNAME + "module.c"	# The file generated by this program

from macsupport import *

# Create the type objects
TEHandle = OpaqueByValueType("TEHandle", "TEObj")
CharsHandle = OpaqueByValueType("CharsHandle", "ResObj")
Handle = OpaqueByValueType("Handle", "ResObj")
StScrpHandle = OpaqueByValueType("StScrpHandle", "ResObj")
TEStyleHandle = OpaqueByValueType("TEStyleHandle", "ResObj")
RgnHandle = OpaqueByValueType("RgnHandle", "ResObj")

TextStyle = OpaqueType("TextStyle", "TextStyle")
TextStyle_ptr = TextStyle

includestuff = includestuff + """
#include <Carbon/Carbon.h>

#ifdef USE_TOOLBOX_OBJECT_GLUE
extern PyObject *_TEObj_New(TEHandle);
extern int _TEObj_Convert(PyObject *, TEHandle *);

#define TEObj_New _TEObj_New
#define TEObj_Convert _TEObj_Convert
#endif

#define as_TE(h) ((TEHandle)h)
#define as_Resource(teh) ((Handle)teh)

/*
** Parse/generate TextStyle records
*/
static PyObject *
TextStyle_New(TextStylePtr itself)
{

	return Py_BuildValue("lllO&", (long)itself->tsFont, (long)itself->tsFace, (long)itself->tsSize, QdRGB_New,
				&itself->tsColor);
}

static int
TextStyle_Convert(PyObject *v, TextStylePtr p_itself)
{
	long font, face, size;
	
	if( !PyArg_ParseTuple(v, "lllO&", &font, &face, &size, QdRGB_Convert, &p_itself->tsColor) )
		return 0;
	p_itself->tsFont = (short)font;
	p_itself->tsFace = (Style)face;
	p_itself->tsSize = (short)size;
	return 1;
}
"""

initstuff = initstuff + """
	PyMac_INIT_TOOLBOX_OBJECT_NEW(TEHandle, TEObj_New);
	PyMac_INIT_TOOLBOX_OBJECT_CONVERT(TEHandle, TEObj_Convert);
"""

class TEMethodGenerator(OSErrWeakLinkMethodGenerator):
	"""Similar to MethodGenerator, but has self as last argument"""

	def parseArgumentList(self, args):
		args, a0 = args[:-1], args[-1]
		t0, n0, m0 = a0
		if m0 != InMode:
			raise ValueError, "method's 'self' must be 'InMode'"
		self.itself = Variable(t0, "_self->ob_itself", SelfMode)
		FunctionGenerator.parseArgumentList(self, args)
		self.argumentList.append(self.itself)



class MyObjectDefinition(PEP253Mixin, GlobalObjectDefinition):
	# XXXX Could be subtype of Resource
	# Attributes that can be set.
	getsetlist = [
		(
		'destRect',
		'return Py_BuildValue("O&", PyMac_BuildRect, &(*self->ob_itself)->destRect);',
		None,
		'Destination rectangle'
		), (
		'viewRect',
		'return Py_BuildValue("O&", PyMac_BuildRect, &(*self->ob_itself)->viewRect);',
		None,
		'Viewing rectangle'
		), (
		'selRect',
		'return Py_BuildValue("O&", PyMac_BuildRect, &(*self->ob_itself)->selRect);',
		None,
		'Selection rectangle'
		), (
		'lineHeight',
		'return Py_BuildValue("h", (*self->ob_itself)->lineHeight);',
		None,
		'Height of a line'
		), (
		'fontAscent',
		'return Py_BuildValue("h", (*self->ob_itself)->fontAscent);',
		None,
		'Ascent of a line'
		), (
		"selPoint",
		'return Py_BuildValue("O&", PyMac_BuildPoint, (*self->ob_itself)->selPoint);',
		None,
		'Selection Point'
		), (
		'selStart',
		'return Py_BuildValue("h", (*self->ob_itself)->selStart);',
		None,
		'Start of selection'
		), (
		'selEnd',
		'return Py_BuildValue("h", (*self->ob_itself)->selEnd);',
		None,
		'End of selection'
		), (
		'active',
		'return Py_BuildValue("h", (*self->ob_itself)->active);',
		None,
		'TBD'
		), (
		'just',
		'return Py_BuildValue("h", (*self->ob_itself)->just);',
		None,
		'Justification'
		), (
		'teLength',
		'return Py_BuildValue("h", (*self->ob_itself)->teLength);',
		None,
		'TBD'
		), (
		'txFont',
		'return Py_BuildValue("h", (*self->ob_itself)->txFont);',
		None,
		'Current font'
		), (
		'txFace',
		'return Py_BuildValue("h", (*self->ob_itself)->txFace);',
		None,
		'Current font variant'
		), (
		'txMode',
		'return Py_BuildValue("h", (*self->ob_itself)->txMode);',
		None,
		'Current text-drawing mode'
		), (
		'txSize',
		'return Py_BuildValue("h", (*self->ob_itself)->txSize);',
		None,
		'Current font size'
		), (
		'nLines',
		'return Py_BuildValue("h", (*self->ob_itself)->nLines);',
		None,
		'TBD'
		)]		
		
	def outputCheckNewArg(self):
		Output("""if (itself == NULL) {
					PyErr_SetString(TE_Error,"Cannot create null TE");
					return NULL;
				}""")
	def outputFreeIt(self, itselfname):
		Output("TEDispose(%s);", itselfname)
		

# From here on it's basically all boiler plate...

# Create the generator groups and link them
module = MacModule(MODNAME, MODPREFIX, includestuff, finalstuff, initstuff)
object = MyObjectDefinition(OBJECTNAME, OBJECTPREFIX, OBJECTTYPE)
module.addobject(object)

# Create the generator classes used to populate the lists
Function = OSErrWeakLinkFunctionGenerator
Method = TEMethodGenerator

# Create and populate the lists
functions = []
methods = []
execfile(INPUTFILE)

# Converter from/to handle
f = Function(TEHandle, 'as_TE', (Handle, 'h', InMode))
functions.append(f)
f = Method(Handle, 'as_Resource', (TEHandle, 'teh', InMode))
methods.append(f)

# add the populated lists to the generator groups
# (in a different wordl the scan program would generate this)
for f in functions: module.add(f)
for f in methods: object.add(f)

# generate output (open the output file as late as possible)
SetOutputFileName(OUTPUTFILE)
module.generate()

