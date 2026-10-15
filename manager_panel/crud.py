"""Small generic CRUD toolkit used by every list/add/edit/delete page of the /manage/ panel."""
from django.contrib import messages
from django.db import models, transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import ListView

from utils.files import delete_stored_file_if_unused

from .mixins import ManagerRequiredMixin


def safe_redirect_target(request, default):
    target = request.POST.get('next') or request.GET.get('next') or ''
    if target and url_has_allowed_host_and_scheme(
            target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return default


def file_snapshot(obj):
    """{field_name: (storage, stored_name)} for every file field of a saved object."""
    snapshot = {}
    if obj is None or obj.pk is None:
        return snapshot
    for field in obj._meta.concrete_fields:
        if isinstance(field, models.FileField):
            current = getattr(obj, field.name)
            if current and current.name:
                snapshot[field.name] = (current.storage, current.name)
    return snapshot


def cleanup_replaced_files(before, obj):
    """Delete files that were replaced/cleared, but only when nothing else still uses them."""
    for field_name, (storage, name) in before.items():
        new_name = getattr(obj, field_name).name if getattr(obj, field_name) else ''
        if new_name != name:
            delete_stored_file_if_unused(storage, name)


def protected_dependencies(obj):
    """Human readable list of PROTECT relations that currently block deleting `obj`."""
    blockers = []
    for relation in obj._meta.related_objects:
        if getattr(relation, 'on_delete', None) is models.PROTECT:
            count = getattr(obj, relation.get_accessor_name()).count()
            if count:
                blockers.append(f'{count} {relation.related_model._meta.verbose_name_plural}')
    return blockers


def reset_to_defaults(obj):
    """Reset text/number/boolean fields of a settings row to their model defaults (files are kept)."""
    for field in obj._meta.concrete_fields:
        if field.primary_key or isinstance(field, models.FileField):
            continue
        if field.has_default():
            setattr(obj, field.attname, field.get_default())
        elif field.null:
            setattr(obj, field.attname, None)
        elif field.blank:
            setattr(obj, field.attname, '')
    obj.save()


class ManagerPageMixin(ManagerRequiredMixin):
    """Common context for panel pages."""
    nav_section = ''
    title = ''

    def panel_context(self, **extra):
        context = {'nav_section': self.nav_section, 'page_title': self.title}
        context.update(extra)
        return context


class ManageListView(ManagerPageMixin, ListView):
    template_name = 'manager_panel/list.html'
    paginate_by = 15
    context_object_name = 'objects'
    url_base = ''
    columns = ()                 # (label, accessor[, kind])  kind: text | image | bool | color
    search_fields = ()
    select_related = ()
    prefetch_related = ()
    filters = ()                 # dicts: {'param','label','field','options': callable -> [(value, label)]}
    sort_choices = ()            # (key, label, ordering)
    has_status_filter = True
    has_toggle = True
    has_move = False
    can_add = True
    can_edit = True
    can_delete = True
    toggle_guard = None
    add_label = 'Add new'
    empty_text = 'Nothing here yet.'
    intro = ''

    def get_queryset(self):
        queryset = self.model._default_manager.all()
        if self.select_related:
            queryset = queryset.select_related(*self.select_related)
        if self.prefetch_related:
            queryset = queryset.prefetch_related(*self.prefetch_related)
        term = (self.request.GET.get('q') or '').strip()
        if term and self.search_fields:
            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{f'{field}__icontains': term})
            queryset = queryset.filter(condition)
        if self.has_status_filter:
            status = self.request.GET.get('status')
            if status == 'active':
                queryset = queryset.filter(is_active=True)
            elif status == 'inactive':
                queryset = queryset.filter(is_active=False)
        for spec in self.filters:
            value = self.request.GET.get(spec['param'])
            if value and value.isdigit():
                queryset = queryset.filter(**{spec['field']: int(value)})
        sort = self.request.GET.get('sort')
        for key, _label, ordering in self.sort_choices:
            if key == sort:
                queryset = queryset.order_by(*ordering) if isinstance(ordering, (list, tuple)) else queryset.order_by(ordering)
                break
        if not queryset.ordered:
            queryset = queryset.order_by('-pk')
        return queryset

    @staticmethod
    def _value(obj, accessor):
        if callable(accessor):
            return accessor(obj)
        value = obj
        for part in accessor.split('.'):
            value = getattr(value, part, '')
            if callable(value):
                value = value()
        return value

    def build_rows(self, objects):
        rows = []
        for obj in objects:
            cells = []
            for column in self.columns:
                label, accessor = column[0], column[1]
                kind = column[2] if len(column) > 2 else 'text'
                value = self._value(obj, accessor)
                if kind == 'image':
                    value = value.url if value else ''
                cells.append({'kind': kind, 'value': value, 'label': label})
            guard_message = self.toggle_guard(obj, self.request) if self.toggle_guard else None
            rows.append({
                'obj': obj, 'cells': cells,
                'is_active': getattr(obj, 'is_active', None),
                'can_toggle': self.has_toggle and not guard_message,
            })
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop('page', None)
        filter_data = []
        for spec in self.filters:
            filter_data.append({
                'param': spec['param'], 'label': spec['label'],
                'options': list(spec['options']()), 'selected': self.request.GET.get(spec['param'], ''),
            })
        base = self.url_base
        context.update(self.panel_context(
            column_labels=[column[0] for column in self.columns],
            rows=self.build_rows(context['object_list']),
            list_url=reverse(f'manage_{base}_list'),
            add_url=reverse(f'manage_{base}_add') if self.can_add else '',
            edit_name=f'manage_{base}_edit' if self.can_edit else '',
            delete_name=f'manage_{base}_delete' if self.can_delete else '',
            toggle_name=f'manage_{base}_toggle' if self.has_toggle else '',
            move_name=f'manage_{base}_move' if self.has_move else '',
            query=self.request.GET.get('q', ''),
            status=self.request.GET.get('status', ''),
            sort=self.request.GET.get('sort', ''),
            sort_choices=[(key, label) for key, label, _o in self.sort_choices],
            filter_data=filter_data,
            has_search=bool(self.search_fields),
            has_status_filter=self.has_status_filter,
            querystring=params.urlencode(),
            add_label=self.add_label,
            empty_text=self.empty_text,
            intro=self.intro,
            current_url=self.request.get_full_path(),
        ))
        return context


