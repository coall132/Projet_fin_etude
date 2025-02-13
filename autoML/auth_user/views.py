from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from .forms import UserForm
from django.http import HttpResponse
from django.contrib.auth import authenticate,login as auth_login
from utils import get_db_mongo

User = get_user_model()

def show_login(request):
    return render(request, 'login.html')

def show_sign(request): 
    return render(request, 'sign.html')

def sign_in(request):
    if request.method=='POST':
        form = UserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            if User.objects.filter(username=username).exists():
                messages.error(request, "Ce nom d'utilisateur est déjà pris.")
            else:
                user = User.objects.create_user(username=username, password=password)
                user.save()
                messages.success(request, "Utilisateur créé avec succès.")
                db,client = get_db_mongo('Auto_ML','localhost',27017)
                collection = db['User']
                collection.insert_one({'username':username,
                                         'id':user.id,
                                         'projet':[]})
                return redirect('show_login')
        else:
            return HttpResponse("Hello, World!")
    return render(request, 'sign.html', {'form': form})

def login(request):
    if request.method=='POST':
        form=UserForm(request.POST)
        print(form)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user=authenticate(username=username,password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, "Utilisateur créé avec succès.")
                return redirect('perso')
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
                return HttpResponse("Hello, World!")
    return render(request, 'login.html', {'form': form})

def success(request):
    return render(request, 'sucess.html')

