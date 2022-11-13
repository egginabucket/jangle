Quickstart
----------

Install jangle from PyPI:

.. code-block:: console

   $ pip install django-jangle

\.\.\.or the latest version from GitHub:

.. code-block:: console

   $ pip install git+https://github.com/egginabucket/jangle.git

Add jangle to your project's installed apps:

.. code-block:: python
   :caption: settings.py
   
   INSTALLED_APPS = [
       ...
       "jangle",
   ]

Save jangle data to the project's database:

.. code-block:: console

   $ python manage.py loadjangledata
