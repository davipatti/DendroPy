#! /usr/bin/env python

###############################################################################
##  DendroPy Phylogenetic Computing Library.
##
##  Copyright 2009 Jeet Sukumaran and Mark T. Holder.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this program. If not, see <http://www.gnu.org/licenses/>.
##
###############################################################################

"""
Support for CLI operations.
"""
import os
import sys

import dendropy

def confirm_overwrite(filepath,
                      replace_without_asking=False,
                      file_desc="Output",
                      out=sys.stdout):
    if os.path.exists(filepath):
        if replace_without_asking:
            overwrite = 'y'
        else:
            out.write('%s file already exists: "%s"\n' % (file_desc, filepath))
            overwrite = raw_input("Overwrite (y/N)? ")
        if not overwrite.lower().startswith("y"):
            return False
        else:
            return True
    else:
        return True

def show_splash(prog_name,
        prog_subtitle,
        prog_version,
        prog_author,
        prog_copyright,
        dest=sys.stderr,
        extended=False,
        width=70):

    lines = []
    lines.append("%s - %s" % (prog_name, prog_subtitle))
    lines.append("%s" % prog_version)
    lines.append("By %s" % prog_author)
    lines.append("(using the DendroPy Phylogenetic Computing Library Version %s)" % (dendropy.__version__))
    if extended:
        lines.append('')
        lines.extend(prog_copyright.split('\n'))
    if width is None or width <= 0:
        width = max([len(i) for i in lines]) + 1
    sbars = '=' * width
    dest.write("%s\n" % sbars)
    dest.write("%s\n" % ('\n'.join(lines)))
    dest.write("%s\n\n" % sbars)


