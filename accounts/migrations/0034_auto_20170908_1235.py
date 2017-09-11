# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-09-08 16:35

from __future__ import unicode_literals
import json
from django.db import migrations

children_created = 0
demographic_data_created = 0

def get_participant_json():
    """
    Loads JSON file with participants from Lookit v1
    """
    with open('participants.json') as data_file:
        data = json.load(data_file)
    return data

def get_duplicate_emails(participants):
    """
    Some lookit v1 users have duplicate emails.  In new db, emails must be unique. Will need to manually migrate.
    """
    email_list = []
    for participant in participants:
        email_list.append(participant.get('attributes').get('email'))
    return [email for email in email_list if email_list.count(email) > 1]

def migrate_participants(apps, schema_editor):
    """
    Maps Lookit V1 participants to new db
    """
    participants = get_participant_json()
    duplicates = get_duplicate_emails(participants)
    print("Starting migration of old lookit participants...")
    part_count = 0
    copied = 0
    unique_duplicates = set(duplicates)
    for participant in participants:
        part_count += 1
        # Skip participants that have duplicate emails in db
        if participant.get('attributes').get('email') not in unique_duplicates:
            print(f'Copying participant {part_count}/{len(participants)}')
            create_participant(participant, apps)
            copied += 1
        else:
            print(f'Skipping participant {part_count}/{len(participants)}')
    print('========================================')
    print(f'Total participants: {len(participants)}')
    print(f'Skipped: {len(duplicates)} entries due to duplicate emails')
    print(f'Total users needing manual migration: {len(set(duplicates))}')
    print(f'Total users copied: {str(copied)}')
    print(f'Total demographics copied: {str(demographic_data_created)}')
    print(f'Total children copied: {str(children_created)}')

def format_gender(gender):
    """
    Maps gender from Lookit v1 to current gender, assuming "other or prefer not to answer" mapping to na
    """
    gender_mapping = {'male': 'm', 'female': 'f', 'other or prefer not to answer': 'na'}
    return gender_mapping.get(gender, '')

def format_age_at_birth(age):
    """
    Old gestationalAgeAtBirth fields went above 40, but now we are capping at 40.
    """
    if age:
        try:
            int_age = int(age)
            if int_age >= 40:
                return '40>'
            return age
        except ValueError:
            return age
    else:
        return None

def create_child(user, profile, apps):
    """
    Creates child and links to user
    """
    Child = apps.get_model("accounts", "Child")
    gender = profile.get('gender')
    birthday = profile.get('birthday')
    Child.objects.create(
        given_name=profile.get('firstName', ''),
        birthday=birthday.split('T')[0] if birthday else birthday,
        gender=format_gender(profile.get('gender')),
        age_at_birth=format_age_at_birth(profile.get('gestationalAgeAtBirth')) or pull_choice_value(profile.get('ageAtBirth'), 'age_at_birth', apps, "Child"),
        additional_information=pull_choice_value(profile.get('additionalInformation', ''), 'additional_information', apps, "Child"),
        deleted=profile.get('deleted'),
        former_lookit_profile_id=profile.get('profileId'),
        user=user
    )
    global children_created
    children_created += 1

def pull_choice_value(original_field_value, field_name, apps, model_name=None):
    """
    Map display name to value for storing in db
    """
    if original_field_value is None:
        return ''
    fetched_model = apps.get_model("accounts", model_name if model_name else "DemographicData")
    choices = fetched_model._meta.get_field(field_name).choices
    ret = []
    if isinstance(original_field_value, str):
        for choice in choices:
            if choice[1] == original_field_value:
                ret = choice[0]
    else:
        for choice in choices:
            for selected in original_field_value:
                if choice[1] == selected:
                    ret.append(choice[0])
    return ret

def get_simple_field(value):
    """
    Returns empty string if value is None, since many fields don't accept null values
    """
    return '' if value is None else value

def create_demographics(user, participant, apps):
    """
    Creates demographic data and attaches to user
    """
    # Looks like annual income used to be stored as a range, before individual values.  Store this old value in former_lookit_annual_income.
    # If salary matches current choices, then it's also stored in annual_income field.
    DemographicData = apps.get_model("accounts", "DemographicData")
    attributes = participant.get('attributes')
    income = get_simple_field(attributes.get('demographicsAnnualIncome'))

    DemographicData.objects.create(
        number_of_children=get_simple_field(attributes.get('demographicsNumberOfChildren')),
        child_birthdays=[birthday.split('T')[0] if birthday else birthday for birthday in attributes.get('demographicsChildBirthdays')],
        languages_spoken_at_home=get_simple_field(attributes.get('demographicsLanguagesSpokenAtHome')),
        number_of_guardians=pull_choice_value(attributes.get('demographicsNumberOfGuardians'), 'number_of_guardians', apps),
        number_of_guardians_explanation=get_simple_field(attributes.get('demographicsNumberOfGuardiansExplanation')),
        race_identification=pull_choice_value(attributes.get('demographicsRaceIdentification'), 'race_identification', apps),
        former_lookit_annual_income=income,
        annual_income=income if income and '$' not in income and ' ' not in income else '',
        age=pull_choice_value(attributes.get('demographicsAge'), 'age', apps),
        gender=format_gender(attributes.get('demographicsGender')),
        education_level=pull_choice_value(attributes.get('demographicsEducationLevel'), 'education_level', apps),
        spouse_education_level=pull_choice_value(attributes.get('demographicsSpouseEducationLevel'), 'spouse_education_level', apps),
        number_of_books=attributes.get('demographicsNumberOfBooks'),
        additional_comments= get_simple_field(attributes.get('demographicsAdditionalComments')),
        country=get_simple_field(attributes.get('demographicsCountry', '')),
        state=get_simple_field(attributes.get('demographicsState', '')),
        density=get_simple_field(attributes.get('demographicsDensity', '')),
        user=user
    )

    global demographic_data_created
    demographic_data_created += 1

def create_participant(participant, apps):
    """
    Creates user and then adds related children and demographic data
    """
    # Assumptions:
    # - Old email field is going into new username field
    # - Old name field is being stored under given_name
    # - Older username field is being stored under nickname
    # - We have a hash of their password, so I don't want to store a hash of a hash?
    # - Don't seem to be many email preferences in db?
    attributes = participant.get('attributes')
    user_model = apps.get_model("accounts", "User")
    user = user_model.objects.create(
        username=attributes.get('email'),
        password=attributes.get('password'),
        former_lookit_id=participant.get('id'),
        given_name=get_simple_field(attributes.get('name')),
        nickname=get_simple_field(attributes.get('username')),
        is_active=True,
        is_staff=False,
        is_researcher=False,
        email_next_session=attributes.get('emailPreferenceNextSession', True),
        email_new_studies=attributes.get('emailPreferenceNewStudies', True),
        email_study_updates=attributes.get('emailPreferenceResultsPublished', True),
        email_response_questions=attributes.get('emailPreferenceOptOut', True)
    )
    create_demographics(user, participant, apps)
    for profile in attributes.get('profiles'):
        create_child(user, profile, apps)

def reverse_func(apps, schema_editor):
    """
    For unapplying migrations - removes participants, children, and demographic data from Lookitv1
    """
    User = apps.get_model("accounts", "User")
    Child = apps.get_model("accounts", "Child")
    DemographicData = apps.get_model("accounts", "DemographicData")
    db_alias = schema_editor.connection.alias

    users = User.objects.using(db_alias).exclude(former_lookit_id__exact='')
    user_ids = users.values_list('id', flat=True)
    DemographicData.objects.using(db_alias).filter(user_id__in=user_ids).delete()
    Child.objects.using(db_alias).exclude(former_lookit_profile_id='').delete()
    users.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0033_auto_20170908_1234'),
    ]

    operations = [
        migrations.RunPython(migrate_participants, reverse_func)
    ]