class ManageFormView(ManagerPageMixin, View):
    """Create/edit page for one model, optionally with inline formsets (variants, gallery, ...)."""
    template_name = 'manager_panel/form.html'
    model = None
    form_class = None
    formset_specs = ()           # dicts: {'key', 'class', 'title', 'help'}
    url_base = ''
    object_label = 'item'
    list_url_name = None

    def get_object(self):
        pk = self.kwargs.get('pk')
        if pk is None:
            return None
        return get_object_or_404(self.model, pk=pk)

    def build_formsets(self, obj, data=None, files=None):
        formsets = []
        for spec in self.formset_specs:
            formset = spec['class'](data, files, instance=obj, prefix=spec['key'])
            formsets.append({'spec': spec, 'formset': formset})
        return formsets

    def render_page(self, request, obj, form, formsets, status=200):
        base = self.url_base
        context = self.panel_context(
            form=form, formsets=formsets, object=obj,
            page_title=f'Edit {self.object_label}' if obj else f'Add {self.object_label}',
            cancel_url=reverse(self.list_url_name or f'manage_{base}_list'),
        )
        return render(request, self.template_name, context, status=status)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        form = self.form_class(instance=obj)
        return self.render_page(request, obj, form, self.build_formsets(obj))

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        before = file_snapshot(obj)
        form = self.form_class(request.POST, request.FILES, instance=obj)
        formsets = self.build_formsets(obj, request.POST, request.FILES)
        form_ok = form.is_valid()
        formsets_ok = all(item['formset'].is_valid() for item in formsets)
        if form_ok and formsets_ok:
            creating = obj is None
            with transaction.atomic():
                saved = form.save()
                for item in formsets:
                    formset = item['formset']
                    formset.instance = saved
                    formset.save()
            cleanup_replaced_files(before, saved)
            for item in formsets:
                for deleted in getattr(item['formset'], 'deleted_objects', []):
                    for field in deleted._meta.concrete_fields:
                        if isinstance(field, models.FileField):
                            stored = getattr(deleted, field.name)
                            if stored and stored.name:
                                delete_stored_file_if_unused(stored.storage, stored.name)
            self.after_save(request, saved, creating)
            messages.success(request, f'{self.object_label.capitalize()} {"created" if creating else "saved"}.')
            return redirect(self.get_success_url(request, saved))
        messages.error(request, 'Please fix the errors below.')
        return self.render_page(request, obj, form, formsets, status=200)

    def after_save(self, request, obj, creating):
        pass

    def get_success_url(self, request, obj):
        return reverse(self.list_url_name or f'manage_{self.url_base}_list')


