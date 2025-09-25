from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, Cliente, Venta

# LISTAR
def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'tienda/lista_productos.html', {'productos': productos})

# AGREGAR (y editar usa mismo template)
def agregar_producto(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        codigo = request.POST['codigo']
        cantidad = int(request.POST['cantidad'] or 0)
        precio = float(request.POST['precio'] or 0)
        # si viene id => actualizar
        producto_id = request.POST.get('producto_id')
        if producto_id:
            producto = get_object_or_404(Producto, id=producto_id)
            producto.nombre = nombre
            producto.codigo = codigo
            producto.cantidad = cantidad
            producto.precio = precio
            producto.save()
        else:
            Producto.objects.create(nombre=nombre, codigo=codigo, cantidad=cantidad, precio=precio)
        return redirect('lista_productos')

    # GET
    producto_id = request.GET.get('id')
    context = {}
    if producto_id:
        context['producto'] = get_object_or_404(Producto, id=producto_id)
    return render(request, 'tienda/agregar_producto.html', context)

# ELIMINAR
def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.delete()
    return redirect('lista_productos')

# REGISTRAR VENTA
def registrar_venta(request):
    productos = Producto.objects.all()
    if request.method == 'POST':
        rut = request.POST['rut'].strip()
        nombre = request.POST.get('nombre', '').strip()
        habitual = request.POST.get('habitual') == 'on'
        codigo = request.POST['codigo']
        cantidad = int(request.POST['cantidad'] or 0)

        producto = get_object_or_404(Producto, codigo=codigo)

        # Validación de stock
        if producto.cantidad < cantidad:
            return render(request, 'tienda/error.html', {'mensaje': 'Stock insuficiente'})

        cliente, creado = Cliente.objects.get_or_create(rut=rut)
        if habitual:
            cliente.habitual = True
            if nombre:
                cliente.nombre = nombre
            cliente.save()

        Venta.objects.create(cliente=cliente, producto=producto, cantidad=cantidad)
        producto.cantidad -= cantidad
        producto.save()

        return redirect('lista_productos')

    return render(request, 'tienda/registrar_venta.html', {'productos': productos})
