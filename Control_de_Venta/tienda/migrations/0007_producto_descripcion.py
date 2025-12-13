from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tienda', '0006_categoria_producto_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='descripcion',
            field=models.TextField(blank=True, null=True),
        ),
    ]
