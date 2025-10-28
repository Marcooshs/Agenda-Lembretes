from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse
from .forms import SignupForm
from rest_framework.authtoken.models import Token


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # cria token de API para este usuário
            Token.objects.get_or_create(user=user)
            # autentica na sessão web
            login(request, user)
            messages.success(request, "Cadastro realizado com sucesso! Você já está logado.")
            return redirect("home")
    else:
        form = SignupForm()
    return render(request, "registration/signup.html", {"form": form})