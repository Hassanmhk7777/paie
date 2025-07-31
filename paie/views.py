from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from .models import Employee, Site, Department
from .forms import EmployeeForm

def home(request):
    return HttpResponse("<h2>Bienvenue sur PaiePro !</h2>")

def dashboard(request):
    return HttpResponse("<h3>Bienvenue sur le Dashboard</h3>")

def payroll(request):
    return HttpResponse("<h3>Calcul de la paie</h3>")

def leave(request):
    return HttpResponse("<h3>Gestion des congés</h3>")

def attendance(request):
    return HttpResponse("<h3>Pointage</h3>")

def employees(request):
    site_id = request.GET.get('site')
    dept_id = request.GET.get('department')
    search = request.GET.get('search')

    employees = Employee.objects.all()
    if site_id:
        employees = employees.filter(site_id=site_id)
    if dept_id:
        employees = employees.filter(department_id=dept_id)
    if search:
        employees = employees.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )

    sites = Site.objects.all()
    departments = Department.objects.all()

    # Pour le filtre AJAX (tableau uniquement)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'GET':
        html = render_to_string(
            'employees/includes/partial_employee_list.html',
            {'employees': employees}
        )
        return HttpResponse(html)

    # Sinon, page complète
    return render(request, 'employees/list.html', {
        'employees': employees,
        'sites': sites,
        'departments': departments
    })

def save_employee_form(request, form, template_name):
    data = {}
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            data['form_is_valid'] = True
            employees = Employee.objects.all()
            data['html_employee_list'] = render_to_string(
                'employees/includes/partial_employee_list.html',
                {'employees': employees}
            )
        else:
            data['form_is_valid'] = False
    context = {'form': form}
    data['html_form'] = render_to_string(template_name, context, request=request)
    return JsonResponse(data)

def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
    else:
        form = EmployeeForm()
    return save_employee_form(request, form, 'employees/includes/partial_employee_create.html')

def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
    else:
        form = EmployeeForm(instance=employee)
    return save_employee_form(request, form, 'employees/includes/partial_employee_update.html')

def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    data = {}
    if request.method == 'POST':
        employee.delete()
        data['form_is_valid'] = True
        employees = Employee.objects.all()
        data['html_employee_list'] = render_to_string(
            'employees/includes/partial_employee_list.html',
            {'employees': employees}
        )
    else:
        context = {'employee': employee}
        data['html_form'] = render_to_string(
            'employees/includes/partial_employee_delete.html',
            context,
            request=request
        )
    return JsonResponse(data)
