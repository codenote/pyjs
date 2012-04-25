"""
* Copyright 2007 Google Inc.
*
* Licensed under the Apache License, Version 2.0 (the "License"); you may not
* use this file except in compliance with the License. You may obtain a copy of
* the License at
*
* http:#www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
* WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
* License for the specific language governing permissions and limitations under
* the License.
"""
#package com.google.gwt.sample.kitchensink.client


from __pyjamas__ import doc

from pyjamas import DOM
from pyjamas import Window
from pyjamas.ui.Image import Image
from pyjamas.ui.ChangeListener import ChangeHandler
from pyjamas.ui.ClickListener import ClickHandler
from pyjamas.ui.Composite import Composite
from pyjamas.ui.HorizontalPanel import HorizontalPanel
from pyjamas.ui.KeyboardListener import KeyboardHandler
from pyjamas.ui.ListBox import ListBox
from pyjamas.ui.PushButton import PushButton
from pyjamas.ui import RichTextAreaConsts
from pyjamas.ui.ToggleButton import ToggleButton
from pyjamas.ui.VerticalPanel import VerticalPanel
from pyjamas.ui.Widget import Widget

from pyjamas.Timer import Timer

from pyjamas.selection.RangeEndPoint import RangeEndPoint
from pyjamas.selection.Range import Range
from pyjamas.selection.RangeUtil import getAdjacentTextElement
from pyjamas.selection import Selection

import EventLinkPopup

import string
import traceback


def print_tree(parent):
    child = parent.firstChild
    while child:
        child = child.nextSibling

def remove_node(doc, element):
    """ removes a specific node, adding its children in its place
    """
    fragment = doc.createDocumentFragment()
    while element.firstChild:
        fragment.appendChild(element.firstChild)

    parent = element.parentNode
    parent.insertBefore(fragment, element)
    parent.removeChild(element)

def remove_editor_styles(doc, csm, tree):
    """ removes all other <span> nodes with an editor style
    """

    element = tree.lastChild
    while element:
        if not csm.identify(element):
            element = element.previousSibling
            continue
        prev_el = element
        remove_editor_styles(doc, csm, prev_el)
        element = element.previousSibling
        remove_node(doc, prev_el)

class Images(object):
    bold = "bold.gif"
    italic = "italic.gif"
    underline = "underline.gif"
    subscript = "subscript.gif"
    superscript = "superscript.gif"
    justifyLeft = "justifyLeft.gif"
    justifyCenter = "justifyCenter.gif"
    justifyRight = "justifyRight.gif"
    strikeThrough = "strikeThrough.gif"
    indent = "indent.gif"
    outdent = "outdent.gif"
    hr = "hr.gif"
    ol = "ol.gif"
    ul = "ul.gif"
    insertImage = "insertImage.gif"
    createLink = "createLink.gif"
    removeLink = "removeLink.gif"
    removeFormat = "removeFormat.gif"

class FontFamilyManager:

    def __init__(self, doc, fontname):
        self.fontname = fontname
        self.doc = doc

    def create(self):
        element = self.doc.createElement("span")
        DOM.setStyleAttribute(element, "font-family", self.fontname)
        return element

    def identify(self, element):
        if element.nodeType != 1:
            return False
        if str(string.lower(element.tagName)) != 'span':
            return False
        style = DOM.getStyleAttribute(element, "font-family")
        return style is not None

class CustomStyleManager:

    def __init__(self, doc, stylename):
        self.stylename = stylename
        self.doc = doc

    def create(self):
        element = self.doc.createElement("span")
        DOM.setAttribute(element, "className", self.stylename)
        return element

    def identify(self, element):
        if element.nodeType != 1:
            return False
        if str(string.lower(element.tagName)) != 'span':
            return False
        style = DOM.getAttribute(element, "className")
        return style and style.startswith("editor-")

class HeadingStyleManager:

    def __init__(self, doc, heading):
        self.heading = heading
        self.doc = doc

    def create(self):
        element = self.doc.createElement(self.heading)
        return element

    def identify(self, element):
        if element.nodeType != 1:
            return False
        tag = str(string.lower(element.tagName))
        return len(tag) == 2 and tag[0] == "h"


