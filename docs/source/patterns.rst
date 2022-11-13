RegEx Patterns
--------------

Jangle uses a variety of regular expressions for validating and parsing
language tags.
All rules from the `RFC 5646 ABNF syntax definition <https://www.rfc-editor.org/rfc/rfc5646.html#section-2.1>`_
have now been implemented!

.. note::

   Some patterns are case-sensitive,
   which is incompliant with
   `RFC 5646 section 2.1 <https://www.rfc-editor.org/rfc/rfc5646.html#section-2.1>`_.
   `RULES` are compiled with the `I` flag -- always pass this flag
   if you are compiling elsewhere.


Language-Tag:

:regexp:`(?P<grandfathered>(?P<regular>art\\-lojban|cel\\-gaulish|no\\-bok|no\\-nyn|zh\\-guoyo|zh\\-hakka|zh\\-min|zh\\-min\\-nan|zh\\-xiang)|(?P<irregular>en\\-GB\\-oed|i\\-(?:ami|bnn|default|enochian|hak|klingon|lux|mingo|navajo|tao|tay|tsu)|sgn\\-(?:BE\\-FR|BE\\-NL|CH\\-DE)))|(?P<private_tag>x(?:\\-[A-Za-z\\d]{1,8})+)|(?P<langtag>(?P<iso_639>[A-Za-z]{2,3})(?:\\-(?P<extlang>(?P<extlang_iso_639>[A-Za-z]{3})(?P<extlang_reserved>(?:\\-[A-Za-z]{3}){0,2})))?(?![^\\-\\s])(?:\\-(?P<script>[A-Za-z]{4})(?![^\\-\\s]))?(?:\\-(?P<region>(?P<iso_3166>[A-Za-z]{2})|(?P<un_m49>\\d{3}))(?![^\\-\\s]))?(?P<variants>(?:\\-(?:[A-Za-z\\d]{5,8}|\\d[A-Za-z\\d]{3}))*)(?P<extensions>(?:\\-(?P<singleton>[A-WY-Za-wy-z\\d])(?P<ext_text>(?:\\-[A-Za-z\\d]{2,8})+))*)(?:\\-(?P<private_subtag>x(?:\\-[A-Za-z\\d]{1,8})+))?)`

langtag:

:regexp:`(?P<iso_639>[A-Za-z]{2,3})(?:\\-(?P<extlang>(?P<extlang_iso_639>[A-Za-z]{3})(?P<extlang_reserved>(?:\\-[A-Za-z]{3}){0,2})))?(?![^\\-\\s])(?:\\-(?P<script>[A-Za-z]{4})(?![^\\-\\s]))?(?:\\-(?P<region>(?P<iso_3166>[A-Za-z]{2})|(?P<un_m49>\\d{3}))(?![^\\-\\s]))?(?P<variants>(?:\\-(?:[A-Za-z\\d]{5,8}|\\d[A-Za-z\\d]{3}))*)(?P<extensions>(?:\\-(?P<singleton>[A-WY-Za-wy-z\\d])(?P<ext_text>(?:\\-[A-Za-z\\d]{2,8})+))*)(?:\\-(?P<private_subtag>x(?:\\-[A-Za-z\\d]{1,8})+))?`

language:

:regexp:`(?P<iso_639>[A-Za-z]{2,3})(?:\\-(?P<extlang>(?P<extlang_iso_639>[A-Za-z]{3})(?P<extlang_reserved>(?:\\-[A-Za-z]{3}){0,2})))?`

extlang:

:regexp:`(?P<extlang_iso_639>[A-Za-z]{3})(?P<extlang_reserved>(?:\\-[A-Za-z]{3}){0,2})`

script:

:regexp:`[A-Za-z]{4}`

region:

:regexp:`(?P<iso_3166>[A-Za-z]{2})|(?P<un_m49>\\d{3})`

variant:

:regexp:`[A-Za-z\\d]{5,8}|\\d[A-Za-z\\d]{3}`

extension:

:regexp:`(?P<singleton>[A-WY-Za-wy-z\\d])(?P<ext_text>(?:\\-[A-Za-z\\d]{2,8})+)`

singleton:

:regexp:`[A-WY-Za-wy-z\\d]`

privateuse:

:regexp:`x(?:\\-[A-Za-z\\d]{1,8})+`

grandfathered:

:regexp:`(?P<regular>art\\-lojban|cel\\-gaulish|no\\-bok|no\\-nyn|zh\\-guoyo|zh\\-hakka|zh\\-min|zh\\-min\\-nan|zh\\-xiang)|(?P<irregular>en\\-GB\\-oed|i\\-(?:ami|bnn|default|enochian|hak|klingon|lux|mingo|navajo|tao|tay|tsu)|sgn\\-(?:BE\\-FR|BE\\-NL|CH\\-DE))`

regular:

:regexp:`art\\-lojban|cel\\-gaulish|no\\-bok|no\\-nyn|zh\\-guoyo|zh\\-hakka|zh\\-min|zh\\-min\\-nan|zh\\-xiang`

irregular:

:regexp:`en\\-GB\\-oed|i\\-(?:ami|bnn|default|enochian|hak|klingon|lux|mingo|navajo|tao|tay|tsu)|sgn\\-(?:BE\\-FR|BE\\-NL|CH\\-DE)`

alphanum:

:regexp:`[A-Za-z\\d]`


.. automodule:: jangle.patterns
   :members:
   :undoc-members:
