from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, UserChangeForm

from accounts.models import DemographicData, User, Child
from guardian.shortcuts import assign_perm, get_objects_for_user, remove_perm
from studies.models import Study


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        exclude = ('password', )


class UserStudiesForm(forms.Form):
    template = 'accounts/researcher_form.html'
    user = forms.ModelChoiceField(User.objects.all(), required=True, label='Researcher')
    studies = forms.ModelMultipleChoiceField(
        Study.objects.all(), required=True, label='Assigned Studies')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('instance')
        super(UserStudiesForm, self).__init__(*args, **kwargs)

    def is_valid(self):
        valid = super(UserStudiesForm, self).is_valid()
        if valid and len(self.data['studies']) > 0:
            return True

    def save(self):
        permissions = ['studies.can_view_study', 'studies.can_edit_study']
        current_permitted_objects = get_objects_for_user(self.cleaned_data['user'], permissions)
        disallowed_studies = current_permitted_objects.exclude(
            id__in=[x.id for x in self.cleaned_data['studies']])

        for perm in permissions:
            for study in self.cleaned_data['studies']:
                assign_perm(perm, self.cleaned_data['user'], study)
            for study in disallowed_studies:
                remove_perm(perm, self.cleaned_data['user'], study)
        return self.cleaned_data['user']


class ParticipantSignupForm(UserCreationForm):

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = True
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ('username',
                  'given_name', 'middle_name', 'family_name', )
        exclude = ('user_permissions', 'groups', '_identicon', 'organization',
                   'is_active', 'is_staff', 'is_superuser', 'last_login')


class ParticipantUpdateForm(forms.ModelForm):
    username = forms.EmailField(disabled=True, label="Email")

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            kwargs.pop('user')
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)

    class Meta:
        model = User
        fields = ('username', 'given_name', 'middle_name', 'family_name',)


class ParticipantPasswordForm(PasswordChangeForm):
    class Meta:
        model = User


class EmailPreferencesForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email_next_session', 'email_new_studies', 'email_results_published', 'email_personally')
        labels = {
            'email_next_session': "It's time for another session of a study we are currently participating in",
            'email_new_studies': "A new study is available for one of my children",
            'email_results_published': "The results of a study we participated in are published",
            'email_personally': "A researcher needs to email me personally if I report a technical problem or there are questions about my responses (for example, if I reported two different birthdates for a child)."
        }


class DemographicDataForm(forms.ModelForm):
    class Meta:
        model = DemographicData
        exclude = ('created_at', 'previous', 'user', 'extra', 'uuid' )


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ('given_name', 'birthday', 'gender', 'age_at_birth', 'additional_information')

        labels = {
            'given_name': 'First Name',
            'birthday': "Birthday - YYYY-MM-DD ",
            'age_at_birth': 'Gestational Age at Birth',
            'additional_information': "Any additional information you'd like us to know"
        }
