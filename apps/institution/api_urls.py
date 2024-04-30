from django.conf.urls import url

from institution.api import (
    FacultyList,
    FacultyDetail,
    FacultyDeleteView,
    InstitutionDetail,
    PublicCheckInstitutionsValidity,
    InstitutionsTagUsage,
)

urlpatterns = [
    url(
        r"^edit/(?P<entity_id>[^/]+)$",
        InstitutionDetail.as_view(),
        name="api_institution_detail",
    ),
    url(r"^faculties/create$", FacultyList.as_view(), name="api_faculty_list"),
    url(
        r"^faculties/edit/(?P<entity_id>[^/]+)$",
        FacultyDetail.as_view(),
        name="api_faculty_detail",
    ),
    url(
        r"^faculties/delete/(?P<entity_id>[^/]+)$",
        FacultyDeleteView.as_view(),
        name="api_faculty_delete",
    ),
    # public endpoint
    url(
        r"^check$",
        PublicCheckInstitutionsValidity.as_view(),
        name="api_check_institution_validity",
    ),
    url(r"^tags$", InstitutionsTagUsage.as_view(), name="api_institutions_tag_usage"),
]
