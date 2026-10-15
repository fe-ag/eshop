# Initial migration for TechStore (Django 5.2).

import django.db.models.deletion
import utils.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=140, unique=True)),
                ('logo', models.ImageField(blank=True, upload_to='brands/', validators=[utils.validators.validate_image_file])),
                ('logo_alt', models.CharField(blank=True, max_length=160)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=100)),
            ],
            options={'ordering': ['sort_order', 'name']},
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=140, unique=True)),
                ('image', models.ImageField(blank=True, upload_to='categories/', validators=[utils.validators.validate_image_file])),
                ('image_alt', models.CharField(blank=True, max_length=160)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('show_on_home', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=100)),
            ],
            options={'ordering': ['sort_order', 'name'], 'verbose_name_plural': 'categories'},
        ),
        migrations.CreateModel(
            name='StorageOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=30, unique=True)),
                ('sort_order', models.PositiveIntegerField(default=100)),
            ],
            options={'ordering': ['sort_order', 'label']},
        ),
        migrations.CreateModel(
            name='ColorOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60, unique=True)),
                ('hex_code', models.CharField(default='#111827', max_length=7, validators=[utils.validators.validate_hex_color])),
                ('sort_order', models.PositiveIntegerField(default=100)),
            ],
            options={'ordering': ['sort_order', 'name']},
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=220, unique=True)),
                ('short_description', models.CharField(blank=True, max_length=300)),
                ('description', models.TextField(blank=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='product_module.brand')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='product_module.category')),
                ('image', models.ImageField(blank=True, upload_to='products/', validators=[utils.validators.validate_image_file])),
                ('image_alt', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('show_on_home', models.BooleanField(default=True)),
                ('is_bestseller_pick', models.BooleanField(default=False)),
                ('home_sort_order', models.PositiveIntegerField(default=100)),
                ('sales_count', models.PositiveIntegerField(default=0)),
                ('ram', models.CharField(blank=True, max_length=60)),
                ('screen_size', models.CharField(blank=True, max_length=60)),
                ('battery_capacity', models.CharField(blank=True, max_length=60)),
                ('operating_system', models.CharField(blank=True, max_length=80)),
                ('processor', models.CharField(blank=True, max_length=120)),
                ('camera', models.CharField(blank=True, max_length=300)),
                ('connectivity', models.CharField(blank=True, max_length=200)),
                ('model_number', models.CharField(blank=True, max_length=80)),
                ('warranty', models.CharField(blank=True, max_length=120)),
                ('meta_title', models.CharField(blank=True, max_length=200)),
                ('meta_description', models.CharField(blank=True, max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at', '-id']},
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='product_module.product')),
                ('storage', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='variants', to='product_module.storageoption')),
                ('color', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='variants', to='product_module.coloroption')),
                ('sku', models.CharField(blank=True, max_length=60)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('discount_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('stock', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=100)),
            ],
            options={'ordering': ['sort_order', 'storage__sort_order', 'color__sort_order', 'id'], 'unique_together': {('product', 'storage', 'color')}},
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery', to='product_module.product')),
                ('image', models.ImageField(upload_to='products/gallery/', validators=[utils.validators.validate_image_file])),
                ('alt_text', models.CharField(blank=True, max_length=200)),
                ('sort_order', models.PositiveIntegerField(default=100)),
            ],
            options={'ordering': ['sort_order', 'id']},
        ),
    ]
