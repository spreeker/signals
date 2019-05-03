from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from signals.apps.signals.managers import CategoryManager


class Category(models.Model):
    HANDLING_A3DMC = 'A3DMC'
    HANDLING_A3DEC = 'A3DEC'
    HANDLING_A3WMC = 'A3WMC'
    HANDLING_A3WEC = 'A3WEC'
    HANDLING_I5DMC = 'I5DMC'
    HANDLING_STOPEC = 'STOPEC'
    HANDLING_KLOKLICHTZC = 'KLOKLICHTZC'
    HANDLING_GLADZC = 'GLADZC'
    HANDLING_A3DEVOMC = 'A3DEVOMC'
    HANDLING_WS1EC = 'WS1EC'
    HANDLING_WS2EC = 'WS2EC'
    HANDLING_WS3EC = 'WS3EC'
    HANDLING_OND = 'ONDERMIJNING'
    HANDLING_REST = 'REST'
    HANDLING_EMPTY = 'EMPTY'
    HANDLING_CHOICES = (
        (HANDLING_A3DMC, HANDLING_A3DMC),
        (HANDLING_A3DEC, HANDLING_A3DEC),
        (HANDLING_A3WMC, HANDLING_A3WMC),
        (HANDLING_A3WEC, HANDLING_A3WEC),
        (HANDLING_I5DMC, HANDLING_I5DMC),
        (HANDLING_STOPEC, HANDLING_STOPEC),
        (HANDLING_KLOKLICHTZC, HANDLING_KLOKLICHTZC),
        (HANDLING_GLADZC, HANDLING_GLADZC),
        (HANDLING_A3DEVOMC, HANDLING_A3DEVOMC),
        (HANDLING_WS1EC, HANDLING_WS1EC),
        (HANDLING_WS2EC, HANDLING_WS2EC),
        (HANDLING_WS3EC, HANDLING_WS3EC),
        (HANDLING_REST, HANDLING_REST),
        (HANDLING_OND, HANDLING_OND),
        (HANDLING_EMPTY, HANDLING_EMPTY),
    )

    parent = models.ForeignKey('signals.Category',
                               related_name='children',
                               on_delete=models.PROTECT,
                               null=True)
    slug = models.SlugField()
    name = models.CharField(max_length=255)
    handling = models.CharField(max_length=20, choices=HANDLING_CHOICES, default=HANDLING_REST)
    departments = models.ManyToManyField('signals.Department')
    is_active = models.BooleanField(default=True)

    objects = CategoryManager()

    class Meta:
        ordering = ('name',)
        unique_together = ('parent', 'slug',)  # does not work if parent == None
        verbose_name_plural = 'Categories'

    def __str__(self):
        """String representation."""
        return '{name}{parent}'.format(name=self.name,
                                       parent=" ({})".format(
                                           self.parent.name) if self.parent else ""
                                       )

    def is_parent(self):
        return self.children.exists()

    def is_child(self):
        return self.parent is not None

    def _validate(self):
        if self.is_parent() and self.is_child() or self.is_child() and self.parent.is_child():
            raise ValidationError('Category hierarchy can only go one level deep')

    def validate_unique(self, exclude=None):
        if Category.objects.filter(parent=self.parent, slug=self.slug).exists():
            msg = 'Combination parent and slug not unique: ({}, {})'.format(
                self.parent, self.slug
            )
            raise ValidationError(msg)

    def save(self, *args, **kwargs):
        """Slug for new instance; disallow slug mutation for old instance."""
        # Note: We do not want changes to the slug, because these slugs are used
        # in the URLs of the API that is built on this model. If name is
        # mutated for display purposes, we want the URLs pointing to the
        # Category instance to stay the same. It is up to the good taste of
        # our business representatives to not change Category semantics through
        # a name change, we allow them only to fix typos.

        self._validate()

        if not self.pk:  # we are a new Category instance
            self.slug = slugify(self.name)
        elif self.slug:  # existing Category instance cannot have its slug value changed:
            slug_in_db = Category.objects.values_list('slug', flat=True).get(id=self.pk)
            if self.slug != slug_in_db:
                raise ValueError('Category slug must not be changed.')

        self.validate_unique()  # test killer
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise NotImplementedError('We do not allow delete on categories.')
