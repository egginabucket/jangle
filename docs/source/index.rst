Welcome to jangle's documentation!
==================================

Jangle is a Django app with database models and other utilities
for working with IETF BCP 47 / `RFC 5646 <https://www.rfc-editor.org/rfc/rfc5646.html>`_ language tags.

Jangle provides a full database representing the IANA subtag registry,
linked to other standards such as
ISO 639-1, 639-2, 639-3, 639-5, 15924, and 3166 (WIP).
These are saved from various sources, including
the Library of Congress, SIL International, and unicode.org.

See :doc:`quickstart` to get started!

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   lite
   patterns
   models/index
   models/languages
   models/scripts
   models/regions
   models/tags
   readers
   utils


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
