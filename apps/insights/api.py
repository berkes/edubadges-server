from datetime import timedelta

from django.db.models import Count
from django.db.models import Q
from django.db.models.functions import TruncWeek, TruncYear, ExtractMonth, ExtractYear
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from badgeuser.models import BadgeUser, StudentAffiliation
from directaward.models import DirectAward
from institution.models import Faculty
from issuer.models import BadgeInstance, Issuer, BadgeClass
from lti_edu.models import StudentsEnrolled
from mainsite.permissions import TeachPermission


class InsightsView(APIView):
    permission_classes = (TeachPermission,)

    def post(self, request, **kwargs):
        lang = request.data.get('lang', 'en')

        current_date = timezone.now().date()
        year = request.data.get('year', current_date.year)
        total = isinstance(year, str)
        if not total:
            start_of_year = current_date.replace(year=year, month=1, day=1)
            if start_of_year.isoweekday() > 1:
                start_of_year = (start_of_year + timedelta(days=(7 + 1) - start_of_year.isoweekday()))
            end_of_year = current_date.replace(year=year, month=12, day=31)
            if end_of_year.isoweekday() > 1:
                end_of_year = (end_of_year + timedelta(days=(7 + 1) - end_of_year.isoweekday()))
        # Super users may select an institution
        institution = request.user.institution
        name_lang = 'name_english' if lang == 'en' else 'name_dutch'
        assertions_query_set = BadgeInstance.objects \
            .filter(issuer__faculty__institution=institution) \
            .values('award_type', 'badgeclass_id', 'badgeclass__name', 'issuer_id',
                    f"issuer__{name_lang}", 'issuer__faculty_id', f"issuer__faculty__{name_lang}") \
            .annotate(year=ExtractYear('created_at')) \
            .annotate(month=ExtractMonth('created_at')) \
            .annotate(nbr=Count('month')) \
            .values('year', 'month', 'nbr', 'award_type', 'badgeclass_id', 'badgeclass__name', 'issuer_id',
                    f"issuer__{name_lang}", 'issuer__faculty_id', f"issuer__faculty__{name_lang}") \
            .order_by('year', 'month')
        if not total:
            assertions_query_set = assertions_query_set \
                .filter(created_at__gte=start_of_year) \
                .filter(created_at__lt=end_of_year)

        direct_awards_query_set = DirectAward.objects \
            .filter(badgeclass__issuer__faculty__institution=institution) \
            .values('status', 'badgeclass_id', 'badgeclass__name', 'badgeclass__issuer__id',
                    f"badgeclass__issuer__{name_lang}", 'badgeclass__issuer__faculty_id',
                    f"badgeclass__issuer__faculty__{name_lang}") \
            .annotate(year=ExtractYear('created_at')) \
            .annotate(month=ExtractMonth('created_at')) \
            .annotate(nbr=Count('month')) \
            .values('month', 'year', 'nbr', 'status', 'badgeclass_id', 'badgeclass__name', 'badgeclass__issuer__id',
                    f"badgeclass__issuer__{name_lang}", 'badgeclass__issuer__faculty_id',
                    f"badgeclass__issuer__faculty__{name_lang}") \
            .order_by('year', 'month')
        if not total:
            direct_awards_query_set = direct_awards_query_set \
                .filter(created_at__gte=start_of_year) \
                .filter(created_at__lt=end_of_year)

        enrollments_query_set = StudentsEnrolled.objects \
            .filter(badge_class__issuer__faculty__institution=institution) \
            .filter(Q(badge_instance_id__isnull=True) | Q(denied=True)) \
            .values('denied', 'badge_class_id', 'badge_class__name', 'badge_class__issuer__id',
                    f"badge_class__issuer__{name_lang}", 'badge_class__issuer__faculty_id',
                    f"badge_class__issuer__faculty__{name_lang}") \
            .annotate(year=ExtractYear('date_created')) \
            .annotate(month=ExtractMonth('date_created')) \
            .annotate(nbr=Count('month')) \
            .values('month', 'year', 'nbr', 'denied', 'badge_class_id', 'badge_class__name', 'badge_class__issuer__id',
                    f"badge_class__issuer__{name_lang}", 'badge_class__issuer__faculty_id',
                    f"badge_class__issuer__faculty__{name_lang}") \
            .order_by('year', 'month')

        if not total:
            enrollments_query_set = enrollments_query_set \
                .filter(date_created__gte=start_of_year) \
                .filter(date_created__lt=end_of_year)

        assertions = list(assertions_query_set.all())
        direct_awards = list(direct_awards_query_set.all())
        enrollments = list(enrollments_query_set.all())
        res = {
            'assertions': assertions,
            'direct_awards': direct_awards,
            'enrollments': enrollments,
            'users_count': BadgeUser.objects.filter(is_teacher=True, institution=institution).count(),
            'faculties_count': Faculty.objects.filter(institution=institution).count(),
            'issuers_count': Issuer.objects.filter(faculty__institution=institution).count(),
            'badge_class_count': BadgeClass.objects.filter(issuer__faculty__institution=institution).count(),
            'backpack_count': StudentAffiliation.objects.filter(schac_home=institution.identifier).count()
        }
        return Response(res, status=status.HTTP_200_OK)
