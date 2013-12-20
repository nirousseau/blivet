# fslabel.py
# Filesystem labeling classes for anaconda's storage configuration module.
#
# Copyright (C) 2009  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Anne Mulhern <amulhern@redhat.com>

import abc
import re

class FSLabelApp(object):
    """An abstract class that represents actions associated with a
       filesystem's labeling application.
    """

    __metaclass__ = abc.ABCMeta

    @property
    def name(self):
        """The name of the filesystem labeling application.

           :rtype: str
        """
        return self._name

    @abc.abstractproperty
    def reads(self):
        """Returns True if this app can also read a label.

           :rtype: bool
        """
        raise NotImplementedError

    @abc.abstractproperty
    def unsetsLabel(self):
        """Returns True if this app can write an empty label.

           :rtype: bool
        """
        raise NotImplementedError

    @abc.abstractmethod
    def labelFormatOK(self, label):
        """Returns True if this label is correctly formatted for this
           filesystem labeling application, otherwise False.

           :param str label: the label for this filesystem
           :rtype: bool
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _writeLabelArgs(self, fs):
        """Returns a list of the arguments for writing a label.

           :param FS fs: a filesystem object

           :return: the arguments
           :rtype: list of str
        """
        raise NotImplementedError

    def setLabelCommand(self, fs):
        """Get the command to label the filesystem.

           :param FS fs: a filesystem object
           :return: the command
           :rtype: list of str
        """
        return [self.name] + self._writeLabelArgs(fs)

    @abc.abstractmethod
    def _readLabelArgs(self, fs):
        """Returns a list of arguments for reading a label.

           :param FS fs: a filesystem object
           :return: the arguments
           :rtype: list of str
        """
        raise NotImplementedError

    def readLabelCommand(self, fs):
        """Get the command to read the filesystem label.

           :param FS fs: a filesystem object
           :return: the command
           :rtype: list of str

           Raises an FSError if this application can not read the label.
        """
        if not self.reads:
            raise FSError("Application %s can not read the filesystem label." % self.name)
        return [self.name] + self._readLabelArgs(fs)

    def extractLabel(self, labelstr):
        """Extract the label from an output string.

           :param str labelstr: the string containing the label information

           :return: the label
           :rtype: str

           Raises an FSError if the label can not be extracted.
        """
        if not self.reads:
            raise FSError("Unknown format for application %s" % self.name)
        match = re.match(self._labelstrRegex(), labelstr)
        if match is None:
            raise FSError("Unknown format for application %s" % self.name)
        return match.group('label')

class E2Label(FSLabelApp):
    """Application used by ext2 and its descendants."""

    _name = "e2label"

    @property
    def reads(self):
        return True

    @property
    def unsetsLabel(self):
        return True

    def _writeLabelArgs(self, fs):
        if fs.label:
            return [fs.device, fs.label]
        else:
            return [fs.device, ""]

    def labelFormatOK(self, label):
        return len(label) < 17

    def _readLabelArgs(self, fs):
        return [fs.device]

    def _labelstrRegex(self):
        return r'(?P<label>.*)'

class DosFsLabel(FSLabelApp):
    """Application used by FATFS."""

    _name = "dosfslabel"

    @property
    def reads(self):
        return True

    @property
    def unsetsLabel(self):
        return True

    def _writeLabelArgs(self, fs):
        if fs.label:
            return [fs.device, fs.label]
        else:
            return [fs.device, ""]

    def labelFormatOK(self, label):
        return len(label) < 12

    def _readLabelArgs(sefl, fs):
        return [fs.device]

    def _labelstrRegex(self):
        return r'(?P<label>.*)'

class JFSTune(FSLabelApp):
    """Application used by JFS."""

    _name = "jfs_tune"

    @property
    def reads(self):
        return False

    @property
    def unsetsLabel(self):
        return True

    def _writeLabelArgs(self, fs):
        if fs.label:
            return ["-L", fs.label, fs.device]
        else:
            return ["-L", "", fs.device]

    def labelFormatOK(self, label):
        return len(label) < 17

    def _readLabelArgs(sefl, fs):
        raise NotImplementedError

    def _labelstrRegex(self):
        raise NotImplementedError

class ReiserFSTune(FSLabelApp):
    """Application used by ReiserFS."""

    _name = "reiserfstune"

    @property
    def reads(self):
        return False

    @property
    def unsetsLabel(self):
        return True

    def _writeLabelArgs(self, fs):
        if fs.label:
            return ["-l", fs.label, fs.device]
        else:
            return ["-l", "", fs.device]

    def labelFormatOK(self, label):
        return len(label) < 17

    def _readLabelArgs(self, fs):
        raise NotImplementedError

    def _labelstrRegex(self):
        raise NotImplementedError

class XFSAdmin(FSLabelApp):
    """Application used by XFS."""

    _name = "xfs_admin"

    @property
    def reads(self):
        return True

    @property
    def unsetsLabel(self):
        return False

    def _writeLabelArgs(self, fs):
        if fs.label:
            return ["-L", fs.label, fs.device]
        else:
            raise ValueError("%s cannot set an empty label." % self.name)

    def labelFormatOK(self, label):
        return ' ' not in label and len(label) < 13

    def _readLabelArgs(sefl, fs):
        return ["-l", fs.device]

    def _labelstrRegex(self):
        return r'label = "(?P<label>.*)"'