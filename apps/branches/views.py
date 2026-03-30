from django.shortcuts import render


def branch_list(request):
    """View for displaying branch list"""
    return render(request, "branches/branch_list.html")
