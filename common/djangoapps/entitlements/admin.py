from django.contrib import admin

from .models import CourseEntitlement


class EntitlementForm(forms.ModelForm):
    """
    Django admin form for Entitlement model
    """
    def __init__(self, *args, **kwargs):
        super(EntitlementForm, self).__init__(*args, **kwargs)
        self.fields['expired_at'] = forms.SplitDateTimeField(
            required=False, empty_value=None
        )

    class Meta(object):
        model = MicrositeOrganizationMapping
        fields = '__all__'

@admin.register(CourseEntitlement)
class EntitlementAdmin(admin.ModelAdmin):
    list_display = ('user',
                    'uuid',
                    'course_uuid',
                    'created',
                    'modified',
                    'expired_at',
                    'mode',
                    'enrollment_course_run',
                    'order_number')
