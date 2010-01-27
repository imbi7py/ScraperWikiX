import re
import sys
import os
import datetime
try:
  import json
except:
  import simplejson as json
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from scraper.models import Scraper as ScraperModel, UserScraperRole
from scraper import template
from scraper import vc
import forms
import settings

def delete_draft(request, short_name=None):
  if short_name == None:
    short_name = "__new__"
  if request.session['ScraperDraft'].get(short_name, None):
    draft = request.session['ScraperDraft'][short_name]
    all_drafts = request.session['ScraperDraft']
    del all_drafts[short_name]
    request.session['ScraperDraft'] = all_drafts
    if draft.short_name:
      return HttpResponseRedirect(reverse('editor', kwargs={'short_name' : draft.short_name}))
  return HttpResponseRedirect(reverse('editor'))

def delete_all_drafts(request):
  try:
    del request.session['ScraperDraft']
  except:
    pass
  return HttpResponseRedirect(reverse('frontpage'))
  
def save_draft(request, short_name=None):
  if short_name == None:
    short_name = "__new__"
  draft_form = forms.editorForm(request.POST)
  savedForm = draft_form.save(commit=False)
  savedForm.code = draft_form.cleaned_data['code']
  request.session['ScraperDraft'][short_name] = savedForm
  return HttpResponseRedirect(reverse('editor'))



def diff(request, short_name=None):
  if not short_name or short_name == "__new__":
    return HttpResponse("Draft scraper, nothing to diff against", mimetype='text')
  code = request.POST.get('code', None)    
  if code:
    scraper = get_object_or_404(ScraperModel, short_name=short_name)
    scraper.code = scraper.committed_code()
    return HttpResponse(vc.diff(scraper.code, code), mimetype='text')
  return HttpResponse("Programme error: No code sent up to diff against", mimetype='text')
    
    
def raw(request, short_name=None):
  if not short_name or short_name == "__new__":
    return HttpResponse("Draft scraper, shouldn't do reload", mimetype='text')
  scraper = get_object_or_404(ScraperModel, short_name=short_name)
  oldcodeineditor = request.POST.get('oldcode', None)
  newcode = scraper.saved_code()
  if oldcodeineditor:
      sequencechange = vc.DiffLineSequenceChanges(oldcodeineditor, newcode)
      res = "%s:::sElEcT rAnGe:::%s" % (str(list(sequencechange)), newcode)   # a delimeter that the javascript can find, in absence of using json
  else:
      res = newcode
  return HttpResponse(res, mimetype="text/plain")

