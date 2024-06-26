from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category, Page
from rango.forms import CategoryForm
from django.shortcuts import redirect
from django.urls import reverse
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime
import json
from serpapi import GoogleSearch
from rango.search import run_query
from registration.backends.simple.views import RegistrationView

def index(request):
    # Query the database for a list of ALL categories currently stored.
    # Order the categories by the number of likes in descending order.
    # Retrieve the top 5 only -- or all if less than 5.
    category_list = Category.objects.order_by('-likes')[:5]
    # Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.
    page_list = Page.objects.order_by('-views')[:5]

    # Construct a dictionary to pass to the template engine as
    # its context. Note the key boldmessage matches to
    # {{ aboldmessage }} in the template!
    context_dict = {}
    #context_dict = {'aboldmessage': 'Crunchy, creamy, cookie, candy, cupcake!'}
    context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
    # Place the list of categories in our context_dict dictionary (with our boldmessage!)
    # that will be passed to the template engine.
    context_dict['categories'] = category_list
    # Place the list of pages in our context_dict dictionary (with our boldmessage!)
    # that will be passed to the template engine.
    context_dict['pages'] = page_list

    visitor_cookie_handler(request)
    # context_dict['visits'] = int(request.COOKIES.get('visits', '1'))
    # context_dict['visits'] = get_server_side_cookie(request, 'visits', 1)
    # request.session.set_test_cookie()

    # return render(request, 'rango/index.html', context=context_dict)

    # Obtain our Response object early so we can add cookie information.
    response = render(request, 'rango/index.html', context=context_dict)
    # Call the helper function to handle the cookies
    # response = visitor_cookie_handler(request, response)
    # Return response back to the user, updating any cookies that need changed.
    return response

def about(request):
    context_dict = {'aboutmessage': 'This tutorial has been put together by Martin Rodriguez'}

    #if request.session.test_cookie_worked():
        #print("TEST COOKIE WORKED!")
        #request.session.delete_test_cookie()
    
    visitor_cookie_handler(request)
    # context_dict['visits'] = int(request.COOKIES.get('visits', '1'))
    context_dict['visits'] = get_server_side_cookie(request, 'visits', 1)
    

    return render(request, 'rango/about.html', context=context_dict)

def show_category(request, category_name_slug):
    #vCreate a context dictionary which we can pass
    # to the template rendering engine.
    context_dict = {}

    try:
        # Can we find a category name slug with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # The .get() method returns one model instance or raises an exception.
        category = Category.objects.get(slug=category_name_slug)

        # Retrieve all of the associated pages.
        # The filter() will return a list of page objects or an empty list.
        pages = Page.objects.filter(category=category).order_by('-views')

        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from
        # the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category

    except Category.DoesNotExist:

        # We get here if we didn't find the specified category.
        # Don't do anything -
        # the template will display the "no category" message for us.
        context_dict['category'] = None
        context_dict['pages'] = None

     # Start new search functionality code.
    context_dict['query'] = 'search'
    if request.method == 'POST':
        query = request.POST['query'].strip()
            
        if query:
            context_dict['result_list'] = run_query(query)
            context_dict['query'] = query
	# End new search functionality code.
    
    return render(request, 'rango/category.html', context=context_dict)

@login_required
def add_category(request):
    form = CategoryForm()
    
    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():

            # Save the new category to the database.
            form.save(commit=True)

            # Now that the category is saved, we could confirm this.
            # For now, just redirect the user back to the index view.
            return redirect('/rango/')
        
        else:
            # The supplied form contained errors -
            # just print them to the terminal.
            print(form.errors)

    # Will handle the bad form, new form, or no form supplied cases.
    # Render the form with error messages (if any).
    return render(request, 'rango/add_category.html', {'form':form})

@login_required
def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    if category is None:
        return redirect(reverse('rango:index'))
    
    form = PageForm()

    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.view = 0
                page.save()

                return redirect(reverse('rango:show_category',
                                        kwargs={'category_name_slug': category_name_slug}))
            else:
                print(form.errors)

    context_dict = {'form' : form, 'category':category}
    return render(request, 'rango/add_page.html', context=context_dict)

@login_required
def restricted(request):
    return render(request, 'rango/restricted.html')

# Use the login_required() decorator to ensure only those logged in can
# access the view.
'''
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)
    # Take the user back to the homepage.
    return redirect(reverse('rango:index'))
'''

# A helper method
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

def visitor_cookie_handler(request):
    # Get the number of visits to the site.
    # We use the COOKIES.get() function to obtain the visits cookie.
    # If the cookie exists, the value returned is casted to an integer.
    # If the cookie doesn't exist, then the default value of 1 is used.
    # visits = int(request.COOKIES.get('visits', '1'))
    visits = int(get_server_side_cookie(request, 'visits', '1'))    # last_visit_cookie = request.COOKIES.get('last_visit', str(datetime.now()))
    last_visit_cookie = get_server_side_cookie(request,'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7],'%Y-%m-%d %H:%M:%S')    
    # If it's been more than a day since the last visit...
    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        # Update the last visit cookie now that we have updated the count
        # response.set_cookie('last_visit', str(datetime.now()))
        request.session['last_visit'] = str(datetime.now())
    else:
        # Set the last visit cookie
        # response.set_cookie('last_visit', last_visit_cookie)
        request.session['last_visit'] = last_visit_cookie

    # Update/set the visits cookie
    # response.set_cookie('visits', visits)
    # return response
    request.session['visits'] = visits

'''
def search(request):
    result_list = []
    query = ''
    
    if request.method == 'POST':
        query = request.POST['query'].strip()
        
        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    return render(request, 'rango/search.html', {'query':query, 'result_list': result_list})
'''
    
def goto_url(request):
    if request.method == 'GET':
        page_id = request.GET.get('page_id')
        try:
            selected_page = Page.objects.get(id=page_id)
            selected_page.views = selected_page.views + 1
            selected_page.save()
            return redirect(selected_page.url)
        except Page.DoesNotExist:
            return redirect(reverse('rango:index'))
    return redirect(reverse('rango:index'))

@login_required
def register_profile(request):
    form = UserProfileForm()
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()
            return redirect(reverse('rango:index'))
        else:
            print(form.errors)
    context_dict = {'form': form}
    return render(request, 'rango/profile_registration.html', context_dict)

class MyRegistrationView(RegistrationView):
    def get_success_url(self, user):
        return reverse('rango:register_profile')