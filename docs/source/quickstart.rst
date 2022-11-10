Quickstart
----------

Install jangle from PyPI:

.. code-block:: console

   $ pip install django-jangle

Or the latest version from git:

.. code-block:: console

   $ pip install git+https://github.com/egginabucket/jangle.git

Add jangle to your installed apps:

.. code-block:: python
   
   # settings.py
   
   INSTALLED_APPS = [
       ...,
       "jangle",
   ]

Save jangle data to the DB from manage.py:

.. code-block:: console

   $ python manage.py loadjangledata
