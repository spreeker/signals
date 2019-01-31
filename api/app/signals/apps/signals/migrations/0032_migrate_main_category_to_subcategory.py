from django.db import migrations


def migrate_main_categories_forward(apps, schema_editor):
    sub_category_model = apps.get_model('signals', 'SubCategory')
    main_category_model = apps.get_model('signals', 'MainCategory')

    for mc in main_category_model.objects.all():
        # Create a SubCategory object to represent each MainCategory (i.e. leave
        # the parent ForeignKey None).
        nsc = sub_category_model.objects.create(
            slug=mc.slug,
            name=mc.name,
            handling=None,
            is_active=True,
            parent=None,
        )

        # Link all relevant (original) SubCategories to this new special 
        # SubCategory (that represents a main category).
        sub_category_model.objects.filter(main_category=mc).update(
            parent=nsc,
            main_category=None,    
        )


def migrate_main_categories_backward(apps, schema_editor):
    sub_category_model = apps.get_model('signals', 'SubCategory')
    main_category_model = apps.get_model('signals', 'MainCategory')

    # Fish the main categories from the SubCategory table, make sure each has
    # an entry in the MainCategory table and  update the "real" sub categories
    # to point to the MainCategory table.
    for mc in sub_category_model.objects.filter(parent=None):
        new_mc, _ = main_category_model.objects.get_or_create(name=mc.name, slug=mc.slug)
        sub_category_model.objects.filter(parent=mc).update(main_category=new_mc)

    # Remove the main categories from the SubCategory table.
    sub_category_model.objects.filter(parent=None).delete()


class Migration(migrations.Migration):
    """
    Represent MainCategories as special case SubCategories.

    Note: SubCategory model will be renamed to Category in future.
    """
    dependencies = [
        ('signals', '0030_auto_20190131_1013'),
    ]

    operations = [
        migrations.RunPython(
            migrate_main_categories_forward,
            migrate_main_categories_backward,
        ),
    ]
