from django import forms
from django.forms import modelformset_factory
from .models import Student, Result


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'usn',
            'name',
            'email',
            'phone',
            'college',
            'degree',
            'branch',
            'scheme',
            'semester'
        ]


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = [
            'semester',
            'subject_code',
            'subject_name',
            'internal_marks',
            'external_marks'
        ]

    def __init__(self, *args, **kwargs):
        super(ResultForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].required = False


ResultFormSet = modelformset_factory(
    Result,
    form=ResultForm,
    extra=8,
    can_delete=True
)