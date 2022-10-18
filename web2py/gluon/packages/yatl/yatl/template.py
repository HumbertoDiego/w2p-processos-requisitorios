#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
| This file was extracted from the web2py Web Framework and made framework independent
| License: BSD
"""

import logging
import os
import sys
from functools import wraps
from re import compile, sub, escape, DOTALL
from . helpers import xmlescape

PY2 = sys.version_info[0] == 2

if PY2:
    from cStringIO import StringIO
    unicodeT = unicode

    def to_bytes(obj, charset='utf-8', errors='strict'):
        return bytes(obj) if isinstance(obj, (bytes, bytearray, buffer)) else obj.encode(charset, errors)

    def to_native(obj, charset='utf8', errors='strict'):
        return obj if isinstance(obj, str) else obj.encode(charset, errors)

else:
    from io import StringIO
    basestring = str
    unicodeT = str

    def to_bytes(obj, charset='utf-8', errors='strict'):
        return bytes(obj) if isinstance(obj, (bytes, bytearray, memoryview)) else obj.encode(charset, errors)

    def to_native(obj, charset='utf8', errors='strict'):
        return obj if isinstance(obj, str) else obj.decode(charset, errors)


DEFAULT_DELIMITERS = ('{{', '}}')


def file_reader(filename, mode='rb'):
    try:
        with open(filename, mode) as fp:
            body = fp.read()
        return body
    except IOError:
        raise RestrictedError(filename, '', 'Unable to find the file')

try:
    # have web2py
    from gluon.restricted import RestrictedError
    from gluon.globals import current
except ImportError:
    # do not have web2py
    current = None

    def RestrictedError(a, b, c):
        logging.error(str(a) + ':' + str(b) + ':' + str(c))
        return RuntimeError


class Node(object):
    """
    Basic Container Object
    """
    def __init__(self, value=None, pre_extend=False):
        self.value = value
        self.pre_extend = pre_extend

    def __str__(self):
        return str(self.value)


class SuperNode(Node):
    def __init__(self, name='', pre_extend=False):
        self.name = name
        self.value = None
        self.pre_extend = pre_extend

    def __str__(self):
        if self.value:
            return str(self.value)
        else:
            return ''

    def __repr__(self):
        return "%s->%s" % (self.name, self.value)


def output_aux(node, blocks):
    # If we have a block level
    #   If we can override this block.
    #     Override block from vars.
    #   Else we take the default
    # Else its just a string
    return (blocks[node.name].output(blocks)
            if node.name in blocks else
            node.output(blocks)) \
        if isinstance(node, BlockNode) \
        else str(node)


class BlockNode(Node):
    """
    Block Container.

    This Node can contain other Nodes and will render in a hierarchical order
    of when nodes were added.

    ie::

        {{ block test }}
            This is default block test
        {{ end }}

    """
    def __init__(self, name='', pre_extend=False, delimiters=None):
        """
        name - Name of this Node.
        """
        self.nodes = []
        self.name = name
        self.pre_extend = pre_extend
        self.left, self.right = delimiters

    def __repr__(self):
        lines = ['%sblock %s%s' % (self.left, self.name, self.right)]
        lines += [str(node) for node in self.nodes]
        lines.append('%send%s' % (self.left, self.right))
        return ''.join(lines)

    def __str__(self):
        """
        Get this BlockNodes content, not including child Nodes
        """
        return ''.join(str(node) for node in self.nodes
                       if not isinstance(node, BlockNode))

    def append(self, node):
        """
        Adds an element to the nodes.

        Args:
            node: Node object or string to append.
        """
        if isinstance(node, str) or isinstance(node, Node):
            self.nodes.append(node)
        else:
            raise TypeError("Invalid type; must be instance of ``str`` or ``BlockNode``. %s" % node)

    def extend(self, other):
        """
        Extends the list of nodes with another BlockNode class.

        Args:
            other: BlockNode or Content object to extend from.
        """
        if isinstance(other, BlockNode):
            self.nodes.extend(other.nodes)
        else:
            raise TypeError(
                "Invalid type; must be instance of ``BlockNode``. %s" % other)

    def output(self, blocks):
        """
        Merges all nodes into a single string.

        Args:
            blocks: Dictionary of blocks that are extending from this template.
        """
        return ''.join(output_aux(node, blocks) for node in self.nodes)


class Content(BlockNode):
    """
    Parent Container -- Used as the root level BlockNode.

    Contains functions that operate as such.

    Args:
        name: Unique name for this BlockNode
    """
    def __init__(self, name="ContentBlock", pre_extend=False):
        self.name = name
        self.nodes = []
        self.blocks = {}
        self.pre_extend = pre_extend

    def __str__(self):
        return ''.join(output_aux(node, self.blocks) for node in self.nodes)

    def _insert(self, other, index=0):
        """
        Inserts object at index.
        """
        if isinstance(other, (str, Node)):
            self.nodes.insert(index, other)
        else:
            raise TypeError(
                "Invalid type, must be instance of ``str`` or ``Node``.")

    def insert(self, other, index=0):
        """
        Inserts object at index.

        You may pass a list of objects and have them inserted.
        """
        if isinstance(other, (list, tuple)):
            # Must reverse so the order stays the same.
            other.reverse()
            for item in other:
                self._insert(item, index)
        else:
            self._insert(other, index)

    def append(self, node):
        """
        Adds a node to list. If it is a BlockNode then we assign a block for it.
        """
        if isinstance(node, (str, Node)):
            self.nodes.append(node)
            if isinstance(node, BlockNode):
                self.blocks[node.name] = node
        else:
            raise TypeError("Invalid type, must be instance of ``str`` or ``BlockNode``. %s" % node)

    def extend(self, other):
        """
        Extends the objects list of nodes with another objects nodes
        """
        if isinstance(other, BlockNode):
            self.nodes.extend(other.nodes)
            self.blocks.update(other.blocks)
        else:
            raise TypeError(
                "Invalid type; must be instance of ``BlockNode``. %s" % other)

    def clear_content(self):
        self.nodes = []


class TemplateParser(object):
    """Parse all blocks

    Args:
        text: text to parse
        context: context to parse in
        path: folder path to templates
        writer: string of writer class to use
        lexers: dict of custom lexers to use.
        delimiters: for example `('{{','}}')`
        _super_nodes: a list of nodes to check for inclusion
            this should only be set by "self.extend"
            It contains a list of SuperNodes from a child
            template that need to be handled.

    """
    r_multiline = compile(r'(""".*?""")|(\'\'\'.*?\'\'\')', DOTALL)

    # These are used for re-indentation.
    # Indent + 1
    re_block = compile('^(elif |else:|except:|except |finally:).*$', DOTALL)

    # Indent - 1
    re_unblock = compile('^(return|continue|break|raise)( .*)?$', DOTALL)
    # Indent - 1
    re_pass = compile('^pass( .*)?$', DOTALL)

    def __init__(self, text,
                 name="ParserContainer",
                 context=None,
                 path='views/',
                 writer='response.write',
                 lexers=None,
                 delimiters=None,
                 _super_nodes = None,
                 reader=None,
                 ):

        context = context or {}
        # Keep a root level name.
        self.name = name
        # Raw text to start parsing.
        self.text = text
        # use the default reader
        self.reader = reader or file_reader
        # Writer to use (refer to the default for an example).
        # This will end up as
        # "%s(%s, escape=False)" % (self.writer, value)
        self.writer = writer
        # Dictionary of custom name lexers to use.
        if isinstance(lexers, dict):
            self.lexers = lexers
        else:
            self.lexers = {}
        if _super_nodes is None:
            _super_nodes = []
        if delimiters is None:
            delimiters = DEFAULT_DELIMITERS

        # Path of templates
        self.path = path
        # Context for templates.
        self.context = context

        self.delimiters = delimiters
        escaped_delimiters = (escape(delimiters[0]), escape(delimiters[1]))
        self.r_tag = compile('(%s.*?%s)' % escaped_delimiters, DOTALL)

        # Create a root level Content that everything will go into.
        self.content = Content(name=name)

        # Stack will hold our current stack of nodes.
        # As we descend into a node, it will be added to the stack
        # And when we leave, it will be removed from the stack.
        # self.content should stay on the stack at all times.
        self.stack = [self.content]

        # This variable will hold a reference to every super block
        # that we come across in this template.
        self.super_nodes = []

        # This variable will hold a reference to the child
        # super nodes that need handling.
        self.child_super_nodes = _super_nodes

        # This variable will hold a reference to every block
        # that we come across in this template
        self.blocks = {}

        # Begin parsing.
        self.parse(text)

    def to_string(self):
        """
        Returns the parsed template with correct indentation.

        Used to make it easier to port to python3.
        """
        return self.reindent(str(self.content))

    def __str__(self):
        "Makes sure str works exactly the same as python 3"
        return self.to_string()

    def __unicode__(self):
        "Makes sure str works exactly the same as python 3"
        return self.to_string()

    def reindent(self, text):
        """
        Reindents a string of unindented python code.
        """

        # Get each of our lines into an array.
        lines = text.split('\n')

        # Our new lines
        new_lines = []

        # Keeps track of how many indents we have.
        # Used for when we need to drop a level of indentation
        # only to reindent on the next line.
        credit = 0

        # Current indentation
        k = 0

        #################
        # THINGS TO KNOW
        #################

        # k += 1 means indent
        # k -= 1 means unindent
        # credit = 1 means unindent on the next line.

        for raw_line in lines:
            line = raw_line.strip()

            # ignore empty lines
            if not line:
                continue

            # If we have a line that contains python code that
            # should be unindented for this line of code.
            # and then reindented for the next line.
            if TemplateParser.re_block.match(line):
                k = k + credit - 1

            # We obviously can't have a negative indentation
            k = max(k, 0)

            # Add the indentation!
            new_lines.append(' ' * (4 * k) + line)

            # Bank account back to 0 again :(
            credit = 0

            # If we are a pass block, we obviously de-dent.
            if TemplateParser.re_pass.match(line):
                k -= 1

            # If we are any of the following, de-dent.
            # However, we should stay on the same level
            # But the line right after us will be de-dented.
            # So we add one credit to keep us at the level
            # while moving back one indentation level.
            if TemplateParser.re_unblock.match(line):
                credit = 1
                k -= 1

            # If we are an if statement, a try, or a semi-colon we
            # probably need to indent the next line.
            if line.endswith(':') and not line.startswith('#'):
                k += 1

        # This must come before so that we can raise an error with the
        # right content.
        new_text = '\n'.join(new_lines)

        if k > 0:
            self._raise_error('missing "pass" in view', new_text)
        elif k < 0:
            self._raise_error('too many "pass" in view', new_text)

        return new_text

    def _raise_error(self, message='', text=None):
        """
        Raises an error using itself as the filename and textual content.
        """
        raise RestrictedError(self.name, text or self.text, message)

    def _get_file_text(self, filename):
        """
        Attempts to open ``filename`` and retrieve its text.

        This will use self.path to search for the file.
        """

        # If they didn't specify a filename, how can we find one!
        if not filename.strip():
            self._raise_error('Invalid template filename')

        # Allow Views to include other views dynamically
        context = self.context
        if current and "response" not in context:
            context["response"] = getattr(current, 'response', None)

        # Get the filename; filename looks like ``"template.html"``.
        # We need to eval to remove the quotes and get the string type.
        filename = eval(filename, context)

        # Allow empty filename for conditional extend and include directives.
        if not filename:
            return ''

        # Get the path of the file on the system.
        if callable(self.path):
            text = self.path(filename)
        else:
            filepath = self.path and os.path.join(self.path, filename) or filename
            # try to read the text.
            try:
                text = self.reader(filepath)
            except IOError:
                self._raise_error('Unable to open included view file: ' + filepath)
        text = to_native(text)
        return text

    def include(self, content, filename):
        """
        Includes ``filename`` here.
        """
        text = self._get_file_text(filename)

        t = TemplateParser(text,
                           name=filename,
                           context=self.context,
                           path=self.path,
                           writer=self.writer,
                           delimiters=self.delimiters,
                           reader=self.reader)

        content.append(t.content)

    def extend(self, filename):
        """
        Extends `filename`. Anything not declared in a block defined by the
        parent will be placed in the parent templates `{{include}}` block.
        """
        # If no filename, create a dummy layout with only an {{include}}.
        text = self._get_file_text(filename) or '%sinclude%s' % tuple(self.delimiters)

        # Create out nodes list to send to the parent
        super_nodes = []
        # We want to include any non-handled nodes.
        super_nodes.extend(self.child_super_nodes)
        # And our nodes as well.
        super_nodes.extend(self.super_nodes)

        t = TemplateParser(text,
                           name=filename,
                           context=self.context,
                           path=self.path,
                           writer=self.writer,
                           delimiters=self.delimiters,
                           _super_nodes=super_nodes,
                           reader=self.reader)

        # Make a temporary buffer that is unique for parent
        # template.
        buf = BlockNode(
            name='__include__' + filename, delimiters=self.delimiters)
        pre = []

        # Iterate through each of our nodes
        for node in self.content.nodes:
            # If a node is a block
            if isinstance(node, BlockNode):
                # That happens to be in the parent template
                if node.name in t.content.blocks:
                    # Do not include it
                    continue

            if isinstance(node, Node):
                # Or if the node was before the extension
                # we should not include it
                if node.pre_extend:
                    pre.append(node)
                    continue

            # Otherwise, it should go int the
            # Parent templates {{include}} section.
                buf.append(node)
            else:
                buf.append(node)

        # Clear our current nodes. We will be replacing this with
        # the parent nodes.
        self.content.nodes = []

        t_content = t.content

        # Set our include, unique by filename
        t_content.blocks['__include__' + filename] = buf

        # Make sure our pre_extended nodes go first
        t_content.insert(pre)

        # Then we extend our blocks
        t_content.extend(self.content)

        # Work off the parent node.
        self.content = t_content

    def parse(self, text):

        # Basically, r_tag.split will split the text into
        # an array containing, 'non-tag', 'tag', 'non-tag', 'tag'
        # so if we alternate this variable, we know
        # what to look for. This is alternate to
        # line.startswith("{{")
        in_tag = False
        extend = None
        pre_extend = True

        # Use a list to store everything in
        # This is because later the code will "look ahead"
        # for missing strings or brackets.
        ij = self.r_tag.split(to_native(text))
        # j = current index
        # i = current item
        stack = self.stack
        for j in range(len(ij)):
            i = ij[j]

            if i:
                if not stack:
                    self._raise_error('The "end" tag is unmatched, please check if you have a starting "block" tag')

                # Our current element in the stack.
                top = stack[-1]

                if in_tag:
                    line = i

                    # Get rid of delimiters
                    line = line[len(self.delimiters[0]): -len(self.delimiters[1])].strip()

                    # This is bad juju, but let's do it anyway
                    if not line:
                        continue

                    # We do not want to replace the newlines in code,
                    # only in block comments.
                    def remove_newline(re_val):
                        # Take the entire match and replace newlines with
                        # escaped newlines.
                        return re_val.group(0).replace('\n', '\\n')

                    # Perform block comment escaping.
                    # This performs escaping ON anything
                    # in between """ and """
                    line = sub(TemplateParser.r_multiline,
                               remove_newline,
                               line)

                    if line.startswith('='):
                        # IE: {{=response.title}}
                        name, value = '=', line[1:].strip()
                    else:
                        v = line.split(' ', 1)
                        if len(v) == 1:
                            # Example
                            # {{ include }}
                            # {{ end }}
                            name = v[0]
                            value = ''
                        else:
                            # Example
                            # {{ block pie }}
                            # {{ include "layout.html" }}
                            # {{ for i in range(10): }}
                            name = v[0]
                            value = v[1]

                    # This will replace newlines in block comments
                    # with the newline character. This is so that they
                    # retain their formatting, but squish down to one
                    # line in the rendered template.

                    # First check if we have any custom lexers
                    if name in self.lexers:
                        # Pass the information to the lexer
                        # and allow it to inject in the environment

                        # You can define custom names such as
                        # '{{<<variable}}' which could potentially
                        # write unescaped version of the variable.
                        self.lexers[name](parser=self,
                                          value=value,
                                          top=top,
                                          stack=stack)

                    elif name == '=':
                        # So we have a variable to insert into
                        # the template
                        buf = "\n%s(%s)" % (self.writer, value)
                        top.append(Node(buf, pre_extend=pre_extend))

                    elif name == 'block' and not value.startswith('='):
                        # Make a new node with name.
                        node = BlockNode(name=value.strip(),
                                         pre_extend=pre_extend,
                                         delimiters=self.delimiters)

                        # Append this node to our active node
                        top.append(node)

                        # Make sure to add the node to the stack.
                        # so anything after this gets added
                        # to this node. This allows us to
                        # "nest" nodes.
                        stack.append(node)

                    elif name == 'end' and not value.startswith('='):
                        # We are done with this node.

                        # Save an instance of it
                        self.blocks[top.name] = top

                        # Pop it.
                        stack.pop()

                    elif name == 'super' and not value.startswith('='):
                        # Get our correct target name
                        # If they just called {{super}} without a name
                        # attempt to assume the top blocks name.
                        if value:
                            target_node = value
                        else:
                            target_node = top.name

                        # Create a SuperNode instance
                        node = SuperNode(name=target_node,
                                         pre_extend=pre_extend)

                        # Add this to our list to be taken care of
                        self.super_nodes.append(node)

                        # And put in in the tree
                        top.append(node)

                    elif name == 'include' and not value.startswith('='):
                        # If we know the target file to include
                        if value:
                            self.include(top, value)

                        # Otherwise, make a temporary include node
                        # That the child node will know to hook into.
                        else:
                            include_node = BlockNode(
                                name='__include__' + self.name,
                                pre_extend=pre_extend,
                                delimiters=self.delimiters)
                            top.append(include_node)

                    elif name == 'extend' and not value.startswith('='):
                        # We need to extend the following
                        # template.
                        extend = value
                        pre_extend = False

                    else:
                        # If we don't know where it belongs
                        # we just add it anyways without formatting.
                        if line and in_tag:

                            # Split on the newlines >.<
                            tokens = line.split('\n')

                            # We need to look for any instances of
                            # for i in range(10):
                            #   = i
                            # pass
                            # So we can properly put a response.write() in place.
                            continuation = False
                            len_parsed = 0
                            for k, token in enumerate(tokens):

                                token = tokens[k] = token.strip()
                                len_parsed += len(token)

                                if token.startswith('='):
                                    if token.endswith('\\'):
                                        continuation = True
                                        tokens[k] = "\n%s(%s" % (
                                            self.writer, token[1:].strip())
                                    else:
                                        tokens[k] = "\n%s(%s)" % (
                                            self.writer, token[1:].strip())
                                elif continuation:
                                    tokens[k] += ')'
                                    continuation = False

                            buf = "\n%s" % '\n'.join(tokens)
                            top.append(Node(buf, pre_extend=pre_extend))

                else:
                    # It is HTML so just include it.
                    buf = "\n%s(%r, escape=False)" % (self.writer, i)
                    top.append(Node(buf, pre_extend=pre_extend))

            # Remember: tag, not tag, tag, not tag
            in_tag = not in_tag

        # Make a list of items to remove from child
        to_rm = []

        # Go through each of the children nodes
        for node in self.child_super_nodes:
            # If we declared a block that this node wants to include
            if node.name in self.blocks:
                # Go ahead and include it!
                node.value = self.blocks[node.name]
                # Since we processed this child, we don't need to
                # pass it along to the parent
                to_rm.append(node)

        # Remove some of the processed nodes
        for node in to_rm:
            # Since this is a pointer, it works beautifully.
            # Sometimes I miss C-Style pointers... I want my asterisk...
            self.child_super_nodes.remove(node)

        # If we need to extend a template.
        if extend:
            self.extend(extend)

# We need this for integration with gluon

def parse_template(filename,
                   path='views/',
                   context=None,
                   lexers=None,
                   delimiters=None,
                   reader=None
                   ):
    """
    Args:
        filename: can be a view filename in the views folder or an input stream
        path: is the path of a views folder of to a function to load the filename
        context: is a dictionary of symbols used to render the template
        lexers: dict of custom lexers to use
        delimiters: opening and closing tags
    """
    context = context or {}
    lexers = lexers or {}
    delimiters = delimiters or DEFAULT_DELIMITERS
    reader = reader or file_reader
    # First, if we have a str try to open the file
    if isinstance(filename, basestring):
        if callable(path):
            text = path(filename)
        else:
            fname = os.path.join(path, filename)
            text = file_reader(fname)
    else:
        text = filename.read()
    text = to_native(text)
    # allow optional alternative delimiters
    if hasattr(context.get('response', None), 'delimiters'):
        if context['response'].delimiters is not None:
            delimiters = context['response'].delimiters
    # Use the file contents to get a parsed template and return it.
    return str(TemplateParser(text, context=context, path=path, lexers=lexers, delimiters=delimiters, reader=reader))


class DummyResponse():
    def __init__(self):
        self.body = StringIO()

    def write(self, data, escape=True):
        if not escape:
            data = str(data)
        elif hasattr(data, 'xml') and callable(data.xml):
            data = data.xml()
        else:
            if PY2 and isinstance(data, unicodeT):
                # in python2 we always encode unicode
                data = data.encode('utf8', 'xmlcharrefreplace')                
            else:
                # in python3 we always use unicode
                data = str(data)
            data = xmlescape(data)
        self.body.write(str(data))


class NOESCAPE():
    """
    A little helper to avoid escaping.
    """
    def __init__(self, text):
        self.text = text

    def xml(self):
        return self.text

# And this is a generic render function.
# Here for integration with gluon.


def render(content=None,
           stream=None,
           filename=None,
           path=None,
           context=None,
           lexers=None,
           delimiters='{{ }}',
           writer='response.write',
           reader=None
           ):
    """
    Generic render function

    Args:
        content: default content
        stream: file-like obj to read template from
        filename: where to find template
        path: base path for templates
        context: env
        lexers: custom lexers to use
        delimiters: opening and closing tags
        writer: where to inject the resulting stream

    Example::
        >>> render()
        'hello world'
        >>> render(content='abc')
        'abc'
        >>> render(content="abc'")
        "abc'"
        >>> render(content=''''a"'bc''')
        'a"'bc'
        >>> render(content='a\\nbc')
        'a\\nbc'
        >>> render(content='a"bcd"e')
        'a"bcd"e'
        >>> render(content="'''a\\nc'''")
        "'''a\\nc'''"
        >>> render(content="'''a\\'c'''")
        "'''a\'c'''"
        >>> render(content='{{for i in range(a):}}{{=i}}<br />{{pass}}', context=dict(a=5))
        '0<br />1<br />2<br />3<br />4<br />'
        >>> render(content='{%for i in range(a):%}{%=i%}<br />{%pass%}', context=dict(a=5),delimiters=('{%','%}'))
        '0<br />1<br />2<br />3<br />4<br />'
        >>> render(content="{{='''hello\\nworld'''}}")
        'hello\\nworld'
        >>> render(content='{{for i in range(3):\\n=i\\npass}}')
        '012'

    """

    # If we don't have anything to render, why bother?
    if content is None and stream is None and filename is None:
        raise SyntaxError("Must specify a stream or filename or content")

    # handle defaults
    if context is None:
        context = {}
    if lexers is None:
        lexers = {}
    if isinstance(delimiters, basestring):
        delimiters = delimiters.split(' ',1)
    if not reader:
        reader = file_reader

    # allow optional alternative delimiters
    if hasattr(context.get('response', None), 'delimiters'):
        if context['response'].delimiters is not None:
            delimiters = context['response'].delimiters

    # here to avoid circular Imports
    try:
        from gluon.globals import Response
    except ImportError:
        # Working standalone. Build a mock Response object.
        Response = DummyResponse

        # Add it to the context so we can use it.
        if 'NOESCAPE' not in context:
            context['NOESCAPE'] = NOESCAPE

    if isinstance(content, unicodeT):
        content = content.encode('utf8')

    # save current response class
    if context and 'response' in context:
        old_response_body = context['response'].body
        context['response'].body = StringIO()
    else:
        old_response_body = None
        context['response'] = Response()


    if content is None:
        if stream is not None:
            content = stream.read()
        elif filename is not None:
            content = reader(filename)
        else:
            content = '(no template found)'

    # Execute the template.
    code = str(TemplateParser(text=content,
                              context=context,
                              path=path,
                              lexers=lexers,
                              delimiters=delimiters,
                              writer=writer,
                              reader=reader))

    try:
        exec(code, context)
    except Exception:
        # for i,line in enumerate(code.split('\n')): print i,line
        raise

    # Returned the rendered content.
    text = context['response'].body.getvalue()
    if old_response_body is not None:
        context['response'].body = old_response_body
    return text

class template(object):

    def __init__(self, filename='{name}.html', body=None, path=None, lexers=None, delimiters=None, reader=None):
        self.filename = filename
        self.body = body
        self.path = path
        self.lexers = lexers
        self.delimiters = delimiters
        self.reader = reader or file_reader

    def __call__(self, func):
        @wraps(func)
        def wrapper(*a, **b):
            context = func(*a, **b)
            if isinstance(context, dict):
                filename = self.filename.format(name=func.__name__)
                if self.body:
                    body = self.body
                else:
                    body = self.reader(filename)
                return render(
                    content=body,
                    path=self.path,
                    lexers=self.lexers,
                    delimiters=self.delimiters,
                    context=context,
                    reader=self.reader)
            else:
                return context
        return wrapper