class ManageDeleteView(ManagerPageMixin, View):
    template_name = 'manager_panel/confirm_delete.html'
    model = None
    url_base = ''
    object_label = 'item'
    extra_warning = ''
    guard = None                 # callable(obj, request) -> error message or None

    def get_object(self):
        return get_object_or_404(self.model, pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        blockers = protected_dependencies(obj)
        guard_message = self.guard(obj, request) if self.guard else None
        return render(request, self.template_name, self.panel_context(
            object=obj, blockers=blockers, guard_message=guard_message,
            extra_warning=self.extra_warning, object_label=self.object_label,
            page_title=f'Delete {self.object_label}',
            cancel_url=reverse(f'manage_{self.url_base}_list'),
            can_deactivate=hasattr(obj, 'is_active'),
        ))

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        list_url = reverse(f'manage_{self.url_base}_list')
        if self.guard:
            message = self.guard(obj, request)
            if message:
                messages.error(request, message)
                return redirect(list_url)
        blockers = protected_dependencies(obj)
        if blockers:
            messages.error(
                request, f'"{obj}" is still used by {", ".join(blockers)} and cannot be deleted. '
                         f'Deactivate it or remove those items first.')
            return redirect(list_url)
        files = file_snapshot(obj)
        related_files = self.collect_related_files(obj)
        name = str(obj)
        with transaction.atomic():
            obj.delete()
        for storage, stored_name in list(files.values()) + related_files:
            delete_stored_file_if_unused(storage, stored_name)
        messages.success(request, f'"{name}" was deleted.')
        return redirect(list_url)

    @staticmethod
    def collect_related_files(obj):
        """Files of objects that are deleted together with `obj` (e.g. a product's gallery)."""
        collected = []
        for relation in obj._meta.related_objects:
            if getattr(relation, 'on_delete', None) is models.CASCADE and relation.one_to_many:
                for child in getattr(obj, relation.get_accessor_name()).all():
                    collected.extend(file_snapshot(child).values())
        return collected


class ToggleActiveView(ManagerPageMixin, View):
    http_method_names = ['post']
    model = None
    url_base = ''
    guard = None

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk=self.kwargs['pk'])
        fallback = reverse(f'manage_{self.url_base}_list')
        if self.guard:
            message = self.guard(obj, request)
            if message:
                messages.error(request, message)
                return redirect(safe_redirect_target(request, fallback))
        obj.is_active = not obj.is_active
        obj.save(update_fields=['is_active'])
        messages.success(request, f'"{obj}" is now {"active" if obj.is_active else "inactive"}.')
        return redirect(safe_redirect_target(request, fallback))


class MoveOrderView(ManagerPageMixin, View):
    """Move a row up/down by renumbering `sort_order` of its siblings (10, 20, 30 ...)."""
    http_method_names = ['post']
    model = None
    url_base = ''
    scope_field = None           # e.g. 'column' for footer links

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk=self.kwargs['pk'])
        direction = self.kwargs.get('direction')
        if direction not in ('up', 'down'):
            raise Http404
        siblings = self.model._default_manager.all()
        if self.scope_field:
            siblings = siblings.filter(**{self.scope_field: getattr(obj, self.scope_field)})
        items = list(siblings.order_by('sort_order', 'id'))
        index = next((i for i, item in enumerate(items) if item.pk == obj.pk), None)
        if index is not None:
            target = index - 1 if direction == 'up' else index + 1
            if 0 <= target < len(items):
                items[index], items[target] = items[target], items[index]
                with transaction.atomic():
                    for position, item in enumerate(items, start=1):
                        new_value = position * 10
                        if item.sort_order != new_value:
                            item.sort_order = new_value
                            item.save(update_fields=['sort_order'])
        return redirect(safe_redirect_target(request, reverse(f'manage_{self.url_base}_list')))


class ManageSingletonView(ManagerPageMixin, View):
    """Edit page for a one-row settings table (site settings, footer) with a reset button."""
    template_name = 'manager_panel/form.html'
    model = None
    form_class = None
    url_name = ''
    object_label = 'settings'
    reset_hint = 'Reset text and number settings to their defaults (uploaded images are kept).'

    def page(self, request, form, obj):
        return render(request, self.template_name, self.panel_context(
            form=form, formsets=[], object=obj, page_title=self.title,
            singleton=True, reset_hint=self.reset_hint, cancel_url=reverse('manage_dashboard'),
            form_action=reverse(self.url_name)))

    def get(self, request, *args, **kwargs):
        obj = self.model.load()
        return self.page(request, self.form_class(instance=obj), obj)

    def post(self, request, *args, **kwargs):
        obj = self.model.load()
        if request.POST.get('action') == 'reset':
            reset_to_defaults(obj)
            messages.success(request, 'Settings were reset to their default values.')
            return redirect(self.url_name)
        before = file_snapshot(obj)
        form = self.form_class(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            saved = form.save()
            cleanup_replaced_files(before, saved)
            messages.success(request, 'Settings saved.')
            return redirect(self.url_name)
        messages.error(request, 'Please fix the errors below.')
        return self.page(request, form, obj)