def edit(request, short_name=None):
  """
  This is the main editor view.  Made more complex by bcause of the 
  'lazy registration' model.  This is implemented by creating a copy
  of the editor form in the session, so if this session exists then 
  it should be loaded by default (see below for problems).
  
  The use cases are as follows:
  
  1. Scraper creation.  Scrapers can be run before saving/committing.  
     Display the standard (empty) editor form at /editor.

  2. Scraper editing.  Scrapers can be edited by anyone, but not saved
     unless they are logged in.  Titles can be changed, but not short
     names.  Display the existing editor at /editor/<shortname>
  
  In both the above cases, if a user isn't logged in then the form object
  is saved in to the session and the user is redirected to the log in page
  
  After logging in they are redirected to the scraper they came from and 
  the action they attepted (save or commit) is performed.  If the action 
  is save then they are redirected to the editor page for that scraper, if
  it's commit (and close) then they are redirected to the scrapers main page.
  
  
    - `short_name` (optional) Short name of the Scraper from web.scrapers.models  

  TODO:
    * Only load draft for the correct scraper (sniff short_name, or new)
    * If short_name exists, don't make a new one
    
  """
  
  # For special cases where we are calling from AJAX
  if request.META.get('CONTENT_TYPE', '').startswith('json'):
    is_json = True
  else:
    is_json = False
  
  if short_name == None:
    short_name = "__new__"  
  
  if not request.session.get('ScraperDraft', None):
    request.session['ScraperDraft'] = {}

  # drafts are saved in session e.g. if you've been redirected to log in
  draft = request.session['ScraperDraft'].get(short_name, None)
  has_draft = False

  # First off, create a scraper instance somehow.
  # Drafts are seen as more 'important' than saved scrapers.
  if draft:
    has_draft = True
    if draft.short_name:
      # We're working with an existing scraper that has been edited, but not saved
      scraper = draft
      scraper.code = draft.code   
    else:
      # This is a new scraper that has been edited, but not saved
      # APS - what is the distinction here? This if/else doesn't seem to do anything
      scraper = draft
      scraper.code = draft.code
    scraper.__dict__['commit_message'] = 'Scraper created'
  else:
    # No drafts exist...
    if short_name is not "__new__":
      # ...and this is an existing scraper.  Load from the database and disk
      # This happens after you've pressed the SAVE button
      scraper = get_object_or_404(ScraperModel, short_name=short_name)
      scraper.code = scraper.saved_code()
      if not scraper.published:
      	scraper.__dict__['commit_message'] = 'Scraper created'
    else:
      # This is a totally brand new scraper, load default code
      scraper = ScraperModel()
      scraper.code = template.default()['code']
      scraper.license = 'Unknown'
      # display 'scraper created' commit message if scraper hasn't been saved yet
      scraper.__dict__['commit_message'] = 'Scraper created'

  # load tags into form (using dict)
  scraper.__dict__['tags'] = ", ".join(tag.name for tag in scraper.tags)
  
  form = forms.editorForm(scraper.__dict__, instance=scraper)

  form.fields['code'].initial = scraper.code
  form.fields['title'].initial = scraper.title
  form.fields['license'].initial = scraper.license
  
  if request.method == 'POST' or bool(re.match('save|commit', request.GET.get('action', ""))):
    if request.POST:
    # If there is POST, then use that as the form
      form = forms.editorForm(request.POST, instance=scraper)
      action = request.POST.get('action').lower()
    else:
      # We only reach here when the GET action is scraper or commit, ('save or commit'?)
      # and that only heppens when the 'draft' feature is being used.
      if draft:
        draft.__dict__['commit_message'] = 'Scraper created - hello world'
        form = forms.editorForm(draft.__dict__, instance=draft)
        form.code = draft.code
        action = request.GET.get('action').lower()
      else:
        # The GET action was called incorrectly, so we just redurect to a cleaner URL
        if short_name:
          return HttpResponseRedirect(reverse('editor', kwargs={'short_name' : short_name}))
        else:
          return HttpResponseRedirect(reverse('editor'))
    
    if form.is_valid():
      # Save the form without committing at first
      # (read http://docs.djangoproject.com/en/dev/topics/forms/modelforms/#the-save-method)
      savedForm = form.save(commit=False)
      
      # Add some more fields to the form
      savedForm.code = form.cleaned_data['code']
      savedForm.description = form.cleaned_data['description']    
      savedForm.license = form.cleaned_data['license']    

      # savedForm.short_name = short_name
      # if hasattr(scraper, 'pk'):
      #   savedForm.pk = scraper.pk

      if request.user.is_authenticated():
        # The user is authenticated, so we can process the form correctly
        if action == 'save':
          savedForm.save()
        if action.startswith('commit'):          
          message = None
          if request.POST.get('commit_message', False):
            message = request.POST['commit_message']
          savedForm.save(commit=True, message=message, user=request.user.pk)

        if savedForm.owner():
          # Set the owner.
          # If there is already an owner, and it is not this user, mark this user as an editor
          # If the scraper has no owner, then the current user takes ownership
          if savedForm.owner().pk != request.user.pk:
            savedForm.add_user_role(request.user, 'editor')
        else:
          savedForm.add_user_role(request.user, 'owner')

        #add any tags (note that we have to do this *after* the scraper has been saved)
        s = get_object_or_404(ScraperModel, short_name=savedForm.short_name)
        s.tags = request.POST.get('tags')
        
        # If the scraper saved, then we can delete the draft  
        if request.session['ScraperDraft'].get(short_name, False):
          all_drafts = request.session['ScraperDraft']
          del all_drafts[short_name]
          request.session['ScraperDraft'] = all_drafts
        
        if is_json:
          url = reverse('editor', kwargs={'short_name' : savedForm.short_name})
          if action.startswith("commit"):
            url = reverse('scraper_code', kwargs={'scraper_short_name' : savedForm.short_name})
          res = json.dumps({
          'redirect' : 'true',
          'url' : url,
          })
          return HttpResponse(res)
          
        if action.startswith("commit"):
          return HttpResponseRedirect(reverse('scraper_code', kwargs={'scraper_short_name' : savedForm.short_name}))

        return HttpResponseRedirect(reverse('editor', kwargs={'short_name' : savedForm.short_name}))
        
      else:
        # The user is not authenticated.
        # This can happen when a user creates a scraper before logging in or registering
        # When they hit the save button, by default an ajax call is made.  In this case we
        # don't want to set a message or redirect them, we just return a JSON object.
        drafts = request.session['ScraperDraft']
        drafts[short_name] = savedForm
        request.session['ScraperDraft'] = drafts
            
        # Set a message with django_notify
        request.notifications.add("You need to sign in or create an account - don't worry, your scraper is safe ")
        savedForm.action = action
        if savedForm.short_name:
          scraper_edit_url = reverse('editor', kwargs={'short_name' : savedForm.short_name}) + '?action=%s' % action
        else:
          scraper_edit_url = reverse('editor') + '?action=%s' % action
        
        if is_json:
          return HttpResponse(json.dumps({'status' : 'OK', 'draft' : 'True', 'url': scraper_edit_url}))
              
        return HttpResponseRedirect(reverse('login') + "?next=%s" % scraper_edit_url) 
        
  return render_to_response('editor.html', {
    'form':form, 
    'scraper' : scraper,
    'has_draft': has_draft 
    }, context_instance=RequestContext(request)) 