"""*
* A sample toolbar for use with {@link RichTextArea}. It provides a simple UI
* for all rich text formatting, dynamically displayed only for the available
* functionality.
"""
class RichTextToolbar(Composite, ClickHandler, ChangeHandler, KeyboardHandler):

    fontSizesConstants = [
        RichTextAreaConsts.XX_SMALL, RichTextAreaConsts.X_SMALL,
        RichTextAreaConsts.SMALL, RichTextAreaConsts.MEDIUM,
        RichTextAreaConsts.LARGE, RichTextAreaConsts.X_LARGE,
        RichTextAreaConsts.XX_LARGE
    ]

    """*
    * Creates a toolbar that drives the given rich text area.
    *
    * @param richText the rich text area to be controlled
    """
    def __init__(self, richText, _parent, **kwargs):

        self.isInText = False
        self.lastText = ""
        self.trigger = False
        self.lastRange = None
        self._parent = _parent

        # Timer for trying real time selection change stuff
        self.timerRange = None
        self.selTimer = Timer(notify=self.run)

        self.outer = VerticalPanel()
        self.topPanel = HorizontalPanel(BorderWidth=1)
        self.bottomPanel = HorizontalPanel()

        self.richText = richText
        self.basic = richText.getBasicFormatter()
        self.extended = richText.getExtendedFormatter()

        self.outer.add(self.topPanel)
        self.outer.add(self.bottomPanel)
        self.topPanel.setWidth("100%")
        self.topPanel.setHeight("20px")
        self.bottomPanel.setWidth("100%")

        kwargs['StyleName'] = kwargs.get('StyleName', "gwt-RichTextToolbar")

        Composite.__init__(self, self.outer, **kwargs)
        ClickHandler.__init__(self)
        ChangeHandler.__init__(self)
        KeyboardHandler.__init__(self)

        if self.basic is not None:
            self.bold = self.createToggleButton(Images.bold,
                                            "bold")
            self.italic = self.createToggleButton(Images.italic,
                                            "italic")
            self.underline = self.createToggleButton(Images.underline,
                                            "underline")
            self.subscript = self.createToggleButton(Images.subscript,
                                            "subscript")
            self.superscript = self.createToggleButton(Images.superscript,
                                            "superscript")
            self.justifyLeft = self.createPushButton(Images.justifyLeft,
                                            "justify left")
            self.justifyCenter = self.createPushButton(Images.justifyCenter,
                                            "justify centre")
            self.justifyRight = self.createPushButton(Images.justifyRight,
                                            "justify right")
            self.topPanel.add(self.bold)
            self.topPanel.add(self.italic)
            self.topPanel.add(self.underline)
            self.topPanel.add(self.subscript)
            self.topPanel.add(self.superscript)
            self.topPanel.add(self.justifyLeft)
            self.topPanel.add(self.justifyCenter)
            self.topPanel.add(self.justifyRight)

        if self.extended is not None:
            self.strikethrough = self.createToggleButton(Images.strikeThrough,
                                            "strikethrough")
            self.indent = self.createPushButton(Images.indent,
                                            "indent")
            self.outdent = self.createPushButton(Images.outdent,
                                            "outdent")
            self.hr = self.createPushButton(Images.hr,
                                            "hr")
            self.ol = self.createPushButton(Images.ol,
                                            "ordered list")
            self.ul = self.createPushButton(Images.ul,
                                            "unordered list")
            self.insertImage = self.createPushButton(Images.insertImage,
                                            "insert image")
            self.createLink = self.createPushButton(Images.createLink,
                                            "create link")
            self.removeLink = self.createPushButton(Images.removeLink,
                                            "remove link")
            self.removeFormat = self.createPushButton(Images.removeFormat,
                                            "remove formatting")

            self.topPanel.add(self.strikethrough)
            self.topPanel.add(self.indent)
            self.topPanel.add(self.outdent)
            self.topPanel.add(self.hr)
            self.topPanel.add(self.ol)
            self.topPanel.add(self.ul)
            self.topPanel.add(self.insertImage)
            self.topPanel.add(self.createLink)
            self.topPanel.add(self.removeLink)
            self.topPanel.add(self.removeFormat)

        if self.basic is not None:
            self.hstyles = self.createHeadingStyleList("Headings")
            self.backColors = self.createColorList("Background")
            self.foreColors = self.createColorList("Foreground")
            self.fonts = self.createFontList()
            self.fontSizes = self.createFontSizes()
            self.bottomPanel.add(self.hstyles)
            self.bottomPanel.add(self.backColors)
            self.bottomPanel.add(self.foreColors)
            self.bottomPanel.add(self.fonts)
            self.bottomPanel.add(self.fontSizes)

            # We only use these listeners for updating status,
            # so don't hook them up
            # unless at least self.basic editing is supported.
            self.richText.addKeyboardListener(self)
            self.richText.addClickListener(self)

    def createHeadingStyleList(self, caption):
        lb = ListBox()
        lb.addChangeListener(self)
        lb.setVisibleItemCount(1)

        lb.addItem(caption)
        lb.addItem("Heading1", "h1")
        lb.addItem("Heading2", "h2")
        lb.addItem("Heading3", "h3")
        lb.addItem("Heading4", "h4")
        lb.addItem("Heading5", "h5")

        return lb

    def createColorList(self, caption):
        lb = ListBox()
        lb.addChangeListener(self)
        lb.setVisibleItemCount(1)

        lb.addItem(caption)
        lb.addItem("White", "white")
        lb.addItem("Black", "black")
        lb.addItem("Red", "red")
        lb.addItem("Green", "green")
        lb.addItem("Yellow", "yellow")
        lb.addItem("Blue", "blue")
        return lb

    def createFontList(self):
        lb = ListBox()
        lb.addChangeListener(self)
        lb.setVisibleItemCount(1)

        lb.addItem("Font", "")
        lb.addItem("Normal", "")
        lb.addItem("Times New Roman", "Times New Roman")
        lb.addItem("Arial", "Arial")
        lb.addItem("Aramanth", "Aramanth")
        lb.addItem("Calibri", "Calibri")
        lb.addItem("Courier New", "Courier New")
        lb.addItem("Georgia", "Georgia")
        lb.addItem("Helvetica", "Helvetica")
        lb.addItem("Symbol", "Symbol")
        lb.addItem("Trebuchet", "Trebuchet")
        lb.addItem("Verdana", "Verdana")
        return lb

    def createFontSizes(self):
        lb = ListBox()
        lb.addChangeListener(self)
        lb.setVisibleItemCount(1)

        lb.addItem("Size")
        lb.addItem("XXsmall")
        lb.addItem("Xsmall")
        lb.addItem("small")
        lb.addItem("medium")
        lb.addItem("large")
        lb.addItem("Xlarge")
        lb.addItem("XXlarge")
        return lb

    def createPushButton(self, img, tip):
        img = Image(img)
        pb = PushButton(img, img, self)
        pb.setTitle(tip)
        return pb

    def createToggleButton(self, img, tip):
        img = Image(img)
        tb = ToggleButton(img, img, self)
        tb.setTitle(tip)
        return tb

    def updateStatus(self):
        """* Updates the status of all the stateful buttons.
        """
        if self.basic is not None:
            self.bold.setDown(self.basic.isBold())
            self.italic.setDown(self.basic.isItalic())
            self.underline.setDown(self.basic.isUnderlined())
            self.subscript.setDown(self.basic.isSubscript())
            self.superscript.setDown(self.basic.isSuperscript())

        if self.extended is not None:
            self.strikethrough.setDown(self.extended.isStrikethrough())

    def onChange(self, sender):
        if sender == self.hstyles:
            bc = self.hstyles.getValue(self.hstyles.getSelectedIndex())
            self._surround(HeadingStyleManager, bc)
            self.backColors.setSelectedIndex(0)
        if sender == self.backColors:
            bc = self.backColors.getValue(self.backColors.getSelectedIndex())
            self.basic.setBackColor(bc)
            self.backColors.setSelectedIndex(0)
        elif sender == self.foreColors:
            fc = self.foreColors.getValue(self.foreColors.getSelectedIndex())
            self.basic.setForeColor(fc)
            self.foreColors.setSelectedIndex(0)
        elif sender == self.fonts:
            fname = self.fonts.getValue(self.fonts.getSelectedIndex())
            self.basic.setFontName(fname)
            self.fonts.setSelectedIndex(0)
        elif sender == self.fontSizes:
            fs = self.fontSizesConstants[self.fontSizes.getSelectedIndex() - 1]
            self.basic.setFontSize(fs)
            self.fontSizes.setSelectedIndex(0)

    def onClick(self, sender):

        if sender == self.bold:
            self.basic.toggleBold()
        elif sender == self.italic:
            self.basic.toggleItalic()
        elif sender == self.underline:
            self.basic.toggleUnderline()
        elif sender == self.subscript:
            self.basic.toggleSubscript()
        elif sender == self.superscript:
            self.basic.toggleSuperscript()
        elif sender == self.strikethrough:
            self.extended.toggleStrikethrough()
        elif sender == self.indent:
            self.extended.rightIndent()
        elif sender == self.outdent:
            self.extended.leftIndent()
        elif sender == self.justifyLeft:
            self.basic.setJustification(RichTextAreaConsts.LEFT)
        elif sender == self.justifyCenter:
            self.basic.setJustification(RichTextAreaConsts.CENTER)
        elif sender == self.justifyRight:
            self.basic.setJustification(RichTextAreaConsts.RIGHT)
        elif sender == self.insertImage:
            url = Window.prompt("Enter an image URL:", "http:#")
            if url is not None:
                self.extended.insertImage(url)

        elif sender == self.createLink:
            EventLinkPopup.open(self)

        elif sender == self.removeLink:
            self.extended.removeLink()
        elif sender == self.hr:
            self.extended.insertHorizontalRule()
        elif sender == self.ol:
            self.extended.insertOrderedList()
        elif sender == self.ul:
            self.extended.insertUnorderedList()
        elif sender == self.removeFormat:
            self.extended.removeFormat()
        elif sender == self.richText:
            # We use the RichTextArea's onKeyUp event to update the
            # toolbar status.  This will catch any cases where the
            # user moves the cursor using the keyboard, or uses one of
            # the browser's built-in keyboard shortcuts.
            self.updateStatus()

        self.checkForChange()

    def onKeyDown(self, sender, keyCode, modifiers):
        pass

    def onKeyPress(self, sender, keyCode, modifiers):
        pass

    def onKeyUp(self, sender, keyCode, modifiers):
        if sender == self.richText:
            # We use the RichTextArea's onKeyUp event to update the
            # toolbar status.  This will catch any cases where the user
            # moves the cursor using the keyboard, or uses one of
            # the browser's built-in keyboard shortcuts.
            self.updateStatus()
            self.checkForChange()

    def onMouseLeave(self, event):
        pass

    def onMouseEnter(self, event):
        pass

    def onMouseUp(self, event, x, y):
        pass

    def onMouseMove(self, event, x, y):
        pass

    def onMouseDown(self, event, x, y):
        self.trigger = True

    def onLostFocus(self, event):
        self.checkForChange()

    def onMouseOut(self, event):
        if self.isInText  and  self.isOnTextBorder(event):
            self.isInText = False
            self.captureSelection()
            self.endSelTimer()

    def onMouseOver(self, event):
        if not self.isInText:
            self.isInText = True
            self.richText.setFocus(True)
            self.lastRange = None
            self.startSelTimer()


    def setFocus(self, wid):
        self._wid = wid # hack
        DeferredCommand.add(getattr(self, "execute_set_focus"))

    def execute_set_focus(self):
        self._wid.setFocus(True)

    def findNodeByNumber(self, num):

        doc = self.getDocument()
        res = getAdjacentTextElement(doc, True)
        while (res is not None)  and  (num > 0):
            num -= 1
            res = getAdjacentTextElement(res, True)

        return res

    def selectNodes(self, startNode, startOffset, endNode=None, endOffset=None):

        startText = self.findNodeByNumber(startNode)
        if endNode is not None:
            endText = self.findNodeByNumber(endNode)
        else:
            endText = startText
            endOffset = startOffset

        rng = Range(RangeEndPoint(startText, startOffset),
                    RangeEndPoint(endText, endOffset))

        self.getSelection()
        Selection.setRange(rng)

        self.refresh()

    def font1(self):
        self._surround(FontFamilyManager, "Times New Roman")

    def font2(self):
        self._surround(FontFamilyManager, "Arial")

    def surround1(self):
        self._surround(CustomStyleManager, "editor-cls1")

    def surround2(self):
        self._surround(CustomStyleManager, "editor-cls2")

    def _surround(self, kls, cls):
        """ this is possibly one of the most truly dreadful bits of code
            for manipulating DOM ever written.  its purpose is to add only
            the editor class required, and no more.  unfortunately, DOM gets
            chopped up by the range thing, and a bit more besides.  so we
            have to:

            * extract the range contents
            * clean up removing any blank text nodes that got created above
            * slap a span round it
            * clean up removing any blank text nodes that got created above
            * remove any prior editor styles on the range contents
            * go hunting through the entire document for stacked editor styles

            this latter is funfunfun because only "spans with editor styles
            which themselves have no child elements but a single span with
            an editor style" must be removed.  e.g. if an outer editor span
            has another editor span and also some text, the outer span must
            be left alone.
        """
        rng = self.getRange()
        if (rng is None)  or rng.isCursor():
            return

        csm = kls(rng.m_document, cls)

        rng.ensureRange()
        dfrag = rng.m_range.extractContents()
        remove_editor_styles(rng.m_document, csm, dfrag)
        element = csm.create()
        DOM.appendChild(element, dfrag)
        rng.m_range.insertNode(element)

        it = DOM.IterWalkChildren(element, True)
        while True:
            try:
                node = it.next()
            except StopIteration:
                break
            if node.nodeType == 3 and unicode(node.data) == u'':
                DOM.removeChild(node.parentNode, node)

        rng.setRange(element)

        it = DOM.IterWalkChildren(rng.m_document, True)
        while True:
            try:
                node = it.next()
            except StopIteration:
                break
            if node.nodeType == 3 and unicode(node.data) == u'':
                DOM.removeChild(node.parentNode, node)

        # clears out all nodes with no children.
        it = DOM.IterWalkChildren(rng.m_document)
        while True:
            try:
                node = it.next()
            except StopIteration:
                break
            if node.firstChild or not csm.identify(node):
                continue
            DOM.removeChild(node.parentNode, node)

        it = DOM.IterWalkChildren(rng.m_document, True)
        while True:
            try:
                node = it.next()
            except StopIteration:
                break
            if not csm.identify(node):
                continue
            if node.firstChild is None:
                continue
            if not csm.identify(node.firstChild):
                continue
            if node.firstChild.nextSibling:
                continue
            # remove the *outer* one because the range was added to
            # the inner, and the inner one overrides anyway

            remove_node(rng.m_document, node)

        doc = self.getDocument()

        self.getSelection()
        Selection.setRange(rng)
        self.refresh()

    def refresh(self):
        self._parent.refresh()

    def delete(self):
        rng = self.getRange()
        if rng is None  or  rng.isCursor():
            return
        rng.deleteContents()
        refresh()

    def toCursor(self, start):
        rng = self.getRange()
        if rng is None  or  rng.isCursor():
            return
        rng.collapse(start)
        self.getSelection()
        Selection.setRange(rng)
        self.refresh()

    def run(self):
        try:
            self.getSelection()
            rng = Selection.getRange()
            if (self.timerRange is None) or (not self.timerRange.equals(rng)):
                self.onSelectionChange(rng)
                self.timerRange = rng

        except:
            GWT.log("Error in timer selection", ex)

    def getSelection(self):
        res = None
        try:
            window = self.getWindow()
            Selection.getSelection(window)

        except:
            print "Error getting the selection"
            traceback.print_exc()

    def getWindow(self, iFrame=None):
        if iFrame is None:
            iFrame = self.richText.getElement()
        iFrameWin = iFrame.contentWindow or iFrame.contentDocument

        if not iFrameWin.document:
            iFrameWin = iFrameWin.parentNode # FBJS version of parentNode

        #print "getWindow", iFrameWin, dir(iFrameWin)

        return iFrameWin

    def captureSelection(self):
        """ This captures the selection when the mouse leaves the RTE,
            because in IE the selection indicating the cursor position
            is lost once another widget gains focus.
            Could be implemented for IE only.
        """
        try:
            self.getSelection()
            self.lastRange = Selection.getRange()

        except:
            GWT.log("Error capturing selection for IE", ex)

    # Gets run every time the selection is changed
    def onSelectionChange(self, sel):
        pass

    def isOnTextBorder(self, event):
        sender = event.getSource()
        twX = self.richText.getAbsoluteLeft()
        twY = self.richText.getAbsoluteTop()
        x = event.getClientX() - twX
        y = event.getClientY() - twY
        width = self.richText.getOffsetWidth()
        height = self.richText.getOffsetHeight()
        return ((sender == self.richText)  and
        ((x <= 0)  or  (x >= width)  or
        (y <= 0)  or  (y >= height)))

    def startSelTimer(self):
        self.selTimer.scheduleRepeating(250)

    def endSelTimer(self):
        self.selTimer.cancel()

    def getRange(self):
        if self.lastRange is None:
            self.getSelection()
            return Selection.getRange()
        else:
            return self.lastRange

    def checkForChange(self):
        text = self.richText.getHTML()
        if text == self.lastText:
            return
        nEvt = doc().createEvent("HTMLEvents")
        nEvt.initEvent("change", False, True)
        self.getElement().dispatchEvent(nEvt)
        self.lastText = text

    def setHtml(self, text):
        self.richText.setHTML(text)
        self.lastText = text

    def getHtml(self):
        return self.richText.getHTML()

    def getDocument(self):
        return Selection.getDocument(self.getWindow())

    def getFormatter(self):
        return self.richText.getExtendedFormatter()


