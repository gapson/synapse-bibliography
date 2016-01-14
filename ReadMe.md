# Introduction #

The synapse-bibliography project is a fully-fledged Django site.  It is **not** a reusable, pluggable Django application, at least not yet.  The result is that you will need to download the whole thing, replace, update or modify the graphics assets and the various references to MSKCC and MSKCC-specific functionality, and customize to your liking.  It is possible, but not easy.  On the other hand, Synapse serves as a fairly reasonable example of a completed Django web site.  You may find it of some pedagogical value in learning more about Django.  I should warn, however, that the code quality in places leaves something to be desired.  There are areas that will be refactored.

# Roadmap #

Synapse-the-MSKCC-site will be adding user registration and authentication via LDAP from Active Directory.  This feature will allow for per-user customization, including saved "favorites", saved searches, and individual submission of articles by the users, for review by the librarians.  It will also allow us to put some controls in place on the REST API, which is half-finished at present.

Synapse-the-pluggable-reusable-Django-app doesn't currently exist.  However, I do plan to factor out the bibliography application from the surrounding project.  At which point, I will likely create a new Google Code project to host the standalone app, and pull it in to the Synapse site via svn externals.  The MSKCC Synapse site will likely become a [Pinax](http://pinaxproject.com) social networking site at that point.


# Dependencies #

Currently, the Synapse site has a few external dependencies:
  * [iplib](http://erlug.linux.it/~da/soft/iplib/) -- tested with v1.0, current version is 1.1 and should probably work, but no guarantees
  * jQuery 1.2.x, and a number of jQuery plugins:
    * jqModal
    * autocomplete
    * columnmanager
    * expander
    * hoverIntent
    * tablesorter
    * superfish
  * Google Analytics

### iplib ###
You may strip out iplib by editing views.py and removing the is\_internal function call from the context for each view.  I'm using iplib as a helper for adding an additional link "Inside MSKCC", to our intranet site, for those users whose IP address matches our internal ranges.  You could replace all occurrences of
`'is_internal':is_internal(request)` with `'is_internal':False` and be fine, or you could redefine the internal IP ranges for your own use.

## jQuery and friends ##
jQuery and plugins provide all the nice extras in the templates:  autocompletion of the author names and journal titles, sorting of the results, column show/hide, modal pop-ups of the individual results detail pages, the drop-down menus.  At some point I will be removing the direct installation of jQuery and pointing to Google's CDN instead, doing the same for as many of the plugins as possible.  I'll also collapse the remaining local plugins and my per-page glue scripts, for better performance.

## Google Analytics ##
The current Synapse site uses Google Analytics for web stats.  I've included a sample ga\_script.html.example, you will need to rename it to ga\_script.html and put in your own GA tracking number.  Once I factor out the reusable app from the project, I expect to use one of the recipes on [djangosnippets](http://www.djangosnippets.org) that makes GA modular and reusable, with the tracking number in settings.py.  Though, the project will then move to using settings.py and settings\_local.py, and the tracking number will go in the latter file.  Additionally, I expect to use the [django-webalizer](http://github.com/arneb/django-webalizer/) app for stats.  Depending on the utility of webalizer, I may drop GA entirely.

# Final Note #

The Synapse project is currently running on Django 1.0.2.  I took some time to update it for the 1.0 release.  I do expect to keep it up-to-date with the latest released version, and there are some new goodies in 1.1 I'm eagerly anticipating.  We'll see how much use gets made, initially, but going forward, expect to see feature additions that depend on the latest Django release.  Backwards compatibility is not a huge priority.