Notes on editing the notebook's stylesheets
============================================

The Sage Notebook uses `Sass <http://sass-lang.com>`_ and `Compass
<http://wiki.github.com/chriseppstein/compass>`_ for its
stylesheets. Sass is a styling language that compiles down to CSS, and
has support for mixins, nesting, variables, and basic
operations. Compass is a CSS meta-framework that uses Sass and
incorporates Sass-ified versions of most common CSS frameworks.

Installing Sass and Compass
----------------------------

Sass and Compass currently require Ruby 1.8.7 and
RubyGems. Installation is simply installing HAML, which includes
Sass::

    $ gem install haml

and then Compass::

    $ gem sources --add http://gems.github.com/
    $ gem install chriseppstein-compass

Editing the SASS stylesheets
-----------------------------

To edit the SASS stylesheets, simply cd to sass/ and run compass::

    $ cd sass
    $ compass --watch

This will automatically compile any changes made to the Sass
files. The Sass files themselves are included at ``sass/src``.
